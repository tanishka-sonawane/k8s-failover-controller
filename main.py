import threading
import time
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os

from database import get_db_connection, create_tenant
from remediator import run_health_check_cycle

app = FastAPI(title="Aegis Multi-Tenant Traffic Redirector & Failover SOC")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Daemon State
daemon_running = False
daemon_thread = None
simulation_failure = False  # If True, forces the primary endpoint to be simulated as OFFLINE

class TenantUpdate(BaseModel):
    aws_role_arn: Optional[str] = None
    k8s_api_endpoint: Optional[str] = None
    k8s_token: Optional[str] = None

class EndpointUpdate(BaseModel):
    endpoint_name: str
    url: str
    latency_threshold_ms: int

def background_daemon_loop():
    global daemon_running, simulation_failure
    print("[DAEMON] Health monitoring daemon started.")
    while daemon_running:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tenants")
            tenants = cursor.fetchall()
            conn.close()
            
            for tenant in tenants:
                tenant_id = tenant["id"]
                # Run the health check cycle for this tenant
                run_health_check_cycle(tenant_id, simulation_failure_trigger=simulation_failure)
                
        except Exception as e:
            print(f"[DAEMON ERROR] Error in check cycle: {str(e)}")
        
        # Sleep for a baseline check interval
        time.sleep(5)
    print("[DAEMON] Health monitoring daemon stopped.")

@app.on_event("startup")
def startup_event():
    global daemon_running, daemon_thread
    daemon_running = True
    daemon_thread = threading.Thread(target=background_daemon_loop, daemon=True)
    daemon_thread.start()

@app.on_event("shutdown")
def shutdown_event():
    global daemon_running
    daemon_running = False

# --- REST API Endpoints ---

@app.get("/api/status")
def get_system_status():
    """Returns the current operational status of the monitoring daemon and the simulator."""
    return {
        "daemon_running": daemon_running,
        "simulation_failure_active": simulation_failure
    }

@app.post("/api/daemon/start")
def start_daemon():
    global daemon_running, daemon_thread
    if daemon_running:
        return {"status": "already_running"}
    daemon_running = True
    daemon_thread = threading.Thread(target=background_daemon_loop, daemon=True)
    daemon_thread.start()
    return {"status": "started"}

@app.post("/api/daemon/stop")
def stop_daemon():
    global daemon_running
    daemon_running = False
    return {"status": "stopped"}

@app.post("/api/simulator/toggle")
def toggle_simulator():
    """Toggles simulated outage on the primary endpoint to test failover behavior."""
    global simulation_failure
    simulation_failure = not simulation_failure
    
    # Immediately write a log to show manual simulation trigger in timeline
    conn = get_db_connection()
    cursor = conn.cursor()
    status_str = "CRITICAL" if simulation_failure else "INFO"
    detail_str = "[SIMULATION] Outage simulation triggered on Primary Endpoint." if simulation_failure else "[SIMULATION] Outage simulation disabled. Primary recovery initiated."
    cursor.execute("""
        INSERT INTO failover_events (tenant_id, event_type, details, status)
        VALUES ('tenant-demo-id', 'SIMULATION_TOGGLE', ?, ?)
    """, (detail_str, status_str))
    conn.commit()
    conn.close()
    
    return {"simulation_failure_active": simulation_failure}

@app.get("/api/tenant/{tenant_id}")
def get_tenant(tenant_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,))
    tenant = cursor.fetchone()
    conn.close()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return dict(tenant)

@app.post("/api/tenant/{tenant_id}")
def update_tenant(tenant_id: str, data: TenantUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,))
    tenant = cursor.fetchone()
    if not tenant:
        conn.close()
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    cursor.execute("""
        UPDATE tenants
        SET aws_role_arn = COALESCE(?, aws_role_arn),
            k8s_api_endpoint = COALESCE(?, k8s_api_endpoint),
            k8s_token = COALESCE(?, k8s_token)
        WHERE id = ?
    """, (data.aws_role_arn, data.k8s_api_endpoint, data.k8s_token, tenant_id))
    conn.commit()
    conn.close()
    return {"status": "updated"}

@app.get("/api/endpoints/{tenant_id}")
def get_endpoints(tenant_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM monitored_endpoints WHERE tenant_id = ?", (tenant_id,))
    endpoints = cursor.fetchall()
    conn.close()
    return [dict(e) for e in endpoints]

@app.post("/api/endpoints/{tenant_id}")
def update_endpoint(tenant_id: str, data: EndpointUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE monitored_endpoints
        SET url = ?, latency_threshold_ms = ?
        WHERE tenant_id = ? AND endpoint_name = ?
    """, (data.url, data.latency_threshold_ms, tenant_id, data.endpoint_name))
    conn.commit()
    conn.close()
    return {"status": "updated"}

@app.get("/api/metrics/{tenant_id}")
def get_metrics(tenant_id: str):
    """Returns the history of latency, replica counts, and DNS routing weights for charting."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, endpoint_name, latency_ms, replica_count, dns_weight
        FROM cluster_metrics
        WHERE tenant_id = ?
        ORDER BY timestamp ASC
    """, (tenant_id,))
    metrics = cursor.fetchall()
    conn.close()
    
    # Format metrics grouped by endpoint for frontend charts
    result = {}
    for row in metrics:
        ep_name = row["endpoint_name"]
        if ep_name not in result:
            result[ep_name] = []
        result[ep_name].append({
            "timestamp": row["timestamp"],
            "latency": row["latency_ms"],
            "replicas": row["replica_count"],
            "dns_weight": row["dns_weight"]
        })
    return result

@app.get("/api/events/{tenant_id}")
def get_events(tenant_id: str):
    """Returns audit timeline of alerts, failovers, and routing events."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, timestamp, event_type, details, status
        FROM failover_events
        WHERE tenant_id = ?
        ORDER BY timestamp DESC
        LIMIT 50
    """, (tenant_id,))
    events = cursor.fetchall()
    conn.close()
    return [dict(e) for e in events]

# --- Frontend Static Files Server ---

# Mount static folder if it exists
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

@app.get("/")
def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Aegis SOC Backend Online. Frontend static files are not yet created."}

# Serve other static files (css, js, assets)
app.mount("/static", StaticFiles(directory=static_dir), name="static")
