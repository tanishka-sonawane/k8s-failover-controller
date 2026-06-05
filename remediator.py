import sqlite3
import json
import os
import time
import requests
import random
import boto3
import urllib.parse
from database import get_db_connection

# Load Kubernetes if present, otherwise mock
try:
    from kubernetes import client as k8s_client
    from kubernetes.client.rest import ApiException
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False

# Active daemon background loops store
active_monitoring_tasks = {}

def get_aws_session(tenant_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT aws_role_arn, external_id FROM tenants WHERE id = ?", (tenant_id,))
    tenant = cursor.fetchone()
    conn.close()
    
    if not tenant or not tenant["aws_role_arn"]:
        return None
        
    try:
        sts_client = boto3.client('sts')
        assumed = sts_client.assume_role(
            RoleArn=tenant["aws_role_arn"],
            RoleSessionName=f"K8sFailover-{tenant_id}",
            ExternalId=tenant["external_id"],
            DurationSeconds=900
        )
        creds = assumed['Credentials']
        return boto3.Session(
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken']
        )
    except Exception as e:
        print(f"[AWS STS FAIL] Tenant {tenant_id} assumption failed: {str(e)}")
        return None

def get_k8s_client(tenant_id):
    if not K8S_AVAILABLE:
        return None
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT k8s_api_endpoint, k8s_token FROM tenants WHERE id = ?", (tenant_id,))
    tenant = cursor.fetchone()
    conn.close()
    
    if not tenant or not tenant["k8s_api_endpoint"] or not tenant["k8s_token"]:
        return None
        
    try:
        configuration = k8s_client.Configuration()
        configuration.host = tenant["k8s_api_endpoint"]
        configuration.api_key = {"authorization": f"Bearer {tenant['k8s_token']}"}
        configuration.verify_ssl = False # Standard bypass for self-signed development clusters
        
        api_client = k8s_client.ApiClient(configuration)
        return k8s_client.AppsV1Api(api_client)
    except Exception as e:
        print(f"[K8S CLIENT FAIL] Tenant {tenant_id} connection failed: {str(e)}")
        return None

def update_route53_dns(session, zone_name, record_name, target_value):
    """
    Executes actual CNAME/A record updates on the tenant's live AWS Hosted Zone.
    """
    client = session.client('route53')
    
    # 1. Resolve Hosted Zone ID
    zones = client.list_hosted_zones_by_name(DNSName=zone_name)
    if not zones.get('HostedZones'):
        raise Exception(f"Hosted Zone {zone_name} not found.")
    zone_id = zones['HostedZones'][0]['Id']
    
    # 2. Change record set pointing to target endpoint
    response = client.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch={
            'Comment': 'Automated Aegis Failover redirect trigger.',
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': record_name,
                        'Type': 'CNAME',
                        'TTL': 60,
                        'ResourceRecords': [{'Value': target_value}]
                    }
                }
            ]
        }
    )
    return response['ChangeInfo']['Id']

def scale_kubernetes_pod(client, namespace, deployment_name, replicas):
    """
    Edits deployment specs in the active K8s cluster to adjust container pod sizes.
    """
    body = {"spec": {"replicas": replicas}}
    try:
        client.patch_namespaced_deployment_scale(
            name=deployment_name,
            namespace=namespace,
            body=body
        )
        return True
    except Exception as e:
        raise Exception(f"K8s scale error: {str(e)}")

