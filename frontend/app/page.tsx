"use client";

import { useState, useEffect, useRef } from "react";
import axios from "axios";
import {
  Plane, Terminal, Play, Power, Activity,
  Video, FileText, Monitor, CheckCircle, AlertTriangle,
  Send, User, Bot, Loader2, Rocket, History, HardDrive,
  Sparkles, ArrowRight, Clock, Target, Zap, RefreshCw,
  MessageSquare, ThumbsUp, HelpCircle, Lightbulb, Brain,
  Eye, MousePointer, Keyboard, ScrollText, Camera, Maximize2, Cloud, MousePointer2
} from "lucide-react";
import clsx from "clsx";

const API_URL = "/api";

type Message = {
  role: "user" | "attendant";
  text: string;
  intent?: string;
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

type PlanStep = {
  step: number;
  action: string;
  url?: string;
  selector?: string;
  instruction?: string;
  text?: string;
  key?: string;
  seconds?: number;
  command?: string;
};

type FlightPlan = {
  summary: string;
  plan: PlanStep[];
  error?: string;
};

type ReActStep = {
  step: number;
  observation: string;
  reasoning: string;
  action: string;
  params: Record<string, any>;
  screenshot?: string;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "attendant",
      text: "機長、おはようございます！✈️ 本日のフライトをサポートいたします。\n\n指示を入力すると、フライトプランを生成します。\nプランを確認後、**Take-off**ボタンでAIが自律的にミッションを実行します。\n\n例：「Amazonでイヤホンを探して」「Googleで天気を調べて」「YouTubeで猫の動画を探して」",
      intent: "greeting"
    }
  ]);
  const [input, setInput] = useState("");
  const [logs, setLogs] = useState<string>("");
  const [status, setStatus] = useState<"running" | "idle">("idle");
  const [activeTab, setActiveTab] = useState<"plan" | "react" | "viewport" | "recorder">("plan");
  const [isThinking, setIsThinking] = useState(false);

  // Flight Plan State (通常モード)
  const [currentPlan, setCurrentPlan] = useState<FlightPlan | null>(null);
  const [executingStep, setExecutingStep] = useState<number | null>(null);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);
  const [pendingGoal, setPendingGoal] = useState<string | null>(null);

  // ReAct State (自律モード)
  const [reactMode, setReactMode] = useState(false);
  const [reactSteps, setReactSteps] = useState<ReActStep[]>([]);
  const [reactRunning, setReactRunning] = useState(false);
  const [reactResult, setReactResult] = useState<any>(null);
  const [awaitingUser, setAwaitingUser] = useState(false);
  const [userQuestion, setUserQuestion] = useState<string | null>(null);
  const [interventionInput, setInterventionInput] = useState("");
  const [isResuming, setIsResuming] = useState(false);
  const [screenshot, setScreenshot] = useState<string | null>(null);

  // Recorder State
  const [flights, setFlights] = useState<Flight[]>([]);
  const [selectedFlightId, setSelectedFlightId] = useState<string | null>(null);
  const [flightLogs, setFlightLogs] = useState<LogEntry[]>([]);

  const logEndRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Polling Status & Logs & ReAct
  useEffect(() => {
    let lastStatus = "idle";
    const interval = setInterval(async () => {
      try {
        // Check normal status
        const statusRes = await axios.get(`${API_URL}/status`);
        const currentStatus = statusRes.data.status;
        if (statusRes.data.screenshot) {
          setScreenshot(statusRes.data.screenshot);
        }

        // Check ReAct status
        const reactRes = await axios.get(`${API_URL}/react/status`);
        setReactRunning(reactRes.data.running);
        setAwaitingUser(reactRes.data.awaiting_user || false);
        setUserQuestion(reactRes.data.question || null);

        // Get screenshot from ReAct status
        if (reactRes.data.screenshot) {
          setScreenshot(reactRes.data.screenshot);
        }

        if (reactRes.data.steps) {
          setReactSteps(reactRes.data.steps);
        }
        if (reactRes.data.result && !reactRes.data.running) {
          setReactResult(reactRes.data.result);
        }

        const isRunning = currentStatus === "running" || reactRes.data.running;
        setStatus(isRunning ? "running" : "idle");

        // Mission completed detection
        if (lastStatus === "running" && !isRunning) {
          fetchFlights();
          const resultMsg = reactRes.data.result
            ? `自律ミッション${reactRes.data.result.success ? "完了" : "終了"}！🎉 ${reactRes.data.result.final_result}`
            : "ミッション完了しました！🎉";
          setMessages(prev => [...prev, {
            role: "attendant",
            text: resultMsg + " Flight Recorderで詳細を確認できます。",
            intent: "complete"
          }]);
          setActiveTab("recorder");
          setExecutingStep(null);
        }
        lastStatus = isRunning ? "running" : "idle";

        const logsRes = await axios.get(`${API_URL}/logs`);
        setLogs(logsRes.data.logs);
      } catch (e) {
        console.error("API Polling Error", e);
      }
    }, 1500);
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
  }, [logs, reactSteps]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim() || isThinking || status === "running") return;

    const userMessage = input;
    const newMessages: Message[] = [...messages, { role: "user", text: userMessage }];
    setMessages(newMessages);
    setInput("");

    // Generate plan first, then await Take-off
    await handleNormalMode(userMessage, newMessages);
  };

  const handleNormalMode = async (userMessage: string, newMessages: Message[]) => {
    setIsThinking(true);
    try {
      const res = await axios.post(`${API_URL}/chat`, { message: userMessage });
      const result = res.data;

      setMessages([...newMessages, {
        role: "attendant",
        text: result.response,
        intent: result.intent
      }]);

      if (result.intent === "task" && result.plan) {
        setCurrentPlan(result.plan);
        setActiveTab("plan");
        setAwaitingConfirmation(true);
        setPendingGoal(userMessage); // Store the goal for ReAct execution
        setReactMode(false);
      } else if (result.intent === "confirmation" && result.execute_now && result.plan) {
        setCurrentPlan(result.plan);
        setPendingGoal(userMessage);
        // Start ReAct mode instead of executing the static plan
        await executeWithReAct(userMessage);
      }
    } catch (e: any) {
      setMessages([...newMessages, {
        role: "attendant",
        text: `システムエラーが発生しました: ${e.message}`,
        intent: "error"
      }]);
    } finally {
      setIsThinking(false);
    }
  };


  const handleResume = async () => {
    if (!interventionInput.trim()) return;
    setIsResuming(true);
    try {
      await axios.post(`${API_URL}/react/resume`, { response: interventionInput });
      setInterventionInput("");
      setAwaitingUser(false);
      setUserQuestion(null);
    } catch (e: any) {
      console.error("Resume Error", e);
    } finally {
      setIsResuming(false);
    }
  };

  const handleViewportClick = async (e: React.MouseEvent<HTMLImageElement>) => {
    // クリックを常に許可（AIがアクティブでない場合でもテスト可能）
    const rect = e.currentTarget.getBoundingClientRect();
    const x_offset = e.clientX - rect.left;
    const y_offset = e.clientY - rect.top;

    // 比率計算 (本来の解像度 1280x720 に合わせる)
    const x = Math.round((x_offset / rect.width) * 1280);
    const y = Math.round((y_offset / rect.height) * 720);

    console.log(`Remote click: (${x}, ${y})`);

    try {
      await axios.post(`${API_URL}/remote/click`, { x, y });
    } catch (err) {
      console.error("Remote Click Error", err);
    }
  };

  const executeCurrentPlan = async (plan: FlightPlan) => {
    try {
      await axios.post(`${API_URL}/execute`, {
        plan: plan.plan,
        summary: plan.summary
      });
      setActiveTab("viewport");
      setExecutingStep(1);
      setAwaitingConfirmation(false);
    } catch (e: any) {
      setMessages(prev => [...prev, {
        role: "attendant",
        text: `離陸に失敗しました: ${e.response?.data?.detail || e.message}`,
        intent: "error"
      }]);
    }
  };

  const executeWithReAct = async (goal: string) => {
    setReactMode(true);
    setReactSteps([]);
    setReactResult(null);
    setActiveTab("react");
    setAwaitingConfirmation(false);

    try {
      setMessages(prev => [...prev, {
        role: "attendant",
        text: `🧠 自律モードを起動します。ゴール：「${goal}」\n\nAIが画面を見ながらリアルタイムで判断・行動します。ReAct Monitorタブで進行状況を確認できます。`,
        intent: "executing"
      }]);

      await axios.post(`${API_URL}/react`, { goal, max_steps: 50 });
    } catch (e: any) {
      setMessages(prev => [...prev, {
        role: "attendant",
        text: `自律モードの起動に失敗しました: ${e.response?.data?.detail || e.message}`,
        intent: "error"
      }]);
    }
  };

  const handleTakeOff = async () => {
    if (!currentPlan || currentPlan.plan.length === 0 || !pendingGoal) return;

    setMessages(prev => [...prev, {
      role: "attendant",
      text: "了解！ミッションを開始します。シートベルトをお締めください。🚀",
      intent: "executing"
    }]);

    await executeWithReAct(pendingGoal);
  };

  const handleResetChat = async () => {
    try {
      await axios.post(`${API_URL}/chat/reset`);
      setMessages([{
        role: "attendant",
        text: "会話をリセットしました。新しいミッションについて話しましょう！\n\n指示を入力するとフライトプランが生成されます。",
        intent: "greeting"
      }]);
      setCurrentPlan(null);
      setAwaitingConfirmation(false);
      setPendingGoal(null);
      setReactMode(false);
      setReactSteps([]);
      setReactResult(null);
    } catch (e) {
      console.error(e);
    }
  };

  const getIntentIcon = (intent?: string) => {
    switch (intent) {
      case "task": return <Target className="w-3 h-3 text-sky-400" />;
      case "question": return <HelpCircle className="w-3 h-3 text-purple-400" />;
      case "clarification": return <Lightbulb className="w-3 h-3 text-yellow-400" />;
      case "confirmation": return <ThumbsUp className="w-3 h-3 text-green-400" />;
      case "complete": return <CheckCircle className="w-3 h-3 text-green-400" />;
      case "error": return <AlertTriangle className="w-3 h-3 text-red-400" />;
      default: return <MessageSquare className="w-3 h-3 text-gray-400" />;
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case "goto": return <Plane className="w-4 h-4 text-blue-400" />;
      case "click": return <MousePointer className="w-4 h-4 text-green-400" />;
      case "type": return <Keyboard className="w-4 h-4 text-yellow-400" />;
      case "key": return <Keyboard className="w-4 h-4 text-orange-400" />;
      case "scroll": return <ScrollText className="w-4 h-4 text-purple-400" />;
      case "read": return <Eye className="w-4 h-4 text-cyan-400" />;
      case "wait": return <Clock className="w-4 h-4 text-gray-400" />;
      case "done": return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "fail": return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default: return <Zap className="w-4 h-4 text-gray-400" />;
    }
  };

  const getActionDescription = (step: PlanStep) => {
    switch (step.action) {
      case "goto": return `Navigate to ${step.url}`;
      case "click": return `Click: ${step.instruction || step.selector}`;
      case "type": case "type_vision": return `Type: "${step.text}"`;
      case "key": return `Press: ${step.key}`;
      case "read": return `Read: ${step.instruction}`;
      case "wait": return `Wait ${step.seconds}s`;
      default: return step.action;
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
              <p className="text-[10px] text-sky-500 font-mono tracking-widest uppercase">AI Flight Assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleResetChat}
              className="p-2 text-gray-500 hover:text-gray-300 hover:bg-gray-800 rounded-lg transition-colors"
              title="Reset conversation"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <div className={clsx(
              "px-2 py-1 rounded text-[10px] font-mono flex items-center gap-1",
              status === "running"
                ? awaitingUser
                  ? "bg-amber-500/20 text-amber-400 border border-amber-500/50"
                  : reactRunning
                    ? "bg-purple-500/20 text-purple-400 border border-purple-500/50"
                    : "bg-green-500/20 text-green-400 border border-green-500/50"
                : "bg-gray-800 text-gray-500"
            )}>
              {(reactRunning || awaitingUser) && <Brain className={clsx("w-3 h-3", awaitingUser ? "text-amber-400" : "animate-pulse")} />}
              {status === "running" ? (awaitingUser ? "AWAITING INTERVENTION" : reactRunning ? "AUTONOMOUS" : "RUNNING") : "IDLE"}
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-grow overflow-y-auto p-6 space-y-4 scrollbar-hide">
          {messages.map((m, i) => (
            <div key={i} className={clsx("flex flex-col", m.role === "user" ? "items-end" : "items-start")}>
              {m.role === "attendant" && (
                <div className="flex items-center gap-1 mb-1 ml-1">
                  {getIntentIcon(m.intent)}
                  <span className="text-[10px] text-gray-500 uppercase">{m.intent || "message"}</span>
                </div>
              )}
              <div className={clsx(
                "max-w-[85%] p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap",
                m.role === "user"
                  ? "bg-sky-600 text-white rounded-tr-none"
                  : "bg-gray-900 text-gray-300 rounded-tl-none border border-gray-800"
              )}>
                {m.text}
              </div>
            </div>
          ))}
          {isThinking && (
            <div className="flex items-start">
              <div className="flex items-center gap-2 text-sky-500 text-xs font-mono bg-gray-900 border border-gray-800 rounded-2xl rounded-tl-none p-4">
                <Sparkles className="w-4 h-4 animate-pulse" />
                <span className="animate-pulse">Attendant is thinking...</span>
              </div>
            </div>
          )}

          {awaitingUser && (
            <div className="flex flex-col items-start gap-2 p-4 bg-amber-950/20 border border-amber-500/30 rounded-2xl rounded-tl-none">
              <div className="flex items-center gap-2 text-amber-400 text-xs font-bold font-orbitron">
                <AlertTriangle className="w-4 h-4" />
                HUMAN INTERVENTION REQUIRED
              </div>
              <p className="text-sm text-gray-300 italic">"{userQuestion}"</p>

              <div className="w-full flex gap-2 mt-2">
                <input
                  type="text"
                  value={interventionInput}
                  onChange={(e) => setInterventionInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleResume()}
                  placeholder="回答を入力して再開..."
                  className="flex-grow bg-amber-950/30 border border-amber-500/30 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
                />
                <button
                  onClick={handleResume}
                  disabled={isResuming || !interventionInput.trim()}
                  className="bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-1 transition-colors"
                >
                  {isResuming ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                  RESUME
                </button>
              </div>
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
              placeholder="指示を入力してください（プラン生成 → Take-offで実行）"
              className="w-full bg-gray-900 border border-gray-800 rounded-xl py-4 pl-4 pr-12 text-sm focus:outline-none focus:border-sky-500 transition-colors"
              disabled={isThinking || status === "running"}
            />
            <button
              onClick={handleSendMessage}
              disabled={isThinking || status === "running"}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-sky-500 hover:text-sky-400 p-2 disabled:opacity-50"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>

          <button
            onClick={handleTakeOff}
            disabled={status === "running" || !currentPlan || currentPlan.plan.length === 0 || reactMode}
            className={clsx(
              "w-full py-5 rounded-xl font-orbitron tracking-[0.2em] relative overflow-hidden group transition-all duration-500",
              status === "running" || !currentPlan || currentPlan.plan.length === 0 || reactMode
                ? "bg-gray-800 text-gray-600 cursor-not-allowed"
                : awaitingConfirmation
                  ? "bg-green-600 hover:bg-green-500 text-white shadow-[0_0_30px_rgba(34,197,94,0.3)] animate-pulse"
                  : "bg-sky-600 hover:bg-sky-500 text-white shadow-[0_0_30px_rgba(14,165,233,0.3)]"
            )}
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:animate-shimmer" />
            <div className="flex items-center justify-center gap-3">
              <Rocket className={clsx("w-5 h-5", currentPlan && !reactMode && "group-hover:-translate-y-1 transition-transform")} />
              {reactMode ? "USE NORMAL MODE" : awaitingConfirmation ? "CONFIRM & TAKE-OFF" : "TAKE-OFF"}
            </div>
          </button>

          {awaitingConfirmation && !reactMode && (
            <p className="text-center text-xs text-green-400 mt-2 animate-pulse">
              プランを確認して、ボタンを押すか「OK」と言ってください
            </p>
          )}
        </div>
      </section>

      {/* RIGHT: DASHBOARD (1/2) */}
      <section className="w-1/2 min-w-0 flex flex-col bg-black">
        {/* Top Navigation Tab */}
        <nav className="flex p-4 gap-2 border-b border-gray-900 bg-gray-950/20">
          {[
            { id: "plan", label: "Mission Plan", icon: Target },
            { id: "react", label: "ReAct Monitor", icon: Brain },
            { id: "viewport", label: "Viewport", icon: Monitor },
            { id: "recorder", label: "Flight Recorder", icon: HardDrive },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={clsx(
                "flex items-center gap-2 px-4 py-2 rounded-full text-xs font-orbitron transition-all",
                activeTab === tab.id
                  ? tab.id === "react" && reactRunning
                    ? "bg-purple-500/20 text-purple-400 border border-purple-500/50"
                    : "bg-sky-500/10 text-sky-400 border border-sky-500/30"
                  : "text-gray-500 hover:text-gray-300"
              )}
            >
              <tab.icon className={clsx("w-3 h-3", tab.id === "react" && reactRunning && "animate-pulse")} />
              {tab.label}
              {tab.id === "react" && reactRunning && (
                <span className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" />
              )}
            </button>
          ))}
        </nav>

        {/* Dashboard Content */}
        <div className="flex-grow p-6 overflow-hidden flex flex-col">

          {/* MISSION PLAN TAB */}
          {activeTab === "plan" && (
            <div className="flex-grow flex flex-col gap-4 overflow-hidden">
              <div className={clsx(
                "border rounded-2xl p-5 transition-all",
                awaitingConfirmation
                  ? "bg-gradient-to-r from-green-500/10 to-emerald-500/10 border-green-500/30"
                  : "bg-gradient-to-r from-sky-500/10 to-purple-500/10 border-sky-500/20"
              )}>
                <div className="flex items-center gap-3 mb-2">
                  <Sparkles className={clsx("w-5 h-5", awaitingConfirmation ? "text-green-400" : "text-sky-400")} />
                  <h2 className="text-lg font-orbitron text-white">
                    {awaitingConfirmation ? "Ready for Takeoff" : "Mission Plan"}
                  </h2>
                </div>
                <p className="text-sm text-gray-400">
                  {currentPlan?.summary || "Attendantに指示すると、フライトプランが生成されます。"}
                </p>
              </div>

              <div className="flex-grow overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                {(!currentPlan || currentPlan.plan.length === 0) ? (
                  <div className="flex flex-col items-center justify-center h-full text-gray-600">
                    <FileText className="w-12 h-12 opacity-20 mb-3" />
                    <p className="text-sm">No flight plan yet</p>
                  </div>
                ) : (
                  currentPlan.plan.map((s, i) => (
                    <div
                      key={i}
                      className={clsx(
                        "p-4 rounded-xl border flex items-center gap-4 transition-all",
                        executingStep === s.step
                          ? "bg-sky-500/10 border-sky-500/50 shadow-[0_0_15px_rgba(14,165,233,0.2)]"
                          : "bg-gray-950 border-gray-900 group hover:border-gray-700"
                      )}
                    >
                      <div className={clsx(
                        "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0",
                        executingStep === s.step ? "bg-sky-500 text-white animate-pulse" : "bg-gray-900 text-gray-500"
                      )}>
                        {s.step}
                      </div>
                      <div className="flex-grow">
                        <div className="flex items-center gap-2">
                          <div className="text-[10px] font-mono text-sky-500 uppercase tracking-widest">{s.action}</div>
                          {executingStep === s.step && <div className="text-[10px] text-sky-400 bg-sky-400/10 px-2 rounded animate-pulse">EXECUTING</div>}
                        </div>
                        <div className="text-sm text-gray-200 mt-0.5">{s.instruction}</div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* REACT MONITOR TAB */}
          {activeTab === "react" && (
            <div className="flex-grow flex flex-col gap-4 overflow-hidden">
              <div className={clsx(
                "border rounded-2xl p-5",
                awaitingUser
                  ? "bg-gradient-to-r from-amber-500/10 to-orange-500/10 border-amber-500/30 shadow-[0_0_20px_rgba(245,158,11,0.1)]"
                  : reactRunning
                    ? "bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/30"
                    : "bg-gradient-to-r from-gray-800/50 to-gray-900/50 border-gray-700"
              )}>
                <div className="flex items-center gap-3 mb-2">
                  <Brain className={clsx("w-5 h-5", awaitingUser ? "text-amber-400" : reactRunning ? "text-purple-400 animate-pulse" : "text-gray-400")} />
                  <h2 className="text-lg font-orbitron text-white">
                    {awaitingUser ? "Waiting for Pilot" : "ReAct Autonomous Agent"}
                  </h2>
                  {reactRunning && !awaitingUser && <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />}
                </div>
                <p className="text-sm text-gray-400">
                  {awaitingUser
                    ? "AIが困難に直面し、あなたの介入を求めています。左のチャットエリアから回答してください。"
                    : reactRunning
                      ? "AIが画面を観察し、リアルタイムで次のアクションを決定しています..."
                      : reactResult
                        ? `完了: ${reactResult.final_result}`
                        : "プランを確認後、Take-offボタンを押すとAIが動的に判断・行動します。"
                  }
                </p>
              </div>

              <div className="flex-grow overflow-y-auto space-y-3 pr-2 custom-scrollbar">
                {reactSteps.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-gray-600">
                    <Brain className="w-12 h-12 opacity-20 mb-3" />
                    <p className="text-sm">No ReAct steps yet</p>
                    <p className="text-xs opacity-60 mt-1">指示入力後、Take-offボタンを押すと始まります</p>
                  </div>
                ) : (
                  reactSteps.map((step, i) => (
                    <div key={i} className="bg-gray-950 border border-gray-900 rounded-xl overflow-hidden animate-in fade-in slide-in-from-top duration-500">
                      <div className="flex items-center justify-between px-4 py-2 bg-gray-900/50 border-b border-gray-900">
                        <div className="flex items-center gap-3">
                          <span className="text-[10px] font-mono text-gray-500">STEP {step.step}</span>
                          <span className="px-2 py-0.5 bg-purple-500/10 text-purple-400 text-[10px] font-mono rounded border border-purple-500/20">{step.action.toUpperCase()}</span>
                        </div>
                      </div>
                      <div className="p-4 space-y-3">
                        <div className="flex gap-4">
                          {step.screenshot && (
                            <div className="w-48 aspect-video shrink-0 bg-black rounded-lg border border-gray-800 overflow-hidden relative group">
                              <img src={step.screenshot} alt={`Step ${step.step}`} className="w-full h-full object-contain" />
                              <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                                <Maximize2 className="w-4 h-4 text-white" />
                              </div>
                            </div>
                          )}
                          <div className="flex-grow space-y-2">
                            <div className="flex items-start gap-2">
                              <Eye className="w-3 h-3 text-purple-400 mt-1 shrink-0" />
                              <p className="text-xs text-gray-400 leading-relaxed">{step.observation}</p>
                            </div>
                            <div className="flex items-start gap-2">
                              <Lightbulb className="w-3 h-3 text-amber-400 mt-1 shrink-0" />
                              <p className="text-[11px] text-gray-300 leading-relaxed italic">{step.reasoning}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
                <div ref={logEndRef} />
              </div>

              {reactResult && (
                <div className={clsx(
                  "p-4 rounded-xl border",
                  reactResult.success ? "bg-green-500/10 border-green-500/30" : "bg-red-500/10 border-red-500/30"
                )}>
                  <div className="flex items-center gap-2">
                    {reactResult.success ? <CheckCircle className="w-5 h-5 text-green-500" /> : <AlertTriangle className="w-5 h-5 text-red-500" />}
                    <span className="font-orbitron">{reactResult.success ? "SUCCESS" : "FAILED"}</span>
                  </div>
                  <p className="text-sm text-gray-400 mt-2">{reactResult.final_result}</p>
                  <p className="text-xs text-gray-600 mt-1">Steps taken: {reactResult.steps_taken}</p>
                </div>
              )}
            </div>
          )}

          {/* VIEWPORT TAB - noVNC Embedded */}
          {activeTab === "viewport" && (
            <div className="flex-grow flex flex-col p-4 bg-black/50 rounded-2xl border border-gray-800 relative overflow-hidden">
              <div className="flex items-center justify-between mb-4">
                <div className="flex gap-2">
                  <div className="px-3 py-1 bg-black/80 border border-red-500/50 rounded-full flex items-center gap-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                    <span className="text-[10px] font-mono text-red-500 font-bold uppercase tracking-widest">Live VNC</span>
                  </div>
                  {awaitingUser && (
                    <div className="px-3 py-1 bg-amber-500/80 border border-amber-400 rounded-full flex items-center gap-2 animate-bounce">
                      <MousePointer2 className="w-3 h-3 text-white" />
                      <span className="text-[10px] font-bold text-white uppercase">Intervention Mode</span>
                    </div>
                  )}
                </div>
                <div className="flex gap-2 text-[10px] font-mono text-gray-500 uppercase">
                  <span>🖥️ Direct Control</span>
                  <span>•</span>
                  <span>1280×720</span>
                </div>
              </div>

              <div className="flex-grow relative bg-black rounded-xl overflow-hidden shadow-2xl border border-white/5">
                <iframe
                  src="/vnc/vnc.html?autoconnect=true&resize=scale&quality=6&compression=2"
                  className="w-full h-full border-0"
                  allow="clipboard-read; clipboard-write"
                  title="VNC Viewer"
                />
              </div>

              <div className="mt-3 text-center text-[10px] font-mono text-gray-600">
                💡 VNCが表示されない場合は <a href="http://localhost:6080/vnc.html" target="_blank" className="text-sky-500 hover:underline">こちら</a> を別タブで開いてください
              </div>
            </div>
          )}

          {/* FLIGHT RECORDER TAB */}
          {activeTab === "recorder" && (
            <div className="flex-grow flex gap-4 h-full overflow-hidden">
              <div className="w-1/3 bg-gray-950 border border-gray-900 rounded-2xl overflow-y-auto p-2">
                {flights.length === 0 && <div className="text-center text-gray-600 text-xs p-4">No Data</div>}
                {flights.map(f => (
                  <button
                    key={f.flight_id}
                    onClick={() => setSelectedFlightId(f.flight_id)}
                    className={clsx(
                      "w-full text-left p-2 mb-1 rounded-lg text-xs font-mono transition-colors",
                      selectedFlightId === f.flight_id ? "bg-sky-500/20 text-sky-400 border border-sky-500/30" : "hover:bg-gray-900 text-gray-500"
                    )}
                  >
                    <div className="font-bold truncate">{f.flight_id}</div>
                    <div className="opacity-60 text-[10px]">{f.status}</div>
                  </button>
                ))}
              </div>

              <div className="w-2/3 bg-black border border-gray-900 rounded-2xl p-3 overflow-hidden flex flex-col">
                <div className="flex items-center gap-2 text-sky-500 mb-3 font-orbitron text-sm border-b border-gray-900 pb-2">
                  <History className="w-4 h-4" /> BLACK BOX
                </div>
                <div className="flex-grow overflow-y-auto space-y-1 custom-scrollbar">
                  {flightLogs.length === 0 && <div className="text-gray-700 text-xs">No logs</div>}
                  {flightLogs.map((log, i) => (
                    <div key={i} className="text-[10px] font-mono border-l-2 border-gray-800 pl-2 py-0.5">
                      <span className="text-gray-600">{log.timestamp.split("T")[1]?.split(".")[0]}</span>
                      <span className={clsx(
                        "font-bold ml-1",
                        log.type === "ERROR" ? "text-red-500" : log.type === "REACT" ? "text-purple-500" : "text-sky-600"
                      )}>[{log.type}]</span>
                      <span className="text-gray-400 ml-1">{log.details.substring(0, 100)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          {/* TELEMETRY Area (optional, removed duplicate live tab content) */}
          <pre className="whitespace-pre-wrap">{logs || "> Awaiting mission..."}</pre>
        </div>
      </section>

      <style jsx global>{`
        .font-orbitron { font-family: var(--font-orbitron); }
        .scrollbar-hide::-webkit-scrollbar { display: none; }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #0c4a6e; border-radius: 10px; }
        @keyframes shimmer { 100% { transform: translateX(100%); } }
        .animate-shimmer { animation: shimmer 2s infinite; }
      `}</style>
    </main>
  );
}
