import { useState } from "react";
import API_BASE from "../api";

export default function LiveAnalysis() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [currentFrame, setCurrentFrame] = useState(0);

  const analyzeVideo = async (e) => {
    e.preventDefault();
    const file = e.target.video.files[0];
    if (!file) return;

    setLoading(true);
    setResults(null);
    setCurrentFrame(0);

    const formData = new FormData();
    formData.append("video", file);

    try {
      const res = await fetch(`${API_BASE}/analyze-live`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (data.success) {
        setResults(data);
      } else {
        alert("Error: " + (data.error || "Unknown error"));
      }
    } catch (error) {
      alert("Error analyzing video: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  const showFrame = (index) => {
    setCurrentFrame(index);
  };

  const nextFrame = () => {
    if (currentFrame < results.frame_predictions.length - 1) {
      setCurrentFrame(currentFrame + 1);
    }
  };

  const prevFrame = () => {
    if (currentFrame > 0) {
      setCurrentFrame(currentFrame - 1);
    }
  };

  const frame = results?.frame_predictions[currentFrame];
  const isFake = frame?.prediction === "FAKE";

  return (
    <div className="section fade">
      <h2>🎬 Live Frame Analysis</h2>

      {/* Upload Form */}
      <div style={{ marginBottom: "2rem" }}>
        <input
          type="file"
          id="videoUpload"
          accept="video/*"
          onChange={(e) => {
            const fileInput = e.target;
            if (fileInput.files[0]) {
              analyzeVideo({ preventDefault: () => {}, target: { video: fileInput } });
            }
          }}
          style={{ display: "none" }}
        />
        <label htmlFor="videoUpload" style={{ cursor: "pointer", display: "inline-block" }}>
          <div
            style={{
              padding: "1rem 2rem",
              background: loading ? "#555" : "linear-gradient(135deg, #63ffda, #00c9a0)",
              color: loading ? "white" : "#030712",
              borderRadius: "8px",
              display: "inline-block",
              fontWeight: "600",
            }}
          >
            {loading ? "Analyzing..." : "Choose Video to Analyze"}
          </div>
        </label>
        <p style={{ fontSize: "0.9rem", color: "#999", marginTop: "0.5rem" }}>
          Analyzes 10 key frames with predictions + heatmaps
        </p>
      </div>

      {/* Loading State */}
      {loading && (
        <div style={{ textAlign: "center", padding: "2rem" }}>
          <div className="spinner"></div>
          <p>⏳ Analyzing video frames...</p>
          <p style={{ color: "#999" }}>This may take a moment</p>
        </div>
      )}

      {/* Results */}
      {results && (
        <>
          {/* Overall Summary */}
          <div className="result" style={{ marginBottom: "2rem" }}>
            <h3>Overall Prediction</h3>
            <p
              style={{
                fontSize: "2rem",
                fontWeight: "bold",
                color: results.overall_prediction === "FAKE" ? "#ef4444" : "#22c55e",
              }}
            >
              {results.overall_prediction}
            </p>
            <p>Confidence: {(results.overall_confidence * 100).toFixed(1)}%</p>
            <p style={{ color: "#999" }}>
              Analyzed {results.frames_analyzed} frames from {results.duration.toFixed(1)}s video
            </p>
          </div>

          {/* Frame Timeline */}
          <div style={{ marginBottom: "2rem" }}>
            <h3>Frame Timeline</h3>
            <div
              style={{
                display: "flex",
                gap: "0.5rem",
                overflowX: "auto",
                paddingBottom: "1rem",
              }}
            >
              {results.frame_predictions.map((f, idx) => (
                <button
                  key={idx}
                  onClick={() => showFrame(idx)}
                  style={{
                    flexShrink: 0,
                    width: "80px",
                    height: "80px",
                    padding: 0,
                    border: `2px solid ${idx === currentFrame ? "#3b82f6" : "#555"}`,
                    borderRadius: "8px",
                    overflow: "hidden",
                    cursor: "pointer",
                    background: "none",
                  }}
                >
                  <img
                    src={f.frame_image}
                    alt={`Frame ${idx}`}
                    style={{ width: "100%", height: "calc(100% - 20px)", objectFit: "cover" }}
                  />
                  <div
                    style={{
                      height: "20px",
                      background: f.prediction === "FAKE" ? "#ef4444" : "#22c55e",
                      color: "white",
                      fontSize: "0.7rem",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    {f.prediction}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Current Frame Display */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: window.innerWidth > 768 ? "1fr 1fr" : "1fr",
              gap: "2rem",
              marginBottom: "2rem",
            }}
          >
            {/* Original Frame */}
            <div className="result">
              <h3>Original Frame</h3>
              <div style={{ position: "relative" }}>
                <img
                  src={frame.frame_image}
                  alt="Current frame"
                  style={{
                    width: "100%",
                    borderRadius: "8px",
                    boxShadow: isFake
                      ? "0 0 20px rgba(239, 68, 68, 0.5)"
                      : "0 0 20px rgba(34, 197, 94, 0.5)",
                  }}
                />
                <div
                  style={{
                    position: "absolute",
                    top: "1rem",
                    right: "1rem",
                    padding: "0.5rem 1rem",
                    borderRadius: "8px",
                    background: isFake ? "#ef4444" : "#22c55e",
                    color: "white",
                    fontWeight: "bold",
                    fontSize: "1.2rem",
                  }}
                >
                  {frame.prediction}
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "1rem" }}>
                <div>
                  <p style={{ color: "#999" }}>Frame Number</p>
                  <p style={{ fontSize: "1.5rem", fontWeight: "bold" }}>#{frame.frame_number}</p>
                </div>
                <div>
                  <p style={{ color: "#999" }}>Timestamp</p>
                  <p style={{ fontSize: "1.5rem", fontWeight: "bold" }}>{frame.timestamp.toFixed(2)}s</p>
                </div>
              </div>
            </div>

            {/* Heatmap */}
            <div className="result">
              <h3>Focus Areas (Grad-CAM)</h3>
              <img
                src={frame.heatmap_image || frame.frame_image}
                alt="Heatmap"
                style={{ width: "100%", borderRadius: "8px" }}
              />
              <div style={{ marginTop: "1rem" }}>
                <p style={{ color: "#999", marginBottom: "0.5rem" }}>Confidence Score</p>
                <div
                  style={{
                    width: "100%",
                    height: "1rem",
                    background: "#374151",
                    borderRadius: "9999px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: `${frame.confidence * 100}%`,
                      background: isFake ? "#ef4444" : "#22c55e",
                      borderRadius: "9999px",
                      transition: "width 0.5s",
                    }}
                  />
                </div>
                <p style={{ textAlign: "right", fontSize: "0.9rem", marginTop: "0.25rem" }}>
                  {(frame.confidence * 100).toFixed(1)}%
                </p>
              </div>
              <div style={{ marginTop: "1rem", fontSize: "0.9rem", color: "#999" }}>
                <p>🔥 Red/Yellow areas = Model's focus regions</p>
                <p>🔵 Blue areas = Less relevant for decision</p>
              </div>
            </div>
          </div>

          {/* Navigation Controls */}
          <div style={{ display: "flex", justifyContent: "center", gap: "1rem", flexWrap: "wrap" }}>
            <button
              onClick={prevFrame}
              disabled={currentFrame === 0}
              style={{
                padding: "0.75rem 1.5rem",
                background: currentFrame === 0 ? "#555" : "#374151",
                color: "white",
                border: "none",
                borderRadius: "8px",
                cursor: currentFrame === 0 ? "not-allowed" : "pointer",
                fontWeight: "600",
                opacity: currentFrame === 0 ? 0.5 : 1,
              }}
            >
              ← Previous Frame
            </button>
            <button
              onClick={nextFrame}
              disabled={currentFrame === results.frame_predictions.length - 1}
              style={{
                padding: "0.75rem 1.5rem",
                background:
                  currentFrame === results.frame_predictions.length - 1 ? "#555" : "#374151",
                color: "white",
                border: "none",
                borderRadius: "8px",
                cursor:
                  currentFrame === results.frame_predictions.length - 1
                    ? "not-allowed"
                    : "pointer",
                fontWeight: "600",
                opacity: currentFrame === results.frame_predictions.length - 1 ? 0.5 : 1,
              }}
            >
              Next Frame →
            </button>
          </div>
        </>
      )}

      <style>{`
        .spinner {
          border: 3px solid #374151;
          border-top: 3px solid #3b82f6;
          border-radius: 50%;
          width: 3rem;
          height: 3rem;
          animation: spin 1s linear infinite;
          margin: 0 auto 1rem;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}