import { useState } from "react";
import API_BASE from "../api";

export default function Custom() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const submit = async (e) => {
    e.preventDefault();

    const file = e.target.video.files[0];
    const threshold = e.target.threshold.value;
    const frames = e.target.frames.value;

    if (!file) return;

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("video", file);
    formData.append("threshold", threshold);
    formData.append("num_frames", frames);

    const res = await fetch(`${API_BASE}/predict-custom`, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    setResult(data);
    setLoading(false);
  };

  const isFake = result?.result?.custom_prediction === "FAKE";

  return (
    <div className="section fade">
      <div className="section-header">
        <div>
          <h2 className="section-title">Custom Configuration</h2>
          <p className="section-desc">// Fine-tune detection parameters</p>
        </div>
      </div>

      <div className="card">
        <form onSubmit={submit}>
          <input type="file" name="video" accept="video/*" required />

          <div className="custom-params">
            <div className="custom-param-group">
              <label>Detection Threshold</label>
              <input type="number" name="threshold" step="0.05" min="0" max="1" defaultValue="0.5" />
            </div>
            <div className="custom-param-group">
              <label>Frames to Sample</label>
              <input type="number" name="frames" min="1" max="50" defaultValue="10" />
            </div>
          </div>

          <button type="submit" disabled={loading}>
            {loading ? "⏳ Processing..." : "⚡ Run Custom Analysis"}
          </button>
        </form>
      </div>

      {loading && (
        <div className="card" style={{ textAlign: "center", padding: "36px" }}>
          <div className="spinner" />
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: "var(--muted)" }}>
            Running custom scan...
          </p>
        </div>
      )}

      {result?.success && (
        <div className="card">
          <div className={`verdict-badge ${isFake ? "verdict-fake" : "verdict-real"}`}>
            {isFake ? "⚠ FAKE" : "✓ REAL"} — {result.result.custom_prediction}
          </div>

          <div className="conf-wrap">
            <div className="conf-label">
              <span>Confidence</span>
              <span>{(result.result.custom_confidence * 100).toFixed(2)}%</span>
            </div>
            <div className="conf-track">
              <div
                className={`conf-fill ${isFake ? "conf-fill--fake" : "conf-fill--real"}`}
                style={{ width: `${result.result.custom_confidence * 100}%` }}
              />
            </div>
          </div>

          <div className="custom-meta-grid">
            {[
              ["Frames Analyzed", result.result.frames_analyzed],
              ["Threshold Used",  result.result.threshold_used],
            ].map(([k, v]) => (
              <div key={k} className="custom-meta-pill">
                <span className="custom-meta-key">{k}</span>
                <span className="custom-meta-val">{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
