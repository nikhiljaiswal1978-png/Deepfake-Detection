import { useState } from "react";
import API_BASE from "../api";

export default function Prediction() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    const file = e.target.video.files[0];
    if (!file) return;

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("video", file);

    const res = await fetch(`${API_BASE}/predict`, { method: "POST", body: formData });
    const data = await res.json();

    setResult(data);
    setLoading(false);
  };

  const isFake = result?.result?.prediction === "FAKE";

  return (
    <div className="section fade">
      <div className="section-header">
        <div>
          <h2 className="section-title">Single Video Analysis</h2>
          <p className="section-desc">// Upload one video for deep forensic scan</p>
        </div>
      </div>

      <div className="card">
        <form onSubmit={submit}>
          <input type="file" name="video" accept="video/*" required />
          <button type="submit" disabled={loading}>
            {loading ? "⏳ Analyzing..." : "▶ Analyze Video"}
          </button>
        </form>
      </div>

      {loading && (
        <div className="card" style={{ textAlign: "center", padding: "36px" }}>
          <div className="spinner" />
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: "var(--muted)" }}>
            Scanning video frames...
          </p>
        </div>
      )}

      {result?.success && (
        <div className="card result-card">
          <h3 className="result-filename">{result.filename}</h3>
          <div className={`verdict-badge ${isFake ? "verdict-fake" : "verdict-real"}`}>
            {isFake ? "⚠ FAKE" : "✓ REAL"}
          </div>
          <div className="conf-wrap">
            <div className="conf-label">
              <span>Confidence</span>
              <span>{(result.result.confidence * 100).toFixed(2)}%</span>
            </div>
            <div className="conf-track">
              <div
                className={`conf-fill ${isFake ? "conf-fill--fake" : "conf-fill--real"}`}
                style={{ width: `${result.result.confidence * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
