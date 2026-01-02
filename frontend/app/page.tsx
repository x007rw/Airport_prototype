"use client";

import { useState, useEffect, useRef } from "react";
import axios from "axios";
import {
  Plane, Terminal, Play, Power, Activity,
  Video, FileText, Monitor, CheckCircle, AlertTriangle
} from "lucide-react";
import clsx from "clsx";

// Use relative path with Next.js proxy settings for stability
const API_URL = "/api";

type LogResponse = { logs: string };
type StatusResponse = { status: "running" | "idle" };
type VideoListResponse = string[];

export default function Home() {
  const [logs, setLogs] = useState<string>("");
  const [status, setStatus] = useState<"running" | "idle">("idle");
  const [videos, setVideos] = useState<string[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"dashboard" | "videos">("dashboard");
  const logEndRef = useRef<HTMLDivElement>(null);

  // Polling Status & Logs
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const statusRes = await axios.get<StatusResponse>(`${API_URL}/status`);
        setStatus(statusRes.data.status);

        const logsRes = await axios.get<LogResponse>(`${API_URL}/logs`);
        setLogs(logsRes.data.logs);
      } catch (e) {
        console.error("API Polling Error", e);
      }
    }, 2000); // 2s polling

    return () => clearInterval(interval);
  }, []);

  // Fetch videos on tab change
  useEffect(() => {
    if (activeTab === "videos") {
      axios.get<VideoListResponse>(`${API_URL}/videos`)
        .then(res => setVideos(res.data))
        .catch(console.error);
    }
  }, [activeTab]);

  // Auto-scroll logs
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const launchMission = async (mode: string, scenario?: string) => {
    try {
      await axios.post(`${API_URL}/run`, { mode, scenario });
      alert(`Mission ${mode} launched!`);
    } catch (e: any) {
      alert(`Launch Failed: ${e.response?.data?.detail || e.message}`);
    }
  };

  return (
    <main className="min-h-screen bg-black text-white p-8 grid grid-cols-12 gap-6">

      {/* SIDEBAR */}
      <aside className="col-span-3 lg:col-span-2 flex flex-col gap-6 border-r border-gray-800 pr-6">
        <div className="flex items-center gap-3 mb-8">
          <Plane className="w-8 h-8 text-sky-400" />
          <h1 className="text-2xl font-bold font-orbitron tracking-widest text-white tracking-widest">
            AIRPORT
          </h1>
        </div>

        <nav className="flex flex-col gap-2">
          <button
            onClick={() => setActiveTab("dashboard")}
            className={clsx(
              "flex items-center gap-3 p-3 rounded-md text-left transition-colors font-orbitron",
              activeTab === "dashboard" ? "bg-sky-900/30 text-sky-400 border-l-4 border-sky-400" : "hover:bg-gray-900 text-gray-400"
            )}
          >
            <Activity className="w-5 h-5" />
            Cockpit
          </button>

          <button
            onClick={() => setActiveTab("videos")}
            className={clsx(
              "flex items-center gap-3 p-3 rounded-md text-left transition-colors font-orbitron",
              activeTab === "videos" ? "bg-sky-900/30 text-sky-400 border-l-4 border-sky-400" : "hover:bg-gray-900 text-gray-400"
            )}
          >
            <Video className="w-5 h-5" />
            Flight Recorder
          </button>
        </nav>

        <div className="mt-auto p-4 border border-gray-800 bg-gray-950 rounded-lg">
          <h3 className="text-xs text-gray-500 font-orbitron mb-2 uppercase">System Status</h3>
          <div className="flex items-center gap-2">
            <div className={clsx("w-3 h-3 rounded-full animate-pulse", status === "running" ? "bg-green-500" : "bg-gray-500")}></div>
            <span className="text-sm font-bold uppercase">{status}</span>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <div className="col-span-9 lg:col-span-10 flex flex-col gap-6">

        {activeTab === "dashboard" && (
          <>
            {/* MISSION CONTROL */}
            <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-950 border border-gray-800 p-6 rounded-lg hover:border-sky-500/50 transition-all group relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                  <Monitor className="w-24 h-24 text-sky-500" />
                </div>
                <h2 className="text-xl font-orbitron text-sky-400 mb-2">Web Scraper</h2>
                <p className="text-gray-400 text-sm mb-4">Vision Search & Extraction (TUT Phone)</p>
                <button
                  onClick={() => launchMission("web", "scenarios/task_tut_phone_ddg.yaml")}
                  disabled={status === "running"}
                  className="bg-sky-600 hover:bg-sky-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded font-bold flex items-center gap-2 w-full justify-center"
                >
                  <Play className="w-4 h-4" /> LAUNCH MISSION
                </button>
              </div>

              <div className="bg-gray-950 border border-gray-800 p-6 rounded-lg hover:border-sky-500/50 transition-all group relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                  <FileText className="w-24 h-24 text-purple-500" />
                </div>
                <h2 className="text-xl font-orbitron text-purple-400 mb-2">Integration</h2>
                <p className="text-gray-400 text-sm mb-4">Web Search &rarr; Desktop Notepad Save</p>
                <button
                  onClick={() => launchMission("weather_demo")}
                  disabled={status === "running"}
                  className="bg-purple-600 hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded font-bold flex items-center gap-2 w-full justify-center"
                >
                  <Play className="w-4 h-4" /> LAUNCH DEMO
                </button>
              </div>

              <div className="bg-gray-950 border border-gray-800 p-6 rounded-lg hover:border-sky-500/50 transition-all group relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                  <AlertTriangle className="w-24 h-24 text-red-500" />
                </div>
                <h2 className="text-xl font-orbitron text-red-400 mb-2">Emergency</h2>
                <p className="text-gray-400 text-sm mb-4">Force Stop All Agents (Not Implemented)</p>
                <button
                  disabled
                  className="bg-red-900/50 text-red-400 border border-red-800 px-4 py-2 rounded font-bold w-full flex items-center gap-2 justify-center cursor-not-allowed"
                >
                  <Power className="w-4 h-4" /> ABORT
                </button>
              </div>
            </section>

            {/* LIVE TERMINAL */}
            <section className="flex-grow bg-black border border-gray-800 rounded-lg p-4 font-mono text-sm overflow-hidden flex flex-col shadow-[0_0_20px_rgba(0,0,0,0.5)]">
              <div className="flex items-center gap-2 text-gray-500 border-b border-gray-800 pb-2 mb-2">
                <Terminal className="w-4 h-4" />
                <span>root@airport-agent:~/logs</span>
              </div>
              <div className="flex-grow overflow-y-auto h-[400px] whitespace-pre-wrap text-green-400 space-y-1 scrollbar-thin scrollbar-thumb-gray-800">
                {logs || "Waiting for mission logs..."}
                <div ref={logEndRef} />
              </div>
            </section>
          </>
        )}

        {activeTab === "videos" && (
          <section className="grid grid-cols-1 md:grid-cols-2 gap-6 h-full">
            {/* Video List */}
            <div className="bg-gray-950 border border-gray-800 rounded-lg p-4 h-[600px] overflow-y-auto">
              <h2 className="text-xl font-orbitron text-white mb-4 flex items-center gap-2">
                <Video className="w-5 h-5 text-sky-400" /> Recordings
              </h2>
              <div className="space-y-2">
                {videos.length === 0 && <p className="text-gray-500">No recordings found.</p>}
                {videos.map(video => (
                  <div
                    key={video}
                    onClick={() => setSelectedVideo(video)}
                    className={clsx(
                      "p-3 rounded border cursor-pointer transition-all flex items-center justify-between",
                      selectedVideo === video
                        ? "bg-sky-900/20 border-sky-500 text-sky-300"
                        : "bg-black border-gray-800 text-gray-400 hover:bg-gray-900"
                    )}
                  >
                    <span className="truncate">{video}</span>
                    <Play className="w-4 h-4 opacity-50" />
                  </div>
                ))}
              </div>
            </div>

            {/* Player */}
            <div className="bg-black border border-gray-800 rounded-lg p-4 flex flex-col items-center justify-center relative">
              {selectedVideo ? (
                <div className="w-full h-full flex flex-col gap-2">
                  <h3 className="text-gray-400 text-xs text-center">{selectedVideo}</h3>
                  <video
                    controls
                    autoPlay
                    className="w-full h-auto max-h-[500px] border border-gray-700 rounded shadow-lg"
                    src={`${API_URL}/videos/${selectedVideo}`}
                  >
                    Your browser does not support the video tag.
                  </video>
                  <a
                    href={`${API_URL}/videos/${selectedVideo}`}
                    download
                    className="mt-4 text-center text-sky-500 hover:text-sky-400 text-sm"
                  >
                    Download Video
                  </a>
                </div>
              ) : (
                <div className="text-gray-600 flex flex-col items-center">
                  <Video className="w-16 h-16 mb-4 opacity-20" />
                  <p>Select a recording to play</p>
                </div>
              )}
            </div>
          </section>
        )}

      </div>
    </main>
  );
}
