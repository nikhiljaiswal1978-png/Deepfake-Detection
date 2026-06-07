import { useState } from "react";

import Header from "./components/Header";
import Tabs from "./components/Tabs";
import Prediction from "./components/Prediction";
import Batch from "./components/Batch";
import Custom from "./components/Custom";
import VideoInfo from "./components/VideoInfo";
import Stats from "./components/Stats";
import Model from "./components/Model";
import Logs from "./components/Logs";
import LivePreview from "./components/LivePreview";

import "./App.css";

export default function App() {
  const [activeTab, setActiveTab] = useState("prediction");

  return (
    <>
      <Header />
      <Tabs activeTab={activeTab} setActiveTab={setActiveTab} />

      <main style={{ marginTop: "28px" }}>
        {activeTab === "prediction"   && <Prediction />}
        {activeTab === "batch"        && <Batch />}
        {activeTab === "custom"       && <Custom />}
        {activeTab === "video-info"   && <VideoInfo />}
        {activeTab === "stats"        && <Stats />}
        {activeTab === "model"        && <Model />}
        {activeTab === "logs"         && <Logs />}
        {activeTab === "live-preview" && <LivePreview />}
      </main>

      <footer className="app-footer">
        <p>
          © 2026 DeepfakeShield&nbsp;
          <span>·</span> EfficientNet-B4
          <span>·</span> Built with AI &amp; ML
        </p>
      </footer>
    </>
  );
}