export default function Header() {
  return (
    <header className="app-header">
      <div className="app-header__left">
        <div className="app-header__icon">🎭</div>
        <div>
          <h1 className="app-header__title">
            Deepfake<span>Shield</span>
          </h1>
          <p className="app-header__sub">// AI-Powered Video Forensics</p>
        </div>
      </div>

      <div className="app-header__badges">
        <span className="badge badge--green">Accuracy 99.08%</span>
        <span className="badge badge--cyan">EfficientNet-B4</span>
        <span className="badge badge--purple">v1.0</span>
      </div>

    </header>
  );
}
