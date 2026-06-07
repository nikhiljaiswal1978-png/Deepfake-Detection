import { useState, useRef } from "react";
import API_BASE from "../api";

export default function VideoInfo() {
  const [loading, setLoading] = useState(false);
  const [info, setInfo] = useState(null);
  const [error, setError] = useState(null);
  const [videoURL, setVideoURL] = useState(null);
  const fileInputRef = useRef(null);

  const submit = async (e) => {
    e.preventDefault();
    const file = fileInputRef.current.files[0];
    if (!file) return;

    setLoading(true);
    setInfo(null);
    setError(null);
    setVideoURL(null);

    const formData = new FormData();
    formData.append("video", file);

    try {
      const res = await fetch(`${API_BASE}/video-info`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        setInfo(data.info);
        setVideoURL(`${API_BASE}/serve-video/${data.info.filename}`);
      } else {
        setError(data.error || "Failed to extract video info");
      }
    } catch (err) {
      setError("Server connection error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="section fade">
      <h2>Video Metadata</h2>

      <form onSubmit={submit}>
        <input
          type="file"
          ref={fileInputRef}
          accept="video/*"
          required
        />
        <button type="submit">Extract Info</button>
      </form>

      {loading && <p>⏳ Extracting metadata...</p>}
      {error && <div className="error">{error}</div>}

      {videoURL && (
        <div style={{ marginTop: "20px" }}>
          <h3>Video Preview</h3>
          <video
            key={videoURL}
            controls
            width="100%"
            src={videoURL}
            style={{ borderRadius: "12px", maxHeight: "400px", display: "block" }}
          />
        </div>
      )}

      {info && (
        <div className="result">
          <h3>Video Metadata</h3>
          <p><strong>Filename:</strong> {info.filename}</p>
          <p><strong>Duration:</strong> {info.duration_seconds} seconds</p>
          <p><strong>Resolution:</strong> {info.width} × {info.height}</p>
          <p><strong>FPS:</strong> {info.fps}</p>
          <p><strong>Total Frames:</strong> {info.total_frames}</p>
          <p><strong>File Size:</strong> {info.file_size_mb} MB</p>
        </div>
      )}
    </div>
  );
}