export default function Tabs({ activeTab, setActiveTab }) {
  const tabs = [
    ["prediction",   "🎥", "Prediction"],
    ["batch",        "📂", "Batch"],
    ["custom",       "⚙",  "Custom"],
    ["video-info",   "📄", "Video Info"],
    ["stats",        "📊", "Stats"],
    ["model",        "🧠", "Model"],
    ["logs",         "📝", "Logs"],
    ["live-preview", "🎬", "Live Preview"],
  ];

  return (
    <>
      <nav className="tabs-wrapper">
        <div className="tabs">
          {tabs.map(([key, icon, label]) => (
            <button
              key={key}
              className={`tab ${activeTab === key ? "active" : ""}`}
              onClick={() => setActiveTab(key)}
            >
              <span>{icon}</span> {label}
            </button>
          ))}
        </div>
      </nav>

      <style>{`
        .tabs-wrapper {
          padding: 24px 0 0;
          animation: fadeUp 0.5s 0.1s ease both;
        }

        .tabs {
          display: flex;
          gap: 4px;
          flex-wrap: wrap;
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 14px;
          padding: 6px;
          overflow-x: auto;
        }

        .tabs::-webkit-scrollbar {
          height: 0;
        }

        .tab {
          font-family: var(--font-display);
          font-size: 13px;
          font-weight: 600;
          padding: 9px 16px;
          border-radius: 10px;
          border: 1px solid transparent;
          background: transparent;
          color: var(--muted);
          cursor: pointer;
          transition: all 0.2s;
          white-space: nowrap;
          flex-shrink: 0;
          display: flex;
          align-items: center;
          gap: 6px;
          margin-top: 0;
        }

        .tab:hover {
          color: var(--text);
          background: rgba(255, 255, 255, 0.04);
          transform: none;
          box-shadow: none;
        }

        .tab.active {
          background: linear-gradient(135deg, rgba(99,255,218,0.15), rgba(167,139,250,0.15));
          color: var(--accent);
          border-color: var(--border-bright);
          box-shadow: 0 0 20px rgba(99,255,218,0.08);
        }
      `}</style>
    </>
  );
}
