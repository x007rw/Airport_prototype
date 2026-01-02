"use client";

import { useState, useEffect, useRef } from "react";
import axios from "axios";
import {
  Plane, Terminal, Play, Power, Activity,
  Video, FileText, Monitor, CheckCircle, AlertTriangle,
  Send, User, Bot, Loader2, Rocket, History, HardDrive
} from "lucide-react";
import clsx from "clsx";

const API_URL = "/api";

type Message = {
  role: "user" | "attendant";
  text: string;
};

type Flight = {
  flight_id: string;
  start_time: string;
  end_time?: string;
  status: string;
  mission: string;
};

type LogEntry = {
  timestamp: string;
  type: string;
  details: string;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "attendant", text: "機長、おはようございます。本日のミッションプラン作成をサポートいたします。どのような任務を実行しますか？" }
  ]);
  const [input, setInput] = useState("");
  const [logs, setLogs] = useState<string>("");
  const [status, setStatus] = useState<"running" | "idle">("idle");
  const [activeTab, setActiveTab] = useState<"live" | "plan" | "recorder">("live");
  const [isPlanning, setIsPlanning] = useState(false);

  // Recorder State
  const [flights, setFlights] = useState<Flight[]>([]);
  const [selectedFlightId, setSelectedFlightId] = useState<string | null>(null);
  const [flightLogs, setFlightLogs] = useState<LogEntry[]>([]);

  const logEndRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Polling Status & Logs
  useEffect(() => {
    let lastStatus = "idle";
    const interval = setInterval(async () => {
      try {
        const statusRes = await axios.get(`${API_URL}/status`);
        const currentStatus = statusRes.data.status;
        setStatus(currentStatus);

        // If mission just finished, load flight history automatically
        if (lastStatus === "running" && currentStatus === "idle") {
          fetchFlights();
          setMessages(prev => [...prev, { role: "attendant", text: "ミッション完了。Flight Recorderにブラックボックスデータを転送しました。右画面で確認できます。" }]);
          setActiveTab("recorder");
        }
        lastStatus = currentStatus;

        const logsRes = await axios.get(`${API_URL}/logs`);
        setLogs(logsRes.data.logs);
      } catch (e) {
        console.error("API Polling Error", e);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (activeTab === "recorder") {
      fetchFlights();
    }
  }, [activeTab]);

  useEffect(() => {
    if (selectedFlightId) {
      fetchFlightDetails(selectedFlightId);
    }
  }, [selectedFlightId]);

  const fetchFlights = async () => {
    try {
      const res = await axios.get(`${API_URL}/flights`);
      setFlights(res.data.flights);
      // Auto-select most recent if none selected
      if (!selectedFlightId && res.data.flights.length > 0) {
        setSelectedFlightId(res.data.flights[0].flight_id);
      }
    } catch (e) { console.error(e); }
  };

  const fetchFlightDetails = async (id: string) => {
    try {
      const res = await axios.get(`${API_URL}/flights/${id}`);
      setFlightLogs(res.data.logs);
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = () => {
    if (!input.trim()) return;
    const newMessages = [...messages, { role: "user", text: input } as Message];
    setMessages(newMessages);
    setInput("");

    // Simulate Attendant thinking (In real implementation, this would call Gemini)
    setIsPlanning(true);
    setTimeout(() => {
      setMessages([...newMessages, {
        role: "attendant",
        text: "了解いたしました。ウェブ検索から情報を抽出し、デスクトップアプリへ記録するミッションプランを立案しました。格納庫（Hangar）の準備は完了しています。いつでも離陸可能です。"
      }]);
      setIsPlanning(false);
    }, 1500);
  };

  const handleTakeOff = async () => {
    try {
      // For prototype, we default to the integration demo
      await axios.post(`${API_URL}/run`, { mode: "weather_demo" });
      setMessages([...messages, { role: "attendant", text: "ミッションを開始します。フルスロットルで加速中。システムをモニタリングしています..." }]);
      setActiveTab("live"); // Switch to live view
    } catch (e: any) {
      alert("Take-off aborted: " + (e.response?.data?.detail || e.message));
    }
  };

  return (
    <main className="h-screen w-full bg-black text-white flex overflow-hidden font-sans">

      {/* LEFT: ATTENDANT CHAT (1/2) */}
      <section className="w-1/2 min-w-0 border-r border-gray-800 flex flex-col bg-gray-950/50 backdrop-blur-xl">
        <div className="p-6 border-b border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-sky-500/10 rounded-lg">
              <Bot className="w-6 h-6 text-sky-400" />
            </div>
            <div>
              <h1 className="text-lg font-orbitron tracking-tight">ATTENDANT</h1>
              <p className="text-[10px] text-sky-500 font-mono tracking-widest uppercase">Planning Officer</p>
            </div>
          </div>
          <div className={clsx("px-2 py-1 rounded text-[10px] font-mono", status === "running" ? "bg-green-500/20 text-green-400 border border-green-500/50" : "bg-gray-800 text-gray-500")}>
            {status.toUpperCase()}
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-grow overflow-y-auto p-6 space-y-6 scrollbar-hide">
          {messages.map((m, i) => (
            <div key={i} className={clsx("flex flex-col", m.role === "user" ? "items-end" : "items-start")}>
              <div className={clsx(
                "max-w-[85%] p-4 rounded-2xl text-sm leading-relaxed",
                m.role === "user" ? "bg-sky-600 text-white rounded-tr-none" : "bg-gray-900 text-gray-300 rounded-tl-none border border-gray-800"
              )}>
                {m.text}
              </div>
            </div>
          ))}
          {isPlanning && (
            <div className="flex items-center gap-2 text-sky-500 text-xs font-mono animate-pulse">
              <Loader2 className="w-3 h-3 animate-spin" /> Attendant is drafting plan...
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input & Take-off Area */}
        <div className="p-6 border-t border-gray-800 bg-black/50">
          <div className="relative mb-4">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              placeholder="Describe your mission..."
              className="w-full bg-gray-900 border border-gray-800 rounded-xl py-4 pl-4 pr-12 text-sm focus:outline-none focus:border-sky-500 transition-colors"
            />
            <button
              onClick={handleSendMessage}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-sky-500 hover:text-sky-400 p-2"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>

          <button
            onClick={handleTakeOff}
            disabled={status === "running"}
            className={clsx(
              "w-full py-5 rounded-xl font-orbitron tracking-[0.2em] relative overflow-hidden group transition-all duration-500",
              status === "running"
                ? "bg-gray-800 text-gray-600 cursor-not-allowed"
                : "bg-sky-600 hover:bg-sky-500 text-white shadow-[0_0_30px_rgba(14,165,233,0.3)]"
            )}
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:animate-shimmer" />
            <div className="flex items-center justify-center gap-3">
              <Rocket className={clsx("w-5 h-5", status !== "running" && "group-hover:-translate-y-1 transition-transform")} />
              TAKE-OFF
            </div>
          </button>
        </div>
      </section>

      {/* RIGHT: DASHBOARD (1/2) */}
      <section className="w-1/2 min-w-0 flex flex-col bg-black">
        {/* Top Navigation Tab */}
        <nav className="flex p-4 gap-2 border-b border-gray-900 bg-gray-950/20">
          {[
            { id: "live", label: "Live Viewport", icon: Monitor },
            { id: "plan", label: "Mission Plan", icon: FileText },
            { id: "recorder", label: "Flight Recorder", icon: HardDrive },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={clsx(
                "flex items-center gap-2 px-6 py-2 rounded-full text-xs font-orbitron transition-all",
                activeTab === tab.id ? "bg-sky-500/10 text-sky-400 border border-sky-500/30" : "text-gray-500 hover:text-gray-300"
              )}
            >
              <tab.icon className="w-3 h-3" />
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Dashboard Content */}
        <div className="flex-grow p-8 overflow-hidden flex flex-col">
          {activeTab === "live" && (
            <div className="flex-grow flex flex-col gap-6">
              <div className="flex-grow bg-gray-950 border border-gray-900 rounded-2xl relative overflow-hidden group">
                <div className="absolute inset-0 flex items-center justify-center text-gray-800 flex-col gap-4">
                  <Monitor className="w-16 h-16 opacity-10" />
                  <p className="text-xs uppercase tracking-[0.3em] opacity-40 font-orbitron">No Live stream from Captain</p>
                </div>
                {/* This would be where real-time screenshot stream goes */}
                <div className="absolute top-4 left-4 flex gap-2">
                  <div className="px-3 py-1 bg-red-500/20 border border-red-500/50 rounded text-[10px] text-red-400 flex items-center gap-2 animate-pulse">
                    <div className="w-1.5 h-1.5 bg-red-500 rounded-full" /> LIVE
                  </div>
                </div>
              </div>

              {/* Mini Terminal below Live View */}
              <div className="h-1/3 bg-black border border-gray-900 rounded-2xl p-6 font-mono text-[11px] overflow-hidden flex flex-col">
                <div className="flex items-center gap-2 text-sky-900 mb-4 font-bold border-b border-gray-900 pb-2">
                  <Terminal className="w-3 h-3" />
                  SYSTEM_TELEMETRY.LOG
                </div>
                <div className="flex-grow overflow-y-auto space-y-1 text-sky-400/80 custom-scrollbar">
                  {/* Reverse logs for display? No, keep it flowing */}
                  <pre className="whitespace-pre-wrap font-mono">{logs || "> Systems check complete. Awaiting Take-off instructions..."}</pre>
                  <div ref={logEndRef} />
                </div>
              </div>
            </div>
          )}

          {activeTab === "plan" && (
            <div className="bg-gray-950 border border-gray-900 rounded-2xl p-8 h-full overflow-y-auto">
              <h2 className="text-xl font-orbitron text-white mb-6">Current Mission Draft</h2>
              <div className="space-y-4">
                {[
                  { step: "01", task: "Initialize Hangar Environment", status: "complete" },
                  { step: "02", task: "Launch Stealth Browser via Playwright", status: "pending" },
                  { step: "03", task: "Execute Vision Reading for 'Current Weather'", status: "pending" },
                  { step: "04", task: "Deploy Native Desktop Control (Mousepad)", status: "pending" },
                  { step: "05", task: "Synchronize & Archive Flight Data", status: "pending" },
                ].map((s) => (
                  <div key={s.step} className="flex items-center gap-6 p-4 border border-gray-900 rounded-xl bg-black/20">
                    <span className="text-sky-500 font-mono text-lg">{s.step}</span>
                    <span className="flex-grow text-gray-400 text-sm">{s.task}</span>
                    {s.status === "complete" ? <CheckCircle className="w-5 h-5 text-green-500" /> : <div className="w-5 h-5 border border-gray-800 rounded-full" />}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === "recorder" && (
            <div className="flex-grow flex gap-4 h-full overflow-hidden">
              {/* List of Flights */}
              <div className="w-1/3 bg-gray-950 border border-gray-900 rounded-2xl overflow-y-auto p-2">
                {flights.length === 0 && <div className="text-center text-gray-600 text-xs p-4">No Data Recorded</div>}
                {flights.map(f => (
                  <button
                    key={f.flight_id}
                    onClick={() => setSelectedFlightId(f.flight_id)}
                    className={clsx(
                      "w-full text-left p-3 mb-2 rounded-lg text-xs font-mono transition-colors",
                      selectedFlightId === f.flight_id ? "bg-sky-500/20 text-sky-400 border border-sky-500/30" : "hover:bg-gray-900 text-gray-500"
                    )}
                  >
                    <div className="font-bold">{f.flight_id}</div>
                    <div className="opacity-60">{f.status}</div>
                  </button>
                ))}
              </div>

              {/* Flight Data Detail */}
              <div className="w-2/3 bg-black border border-gray-900 rounded-2xl p-4 overflow-hidden flex flex-col">
                <div className="flex items-center gap-2 text-sky-500 mb-4 font-orbitron border-b border-gray-900 pb-2">
                  <History className="w-4 h-4" /> BLACK BOX DATA
                </div>
                <div className="flex-grow overflow-y-auto space-y-2 custom-scrollbar">
                  {flightLogs.length === 0 && <div className="text-gray-700 text-xs">No logs found for this flight.</div>}
                  {flightLogs.map((log, i) => (
                    <div key={i} className="text-[10px] font-mono border-l-2 border-gray-800 pl-2 py-1">
                      <div className="text-xs text-gray-500 mb-0.5">{log.timestamp.split("T")[1].split(".")[0]} <span className={clsx("font-bold", log.type === "ERROR" ? "text-red-500" : "text-sky-600")}>[{log.type}]</span></div>
                      <div className="text-gray-300 whitespace-pre-wrap">{log.details}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      <style jsx global>{`
        .font-orbitron { font-family: var(--font-orbitron); }
        .scrollbar-hide::-webkit-scrollbar { display: none; }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #0c4a6e; border-radius: 10px; }
        @keyframes shimmer {
          100% { transform: translateX(100%); }
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
    </main>
  );
}
