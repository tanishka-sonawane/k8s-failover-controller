const { useState, useEffect, useRef } = React;

// Simple Inline SVG Icon Helper for clean vector rendering
const Icon = ({ name, size = 18, className = "" }) => {
  const icons = {
    activity: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
      </svg>
    ),
    database: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
        <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
        <path d="M3 5V19A9 3 0 0 0 21 19V5"></path>
        <path d="M3 12A9 3 0 0 0 21 12"></path>
      </svg>
    ),
    terminal: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
        <polyline points="4 17 10 11 4 5"></polyline>
        <line x1="12" y1="19" x2="20" y2="19"></line>
      </svg>
    ),
    key: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
        <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"></path>
      </svg>
    ),
    settings: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
        <circle cx="12" cy="12" r="3"></circle>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
      </svg>
    ),
    shield: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
      </svg>
    ),
    alert: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
    )
  };
  return icons[name] || null;
};

// React Metrics Chart Component (Purple & Emerald colors matching the new theme)
const MetricsChart = ({ metrics }) => {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    if (chartRef.current) chartRef.current.destroy();

    const ctx = canvasRef.current.getContext('2d');
    const primaryData = metrics["Primary Web Cluster (US-East)"] || [];
    const secondaryData = metrics["Secondary Web Cluster (US-West)"] || [];

    const labels = primaryData.map(m => {
      const d = new Date(m.timestamp);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    });

    chartRef.current = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Primary Latency (ms)',
            data: primaryData.map(m => m.latency),
            borderColor: '#a855f7',
            backgroundColor: 'rgba(168, 85, 247, 0.05)',
            tension: 0.2,
            fill: true,
            borderWidth: 2
          },
          {
            label: 'Secondary Latency (ms)',
            data: secondaryData.map(m => m.latency),
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.05)',
            tension: 0.2,
            fill: true,
            borderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false }, ticks: { color: '#64748b', font: { family: 'Space Grotesk' } } },
          y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#64748b', font: { family: 'Space Grotesk' } } }
        },
        plugins: {
          legend: { labels: { color: '#f8fafc', font: { family: 'Space Grotesk' } } }
        }
      }
    });

    return () => {
      if (chartRef.current) chartRef.current.destroy();
    };
  }, [metrics]);

  return <canvas ref={canvasRef} />;
};

// React Replica Scaling Chart Component (Coral & Amber colors matching new theme)
const ReplicaChart = ({ metrics }) => {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    if (chartRef.current) chartRef.current.destroy();

    const ctx = canvasRef.current.getContext('2d');
    const primaryData = metrics["Primary Web Cluster (US-East)"] || [];
    const secondaryData = metrics["Secondary Web Cluster (US-West)"] || [];

    const labels = primaryData.map(m => {
      const d = new Date(m.timestamp);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    });

    chartRef.current = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Primary Pod Replicas',
            data: primaryData.map(m => m.replicas),
            borderColor: '#f43f5e',
            backgroundColor: 'rgba(244, 63, 94, 0.05)',
            stepped: true,
            borderWidth: 2
          },
          {
            label: 'Secondary Pod Replicas',
            data: secondaryData.map(m => m.replicas),
            borderColor: '#fbbf24',
            backgroundColor: 'rgba(251, 191, 36, 0.05)',
            stepped: true,
            borderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false }, ticks: { color: '#64748b', font: { family: 'Space Grotesk' } } },
          y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#64748b', stepSize: 1, font: { family: 'Space Grotesk' } } }
        },
        plugins: {
          legend: { labels: { color: '#f8fafc', font: { family: 'Space Grotesk' } } }
        }
      }
    });

    return () => {
      if (chartRef.current) chartRef.current.destroy();
    };
  }, [metrics]);

  return <canvas ref={canvasRef} />;
};

