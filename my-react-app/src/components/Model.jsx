import { useState } from "react";
import API_BASE from "../api";

export default function Model() {
  const [model, setModel] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadModelInfo = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/model-info`);
      const data = await res.json();
      setModel(data);
    } catch (err) {
      console.error("Failed to load model info", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="section fade">
      <div className="section-header">
        <div>
          <h2 className="section-title">Model Details</h2>
          <p className="section-desc">// Architecture and performance metrics</p>
        </div>
        {!model && (
          <button className="btn-primary-sm" onClick={loadModelInfo} disabled={loading}>
            {loading ? "Loading..." : "Load Model Info"}
          </button>
        )}
      </div>

      {loading && (
        <div className="card" style={{ textAlign: "center", padding: "36px" }}>
          <div className="spinner" />
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: "var(--muted)" }}>
            Loading model data...
          </p>
        </div>
      )}

      {model && (
        <>
          <div className="card model-identity">
            <div className="model-name-row">
              <div>
                <h3 className="model-name">{model.model_name}</h3>
                <p className="model-sub">{model.architecture} · {model.framework}</p>
              </div>
              <span className="model-loaded-badge">● LOADED</span>
            </div>
          </div>

          <div className="model-two-col">
            {/* Performance */}
            <div className="card">
              <h4 className="model-section-title">📈 Performance</h4>
              <div className="metrics-list">
                {[
                  ["Validation Accuracy", model.performance_metrics.validation_accuracy],
                  ["AUC Score",           model.performance_metrics.auc_score],
                  ["Precision",           model.performance_metrics.precision],
                  ["Recall",              model.performance_metrics.recall],
                  ["F1 Score",            model.performance_metrics.f1_score],
                ].map(([k, v]) => (
                  <div key={k} className="metric-pill">
                    <span className="metric-name">{k}</span>
                    <span className="metric-val">{v}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Training */}
            <div className="card">
              <h4 className="model-section-title">🗂 Training Details</h4>
              {[
                ["Dataset",       model.training_details.dataset],
                ["Total Videos",  model.training_details.total_videos],
                ["Total Frames",  model.training_details.total_frames],
                ["Epochs",        model.training_details.epochs],
                ["Batch Size",    model.training_details.batch_size],
              ].map(([k, v]) => (
                <div key={k} className="training-row">
                  <span className="training-key">{k}</span>
                  <span className="training-val">{v}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

    </div>
  );
}