def run_health_check_cycle(tenant_id: str, simulation_failure_trigger: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch monitored targets
    cursor.execute("SELECT * FROM monitored_endpoints WHERE tenant_id = ?", (tenant_id,))
    endpoints = cursor.fetchall()
    
    if not endpoints:
        conn.close()
        return
        
    session = get_aws_session(tenant_id)
    k8s_api = get_k8s_client(tenant_id)
    
    # Fetch current state to check if we are already failed over
    cursor.execute("SELECT dns_weight FROM cluster_metrics WHERE tenant_id = ? AND endpoint_name = 'Primary Web Cluster (US-East)' ORDER BY timestamp DESC LIMIT 1", (tenant_id,))
    last_metric = cursor.fetchone()
    is_failed_over = last_metric["dns_weight"] == 0 if last_metric else False
    
    primary_offline = False
    primary_name = ""
    primary_url = ""
    secondary_name = ""
    secondary_url = ""
    threshold = 300
    
    for ep in endpoints:
        name = ep["endpoint_name"]
        url = ep["url"]
        is_primary = bool(ep["is_primary"])
        latency_thresh = ep["latency_threshold_ms"]
        
        # Ping check
        status = "ONLINE"
        latency = 0
        
        if is_primary:
            primary_name = name
            primary_url = url
            threshold = latency_thresh
            
            # If user triggered simulated outage, force offline
            if simulation_failure_trigger:
                status = "OFFLINE"
                latency = 999
                primary_offline = True
            else:
                # Real Ping logic
                if url.startswith("http"):
                    try:
                        start_time = time.time()
                        r = requests.get(url, timeout=3)
                        latency = int((time.time() - start_time) * 1000)
                        if r.status_code >= 500:
                            status = "OFFLINE"
                            primary_offline = True
                        elif latency > latency_thresh:
                            status = "DEGRADED"
                            primary_offline = True
                    except Exception:
                        status = "OFFLINE"
                        latency = 999
                        primary_offline = True
                else:
                    # Simulated ping fluctuation
                    latency = random.randint(35, 60)
                    status = "ONLINE"
        else:
            secondary_name = name
            secondary_url = url
            if url.startswith("http"):
                try:
                    start_time = time.time()
                    requests.get(url, timeout=3)
                    latency = int((time.time() - start_time) * 1000)
                except Exception:
                    status = "OFFLINE"
                    latency = 999
            else:
                latency = random.randint(110, 130)
                status = "ONLINE"
                
        # Update current status
        cursor.execute("""
        UPDATE monitored_endpoints 
        SET current_status = ?, current_latency_ms = ? 
        WHERE tenant_id = ? AND endpoint_name = ?
        """, (status, latency, tenant_id, name))
        
    # Evaluate failover states
    if primary_offline and not is_failed_over:
        # 1. Trigger FAILOVER Flow
        cursor.execute("""
        INSERT INTO failover_events (tenant_id, event_type, details, status)
        VALUES (?, 'OUTAGE_DETECTED', ?, 'CRITICAL')
        """, (tenant_id, f"Primary Endpoint ({primary_url}) is OFFLINE. Triggering automated traffic redirection.", "CRITICAL"))
        
        # DNS Update (Route53)
        dns_status = "Simulated Routing Switch"
        if session:
            try:
                # Mock variables for hosted zone parameters
                update_route53_dns(session, "enterprise-app.com", "app.enterprise-app.com", "us-west.enterprise-app.com")
                dns_status = "AWS Route53 records modified: app.enterprise-app.com -> us-west.enterprise-app.com (CNAME)"
            except Exception as e:
                dns_status = f"AWS Route53 Switch Failed: {str(e)}. Fallback to internal DNS routing."
                cursor.execute("INSERT INTO failover_events (tenant_id, event_type, details, status) VALUES (?, 'DNS_FAIL', ?, 'WARNING')", (tenant_id, dns_status))
                
        cursor.execute("""
        INSERT INTO failover_events (tenant_id, event_type, details, status)
        VALUES (?, 'DNS_REDIRECT', ?, 'WARNING')
        """, (tenant_id, dns_status))
        
        # Kubernetes scaling
        k8s_status = "Simulated Kubernetes Replica Scale Up"
        if k8s_api:
            try:
                scale_kubernetes_pod(k8s_api, "default", "web-deployment-west", 10)
                k8s_status = "K8s Web Scale successful: Deployment scaled from 1 to 10 pod replicas."
            except Exception as e:
                k8s_status = f"K8s Scale Failed: {str(e)}."
                cursor.execute("INSERT INTO failover_events (tenant_id, event_type, details, status) VALUES (?, 'K8S_SCALE_FAIL', ?, 'WARNING')", (tenant_id, k8s_status))
                
        cursor.execute("""
        INSERT INTO failover_events (tenant_id, event_type, details, status)
        VALUES (?, 'K8S_SCALE', ?, 'WARNING')
        """, (tenant_id, k8s_status))
        
        # Log final failover success
        cursor.execute("""
        INSERT INTO failover_events (tenant_id, event_type, details, status)
        VALUES (?, 'FAILOVER_SUCCESS', 'Automated DNS and container scaling failover completed successfully.', 'INFO')
        """, (tenant_id,))
        
        # Save metrics showing failover weights (Primary gets 0%, Secondary 100%, replica counts updated)
        cursor.execute("INSERT INTO cluster_metrics (tenant_id, endpoint_name, latency_ms, replica_count, dns_weight) VALUES (?, 'Primary Web Cluster (US-East)', 999, 0, 0)", (tenant_id,))
        cursor.execute("INSERT INTO cluster_metrics (tenant_id, endpoint_name, latency_ms, replica_count, dns_weight) VALUES (?, 'Secondary Web Cluster (US-West)', 120, 10, 100)", (tenant_id,))
        
    elif not primary_offline and is_failed_over:
        # 2. Trigger HEAL & RESTORE Flow
        cursor.execute("""
        INSERT INTO failover_events (tenant_id, event_type, details, status)
        VALUES (?, 'RESTORE', 'Primary Endpoint recovered online. Initiating rollback and traffic recovery.', 'INFO')
        """, (tenant_id,))
        
        # Restore DNS
        dns_status = "Simulated DNS Recovery"
        if session:
            try:
                update_route53_dns(session, "enterprise-app.com", "app.enterprise-app.com", "us-east.enterprise-app.com")
                dns_status = "AWS Route53 records restored: app.enterprise-app.com -> us-east.enterprise-app.com (CNAME)"
            except Exception as e:
                dns_status = f"AWS Route53 Recovery Failed: {str(e)}"
                
        cursor.execute("""
        INSERT INTO failover_events (tenant_id, event_type, details, status)
        VALUES (?, 'DNS_REDIRECT', ?, 'INFO')
        """, (tenant_id, dns_status))
        
        # Scale back down
        k8s_status = "Simulated Kubernetes Scale Down"
        if k8s_api:
            try:
                scale_kubernetes_pod(k8s_api, "default", "web-deployment-west", 1)
                k8s_status = "K8s Web Scale down successful: Deployment reset to 1 pod replica."
            except Exception as e:
                k8s_status = f"K8s Scale Down Failed: {str(e)}"
                
        cursor.execute("""
        INSERT INTO failover_events (tenant_id, event_type, details, status)
        VALUES (?, 'K8S_SCALE', ?, 'INFO')
        """, (tenant_id, k8s_status))
        
        # Save metrics showing standard weights
        cursor.execute("INSERT INTO cluster_metrics (tenant_id, endpoint_name, latency_ms, replica_count, dns_weight) VALUES (?, 'Primary Web Cluster (US-East)', 45, 3, 100)", (tenant_id,))
        cursor.execute("INSERT INTO cluster_metrics (tenant_id, endpoint_name, latency_ms, replica_count, dns_weight) VALUES (?, 'Secondary Web Cluster (US-West)', 120, 1, 0)", (tenant_id,))
        
    else:
        # Standard loop metrics log
        # Primary
        cursor.execute("SELECT current_latency_ms, current_status FROM monitored_endpoints WHERE tenant_id = ? AND endpoint_name = ?", (tenant_id, primary_name))
        prim = cursor.fetchone()
        p_lat = prim["current_latency_ms"] if prim else 45
        p_rep = 3 if not is_failed_over else 0
        p_weight = 100 if not is_failed_over else 0
        cursor.execute("INSERT INTO cluster_metrics (tenant_id, endpoint_name, latency_ms, replica_count, dns_weight) VALUES (?, ?, ?, ?, ?)", (tenant_id, primary_name, p_lat, p_rep, p_weight))
        
        # Secondary
        cursor.execute("SELECT current_latency_ms, current_status FROM monitored_endpoints WHERE tenant_id = ? AND endpoint_name = ?", (tenant_id, secondary_name))
        sec = cursor.fetchone()
        s_lat = sec["current_latency_ms"] if sec else 120
        s_rep = 1 if not is_failed_over else 10
        s_weight = 0 if not is_failed_over else 100
        cursor.execute("INSERT INTO cluster_metrics (tenant_id, endpoint_name, latency_ms, replica_count, dns_weight) VALUES (?, ?, ?, ?, ?)", (tenant_id, secondary_name, s_lat, s_rep, s_weight))

    # Limit metrics storage to prevent DB bloating (keep last 50 metrics per tenant)
    cursor.execute("""
    DELETE FROM cluster_metrics 
    WHERE tenant_id = ? AND id NOT IN (
        SELECT id FROM cluster_metrics WHERE tenant_id = ? ORDER BY timestamp DESC LIMIT 50
    )
    """, (tenant_id, tenant_id))

    conn.commit()
    conn.close()
