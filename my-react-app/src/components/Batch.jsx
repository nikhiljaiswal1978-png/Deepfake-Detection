import { useState } from "react";
import API_BASE from "../api";

export default function Batch() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    const files = e.target.videos.files;
    if (!files.length) return;

    if (files.length > 10) {
      alert("Maximum 10 videos allowed");
      return;
    }

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    Array.from(files).forEach((file) => {
      formData.append("videos", file);
    });

    const res = await fetch(`${API_BASE}/predict-batch`, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    setResult(data);
    setLoading(false);
  };

  return (
    <div className="section fade">
      <div className="section-header">
        <div>
          <h2 className="section-title">Batch Processing</h2>
          <p className="section-desc">// Analyze up to 10 videos simultaneously</p>
        </div>
      </div>

      <div className="card">
        <form onSubmit={submit}>
          <input type="file" name="videos" multiple accept="video/*" />
          <button type="submit" disabled={loading}>
            {loading ? "⏳ Processing..." : "▶ Analyze Batch"}
          </button>
        </form>
      </div>

      {loading && (
        <div className="card" style={{ textAlign: "center", padding: "36px" }}>
          <div className="spinner" />
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: "var(--muted)" }}>
            Processing batch...
          </p>
        </div>
      )}

      {result?.success && (
        <div className="card">
          <div className="batch-summary">
            {[
              ["Total",      result.total,      "var(--text)"],
              ["Successful", result.successful, "var(--safe)"],
              ["Failed",     result.failed,     "var(--danger)"],
            ].map(([label, val, color]) => (
              <div key={label} className="batch-stat">
                <div className="batch-stat__label">{label}</div>
                <div className="batch-stat__val" style={{ color }}>{val}</div>
              </div>
            ))}
          </div>

          <table>
            <thead>
              <tr>
                <th>Filename</th>
                <th>Prediction</th>
                <th>Confidence</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {result.results.map((r, i) => (
                <tr key={i}>
                  <td>{r.filename}</td>
                  {r.success ? (
                    <>
                      <td style={{ color: r.result.prediction === "FAKE" ? "var(--danger)" : "var(--safe)", fontWeight: 700 }}>
                        {r.result.prediction}
                      </td>
                      <td>{(r.result.confidence * 100).toFixed(2)}%</td>
                      <td style={{ color: "var(--safe)" }}>✓ Success</td>
                    </>
                  ) : (
                    <>
                      <td colSpan="2" style={{ color: "var(--danger)" }}>{r.error}</td>
                      <td style={{ color: "var(--danger)" }}>✗ Failed</td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      </div>
  );
}
