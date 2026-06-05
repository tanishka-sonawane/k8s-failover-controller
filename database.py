import sqlite3
import json
import os
import uuid
import time

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "failover.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Tenants profile table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tenants (
        id TEXT PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        aws_role_arn TEXT,
        external_id TEXT NOT NULL,
        k8s_api_endpoint TEXT,
        k8s_token TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. Monitored Target Endpoints
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS monitored_endpoints (
        tenant_id TEXT NOT NULL,
        endpoint_name TEXT NOT NULL,
        url TEXT NOT NULL,
        is_primary INTEGER NOT NULL DEFAULT 1, -- 1=Primary, 0=Secondary
        latency_threshold_ms INTEGER NOT NULL DEFAULT 300,
        check_interval_seconds INTEGER NOT NULL DEFAULT 5,
        current_status TEXT DEFAULT 'ONLINE', -- ONLINE, DEGRADED, OFFLINE
        current_latency_ms INTEGER DEFAULT 45,
        PRIMARY KEY (tenant_id, endpoint_name),
        FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
    )
    """)
    
    # 3. Failover Events Log (Audit Trail)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS failover_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        event_type TEXT NOT NULL, -- LATENCY_ALERT, OUTAGE, DNS_REDIRECT, K8S_SCALE, RESTORE
        details TEXT NOT NULL,
        status TEXT DEFAULT 'INFO', -- INFO, WARNING, CRITICAL
        FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
    )
    """)
    
    # 4. Cluster Health Metrics History (For charts)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cluster_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        endpoint_name TEXT NOT NULL,
        latency_ms INTEGER NOT NULL,
        replica_count INTEGER NOT NULL,
        dns_weight INTEGER NOT NULL, -- 0 to 100
        FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
    )
    """)
    
    # Seed default Demo Tenant
    tid = "tenant-demo-id"
    cursor.execute("""
    INSERT OR IGNORE INTO tenants (id, email, aws_role_arn, external_id, k8s_api_endpoint, k8s_token)
    VALUES (?, 'demo-operator@enterprise.com', 'arn:aws:iam::123456789012:role/K8sTrafficController', 'ext-id-k8s-remediation-1234', 'https://k8s.us-east.prod.internal:6443', 'mock-kube-token-secure')
    """, (tid,))
    
    # Seed default monitored endpoints (Primary in East, Secondary in West)
    endpoints = [
        (tid, "Primary Web Cluster (US-East)", "https://us-east.enterprise-app.com/healthz", 1, 250, 5, "ONLINE", 45),
        (tid, "Secondary Web Cluster (US-West)", "https://us-west.enterprise-app.com/healthz", 0, 250, 5, "ONLINE", 120)
    ]
    for e in endpoints:
        cursor.execute("""
        INSERT OR IGNORE INTO monitored_endpoints 
        (tenant_id, endpoint_name, url, is_primary, latency_threshold_ms, check_interval_seconds, current_status, current_latency_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, e)
        
    # Seed metrics history for charts (going back 10 intervals)
    now = time.time()
    for i in range(10):
        # Subtracting intervals
        timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now - (i * 10)))
        # Primary metrics
        cursor.execute("""
        INSERT INTO cluster_metrics (tenant_id, timestamp, endpoint_name, latency_ms, replica_count, dns_weight)
        VALUES (?, ?, 'Primary Web Cluster (US-East)', ?, 3, 100)
        """, (tid, timestamp_str, int(40 + (i % 3) * 5)))
        # Secondary metrics
        cursor.execute("""
        INSERT INTO cluster_metrics (tenant_id, timestamp, endpoint_name, latency_ms, replica_count, dns_weight)
        VALUES (?, ?, 'Secondary Web Cluster (US-West)', ?, 1, 0)
        """, (tid, timestamp_str, int(115 + (i % 2) * 10)))
        
    conn.commit()
    conn.close()

def create_tenant(email: str, aws_role_arn: str = None) -> dict:
    tenant_id = f"tenant-{str(uuid.uuid4())[:8]}"
    external_id = f"ext-{str(uuid.uuid4())}"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO tenants (id, email, aws_role_arn, external_id)
        VALUES (?, ?, ?, ?)
        """, (tenant_id, email, aws_role_arn, external_id))
        
        # Insert default endpoints for the new tenant
        endpoints = [
            (tenant_id, f"Primary Web Cluster ({tenant_id})", "https://primary-app.internal/health", 1, 300, 5, "ONLINE", 50),
            (tenant_id, f"Secondary Web Cluster ({tenant_id})", "https://backup-app.internal/health", 0, 300, 5, "ONLINE", 110)
        ]
        for e in endpoints:
            cursor.execute("""
            INSERT INTO monitored_endpoints 
            (tenant_id, endpoint_name, url, is_primary, latency_threshold_ms, check_interval_seconds, current_status, current_latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, e)
            
        conn.commit()
        return {"id": tenant_id, "email": email, "aws_role_arn": aws_role_arn, "external_id": external_id}
    except sqlite3.IntegrityError:
        cursor.execute("SELECT * FROM tenants WHERE email = ?", (email,))
        row = cursor.fetchone()
        return {
            "id": row["id"],
            "email": row["email"],
            "aws_role_arn": row["aws_role_arn"],
            "external_id": row["external_id"]
        }
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print("Kubernetes Failover Database initialized successfully.")