// Main App component with new Top-Navbar widescreen structure
const App = () => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [tenantId, setTenantId] = useState("tenant-demo-id");
  const [tenant, setTenant] = useState({});
  const [endpoints, setEndpoints] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [events, setEvents] = useState([]);
  const [systemStatus, setSystemStatus] = useState({ daemon_running: false, simulation_failure_active: false });
  
  // Credentials Form States
  const [awsRoleArn, setAwsRoleArn] = useState("");
  const [k8sApi, setK8sApi] = useState("");
  const [k8sToken, setK8sToken] = useState("");

  // Endpoint Update State
  const [primaryUrl, setPrimaryUrl] = useState("");
  const [secondaryUrl, setSecondaryUrl] = useState("");
  const [primaryThresh, setPrimaryThresh] = useState(250);
  const [secondaryThresh, setSecondaryThresh] = useState(250);

  // Poll Backend Data
  const fetchData = async () => {
    try {
      const statusRes = await fetch("/api/status");
      const statusData = await statusRes.json();
      setSystemStatus(statusData);

      const tenantRes = await fetch(`/api/tenant/${tenantId}`);
      const tenantData = await tenantRes.json();
      setTenant(tenantData);
      
      const epRes = await fetch(`/api/endpoints/${tenantId}`);
      const epData = await epRes.json();
      setEndpoints(epData);
      
      const prim = epData.find(e => e.is_primary === 1);
      const sec = epData.find(e => e.is_primary === 0);
      if (prim) {
        setPrimaryUrl(prim.url);
        setPrimaryThresh(prim.latency_threshold_ms);
      }
      if (sec) {
        setSecondaryUrl(sec.url);
        setSecondaryThresh(sec.latency_threshold_ms);
      }

      const metricsRes = await fetch(`/api/metrics/${tenantId}`);
      const metricsData = await metricsRes.json();
      setMetrics(metricsData);

      const eventsRes = await fetch(`/api/events/${tenantId}`);
      const eventsData = await eventsRes.json();
      setEvents(eventsData);
      
    } catch (err) {
      console.error("Error polling backend telemetry: ", err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, [tenantId]);

  useEffect(() => {
    if (tenant.aws_role_arn) setAwsRoleArn(tenant.aws_role_arn);
    if (tenant.k8s_api_endpoint) setK8sApi(tenant.k8s_api_endpoint);
    if (tenant.k8s_token) setK8sToken(tenant.k8s_token);
  }, [tenant]);

  // Actions
  const handleToggleSimulator = async () => {
    try {
      const res = await fetch("/api/simulator/toggle", { method: "POST" });
      const data = await res.json();
      setSystemStatus(prev => ({ ...prev, simulation_failure_active: data.simulation_failure_active }));
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleToggleDaemon = async () => {
    const endpoint = systemStatus.daemon_running ? "/api/daemon/stop" : "/api/daemon/start";
    try {
      await fetch(endpoint, { method: "POST" });
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveCredentials = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`/api/tenant/${tenantId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          aws_role_arn: awsRoleArn,
          k8s_api_endpoint: k8sApi,
          k8s_token: k8sToken
        })
      });
      if (res.ok) {
        alert("AWS & Kubernetes routing connections updated.");
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveEndpoints = async (e) => {
    e.preventDefault();
    try {
      const pEp = endpoints.find(el => el.is_primary === 1);
      const sEp = endpoints.find(el => el.is_primary === 0);
      
      if (pEp) {
        await fetch(`/api/endpoints/${tenantId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            endpoint_name: pEp.endpoint_name,
            url: primaryUrl,
            latency_threshold_ms: Number(primaryThresh)
          })
        });
      }
      
      if (sEp) {
        await fetch(`/api/endpoints/${tenantId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            endpoint_name: sEp.endpoint_name,
            url: secondaryUrl,
            latency_threshold_ms: Number(secondaryThresh)
          })
        });
      }
      alert("Traffic failover thresholds saved successfully.");
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const primaryEP = endpoints.find(e => e.is_primary === 1) || {};
  const secondaryEP = endpoints.find(e => e.is_primary === 0) || {};
  const isFailedOver = systemStatus.simulation_failure_active || primaryEP.current_status === "OFFLINE" || primaryEP.current_status === "DEGRADED";

  return (
    <div className="app-container">
      {/* Top Navigation Bar */}
      <nav className="navbar">
        <div className="navbar-left">
          <div className="logo-container">
            <div className="logo-icon"></div>
            <span className="logo-text">SENTINELFLOW SOC</span>
          </div>

          <ul className="navbar-menu">
            <li>
              <div className={`navbar-item ${activeTab === "dashboard" ? "active" : ""}`} onClick={() => setActiveTab("dashboard")}>
                <Icon name="activity" size={16} />
                <span>Dashboard</span>
              </div>
            </li>
            <li>
              <div className={`navbar-item ${activeTab === "credentials" ? "active" : ""}`} onClick={() => setActiveTab("credentials")}>
                <Icon name="key" size={16} />
                <span>AWS & K8s Connect</span>
              </div>
            </li>
            <li>
              <div className={`navbar-item ${activeTab === "logs" ? "active" : ""}`} onClick={() => setActiveTab("logs")}>
                <Icon name="terminal" size={16} />
                <span>Audit Logs</span>
              </div>
            </li>
            <li>
              <div className={`navbar-item ${activeTab === "settings" ? "active" : ""}`} onClick={() => setActiveTab("settings")}>
                <Icon name="settings" size={16} />
                <span>Controller Settings</span>
              </div>
            </li>
          </ul>
        </div>

        <div className="navbar-right">
          <div className="tenant-selector">
            <span style={{ fontSize: "13px", fontWeight: "600", color: "var(--text-secondary)" }}>Tenant:</span>
            <span className="tenant-badge">{tenantId}</span>
          </div>
          
          <div className="switch-container" onClick={handleToggleSimulator}>
            <span className="switch-label" style={{ color: systemStatus.simulation_failure_active ? "var(--danger)" : "var(--text-secondary)" }}>
              {systemStatus.simulation_failure_active ? "⚠️ Simulation Mode" : "Simulate Outage"}
            </span>
            <div className={`switch-track ${systemStatus.simulation_failure_active ? "active" : ""}`} style={{ backgroundColor: systemStatus.simulation_failure_active ? "var(--danger)" : "" }}>
              <div className="switch-thumb"></div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Container */}
      <main className="main-content">
        {activeTab === "dashboard" && (
          <div>
            {/* Widescreen KPI Stats */}
            <div className="dashboard-grid">
              <div className="panel stat-card">
                <span className="stat-header">Primary Cluster Status</span>
                <div className="stat-value">
                  <span className={`status-light ${primaryEP.current_status === "ONLINE" ? "online" : primaryEP.current_status === "DEGRADED" ? "degraded" : "offline"}`}></span>
                  <span style={{ marginLeft: "10px" }}>{primaryEP.current_status || "UNKNOWN"}</span>
                </div>
                <span className="stat-footer">{primaryEP.endpoint_name}</span>
              </div>

              <div className="panel stat-card">
                <span className="stat-header">Active Routing Target</span>
                <div className="stat-value" style={{ color: isFailedOver ? "var(--primary)" : "var(--success)" }}>
                  {isFailedOver ? "US-WEST (SEC)" : "US-EAST (PRIM)"}
                </div>
                <span className="stat-footer">Route53 Weighted DNS</span>
              </div>

              <div className="panel stat-card">
                <span className="stat-header">Cluster Latency</span>
                <div className="stat-value">
                  {primaryEP.current_latency_ms || 0} <span className="stat-unit">ms</span>
                </div>
                <span className="stat-footer">Threshold: {primaryEP.latency_threshold_ms}ms</span>
              </div>

              <div className="panel stat-card">
                <span className="stat-header">K8s Western Pod Scale</span>
                <div className="stat-value" style={{ color: isFailedOver ? "var(--primary)" : "var(--text-primary)" }}>
                  {isFailedOver ? "10" : "1"} <span className="stat-unit">replicas</span>
                </div>
                <span className="stat-footer">Current secondary weight: {isFailedOver ? "100" : "0"}%</span>
              </div>
            </div>

            {/* Charts & Interactive Section */}
            <div className="main-dashboard-layout">
              {/* Left Column: Charts */}
              <div className="charts-grid">
                <div className="panel">
                  <h3 style={{ fontSize: "15px", fontWeight: "600", marginBottom: "16px", color: "var(--text-primary)" }}>Network Latency RTT (Telemetry)</h3>
                  <div className="chart-box">
                    <MetricsChart metrics={metrics} />
                  </div>
                </div>

                <div className="panel">
                  <h3 style={{ fontSize: "15px", fontWeight: "600", marginBottom: "16px", color: "var(--text-primary)" }}>K8s West Deployment Scale Replicas</h3>
                  <div className="chart-box">
                    <ReplicaChart metrics={metrics} />
                  </div>
                </div>
              </div>

              {/* Right Column: Connection State & Endpoint Status */}
              <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                <div className="panel">
                  <h3 style={{ fontSize: "15px", fontWeight: "600", marginBottom: "16px" }}>Ping Targets Health Monitors</h3>
                  <div className="endpoints-container">
                    {endpoints.map((ep, idx) => (
                      <div key={idx} className="endpoint-row">
                        <div className="endpoint-info">
                          <span className="endpoint-title">{ep.endpoint_name}</span>
                          <span className="endpoint-url">{ep.url}</span>
                        </div>
                        <div className="endpoint-status">
                          <span className={`status-light ${ep.current_status === 'ONLINE' ? 'online' : ep.current_status === 'DEGRADED' ? 'degraded' : 'offline'}`}></span>
                          <span style={{ fontSize: "12px", fontWeight: "700", fontFamily: "var(--font-mono)" }}>{ep.current_latency_ms} ms</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="panel">
                  <h3 style={{ fontSize: "15px", fontWeight: "600", marginBottom: "12px" }}>Credential Integration Profile</h3>
                  <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6", marginBottom: "12px" }}>
                    AWS STS Session State: <span style={{ color: tenant.aws_role_arn ? "var(--success)" : "var(--warning)", fontWeight: "600" }}>
                      {tenant.aws_role_arn ? "CONNECTED (ROLE ASSUMED)" : "SIMULATED FALLBACK ACTIVE"}
                    </span>
                  </p>
                  <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6" }}>
                    Kubernetes cluster connection: <span style={{ color: tenant.k8s_api_endpoint ? "var(--success)" : "var(--warning)", fontWeight: "600" }}>
                      {tenant.k8s_api_endpoint ? "CONNECTED" : "SIMULATED FALLBACK ACTIVE"}
                    </span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "credentials" && (
          <div className="main-dashboard-layout" style={{ justifyContent: "center" }}>
            <div className="panel" style={{ gridColumn: "span 2" }}>
              <h2 style={{ fontSize: "18px", fontWeight: "600", marginBottom: "20px" }}>AWS STS Cross-Account & K8s Connectors</h2>
              
              <form onSubmit={handleSaveCredentials}>
                <div style={{ background: "rgba(255,255,255,0.01)", padding: "20px", borderRadius: "8px", border: "1px solid var(--border-color)", marginBottom: "24px" }}>
                  <h3 style={{ fontSize: "14px", fontWeight: "600", color: "var(--primary)", marginBottom: "8px" }}>Configure AWS Trust Relationship</h3>
                  <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6", marginBottom: "12px" }}>
                    Setup a trust role in your AWS Account Console. Ensure you require the following generated External ID to secure the connection:
                  </p>
                  <pre style={{ background: "#05060a", padding: "12px", borderRadius: "6px", fontSize: "11px", fontFamily: "var(--font-mono)", border: "1px solid var(--border-color)", color: "var(--text-secondary)", overflowX: "auto" }}>
{`{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "AWS": "arn:aws:iam::111122223333:root" },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": { "sts:ExternalId": "${tenant.external_id || "ext-id-k8s-remediation-1234"}" }
      }
    }
  ]
}`}
                  </pre>
                </div>

                <div className="form-group">
                  <label className="form-label">AWS Role ARN</label>
                  <input type="text" className="form-input code-style" placeholder="arn:aws:iam::ACCOUNT_ID:role/ROLE_NAME" value={awsRoleArn} onChange={e => setAwsRoleArn(e.target.value)} />
                </div>

                <div className="form-group">
                  <label className="form-label">Kubernetes Master API Host</label>
                  <input type="text" className="form-input code-style" placeholder="https://api.cluster.domain:6443" value={k8sApi} onChange={e => setK8sApi(e.target.value)} />
                </div>

                <div className="form-group">
                  <label className="form-label">Kubernetes Service JWT Token</label>
                  <input type="password" className="form-input code-style" placeholder="eyJhbGciOiJSUzI1NiIsImtpZCI6..." value={k8sToken} onChange={e => setK8sToken(e.target.value)} />
                </div>

                <button type="submit" className="btn btn-primary" style={{ marginTop: "12px" }}>Save Connector Config</button>
              </form>
            </div>
          </div>
        )}

        {activeTab === "logs" && (
          <div>
            <div className="panel">
              <h2 style={{ fontSize: "18px", fontWeight: "600", marginBottom: "20px" }}>Failover Telemetry Logs</h2>
              
              <div className="terminal-panel" style={{ height: "500px" }}>
                <div className="terminal-header">
                  <span>TELEMETRY STACK AUDIT</span>
                  <span>IMMUTABLE DATABASE STATE</span>
                </div>
                <div className="terminal-body">
                  {events.length === 0 ? (
                    <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "40px" }}>Telemetry daemon idle. Turn on the daemon to view logs.</div>
                  ) : (
                    events.map((ev, idx) => (
                      <div className="log-entry" key={idx}>
                        <span className="log-timestamp">[{ev.timestamp}]</span>
                        <span className={`log-type ${ev.status}`}>{ev.event_type}</span>
                        <span className="log-details">{ev.details}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "settings" && (
          <div className="main-dashboard-layout">
            <div className="panel" style={{ gridColumn: "span 2" }}>
              <h2 style={{ fontSize: "18px", fontWeight: "600", marginBottom: "20px" }}>System Controller Settings</h2>
              
              <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                <div className="form-group" style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", background: "rgba(255,255,255,0.01)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
                  <div>
                    <h4 style={{ fontWeight: "600", marginBottom: "4px" }}>Telemetry Daemon Controller</h4>
                    <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>Actively queries targets and routes DNS/replica changes.</p>
                  </div>
                  <button onClick={handleToggleDaemon} className={`btn ${systemStatus.daemon_running ? "btn-danger" : "btn-primary"}`}>
                    {systemStatus.daemon_running ? "Stop Monitoring Daemon" : "Start Monitoring Daemon"}
                  </button>
                </div>

                <div className="panel" style={{ background: "rgba(255,255,255,0.005)", border: "1px solid var(--border-color)" }}>
                  <h3 style={{ fontSize: "15px", fontWeight: "600", marginBottom: "16px" }}>Update Check Targets</h3>
                  <form onSubmit={handleSaveEndpoints}>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
                      <div className="form-group">
                        <label className="form-label">Primary Endpoint URL</label>
                        <input type="text" className="form-input code-style" value={primaryUrl} onChange={e => setPrimaryUrl(e.target.value)} />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Primary Max Latency (ms)</label>
                        <input type="number" className="form-input code-style" value={primaryThresh} onChange={e => setPrimaryThresh(e.target.value)} />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Secondary Endpoint URL</label>
                        <input type="text" className="form-input code-style" value={secondaryUrl} onChange={e => setSecondaryUrl(e.target.value)} />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Secondary Max Latency (ms)</label>
                        <input type="number" className="form-input code-style" value={secondaryThresh} onChange={e => setSecondaryThresh(e.target.value)} />
                      </div>
                    </div>
                    <button type="submit" className="btn btn-primary" style={{ marginTop: "12px" }}>Save Endpoint Configs</button>
                  </form>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
