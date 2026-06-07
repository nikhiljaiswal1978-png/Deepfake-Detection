import { useState } from "react";
import API_BASE from "../api";

export default function Logs() {
  const [logs, setLogs] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadLogs = async () => {
    setLoading(true);
    const res = await fetch(`${API_BASE}/logs`);
    const data = await res.json();
    setLogs(data);
    setLoading(false);
  };

  return (
    <div className="section fade">
      <div className="section-header">
        <div>
          <h2 className="section-title">System Logs</h2>
          <p className="section-desc">// Real-time system event stream</p>
        </div>
        <button className="logs-refresh-btn" onClick={loadLogs} disabled={loading}>
          {loading ? "⏳ Loading..." : "↻ Fetch Logs"}
        </button>
      </div>

      {logs?.success && (
        <div className="card">
          <div className="logs-count">
            SHOWING {logs.showing} / {logs.total_lines} ENTRIES
          </div>
          <pre>{logs.logs.join("\n")}</pre>
        </div>
      )}

      {logs && !logs.success && (
        <div className="error">{logs.error}</div>
      )}

    </div>
  );
}
