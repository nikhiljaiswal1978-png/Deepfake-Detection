import { useEffect, useState } from "react";
import API_BASE from "../api";

export default function Stats() {
  const [stats, setStats] = useState(null);

  const loadStats = async () => {
    const res = await fetch(`${API_BASE}/stats`);
    const data = await res.json();
    setStats(data);
  };

  useEffect(() => {
    loadStats();
  }, []);

  if (!stats) return (
    <div className="card" style={{ textAlign: "center", padding: "36px" }}>
      <div className="spinner" />
      <p style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: "var(--muted)" }}>
        Loading statistics...
      </p>
    </div>
  );

  return (
    <div className="section fade">
      <div className="section-header">
        <div>
          <h2 className="section-title">Usage Statistics</h2>
          <p className="section-desc">// System-wide detection metrics</p>
        </div>
        <button className="btn-ghost" onClick={loadStats}>↻ Refresh</button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.total_predictions}</div>
          <div className="stat-label">Total Predictions</div>
        </div>

        <div className="stat-card" style={{ "--card-color": "var(--safe)" }}>
          <div className="stat-value" style={{ color: "var(--safe)" }}>{stats.real_count}</div>
          <div className="stat-label">Real Videos ({stats.real_percentage})</div>
        </div>

        <div className="stat-card">
          <div className="stat-value" style={{ color: "var(--danger)" }}>{stats.fake_count}</div>
          <div className="stat-label">Fake Videos ({stats.fake_percentage})</div>
        </div>

        <div className="stat-card">
          <div className="stat-value" style={{ color: "var(--accent3)" }}>{stats.average_confidence}</div>
          <div className="stat-label">Average Confidence</div>
        </div>
      </div>

      <div className="card stats-meta">
        <div className="stats-meta-row">
          <span className="stats-meta-key">API Started</span>
          <span className="stats-meta-val">{stats.started_at}</span>
        </div>
      </div>
    </div>
  );
}
