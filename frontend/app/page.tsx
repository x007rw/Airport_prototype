"use client";

import { useState, useEffect, useRef } from "react";
import axios from "axios";
import {
  Plane, Terminal, Play, Power, Activity,
  Video, FileText, Monitor, CheckCircle, AlertTriangle,
  Send, User, Bot, Loader2, Rocket, History, HardDrive,
  Sparkles, ArrowRight, Clock, Target, Zap, RefreshCw,
  MessageSquare, ThumbsUp, HelpCircle, Lightbulb, Brain,
  Eye, MousePointer, Keyboard, ScrollText
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
      text: "機長、おはようございます！✈️ 本日のフライトをサポートいたします。\n\nどのようなミッションをご希望ですか？\n\n🚀 **通常モード**: 事前にプランを確認してから実行\n🧠 **自律モード**: AIが状況を見ながら動的に判断\n\n例：「東京の天気を調べて」「自律モードでAmazonでイヤホンを探して」",
      intent: "greeting"
    }
  ]);
  const [input, setInput] = useState("");
  const [logs, setLogs] = useState<string>("");
  const [status, setStatus] = useState<"running" | "idle">("idle");
  const [activeTab, setActiveTab] = useState<"plan" | "react" | "live" | "recorder">("plan");
  const [isThinking, setIsThinking] = useState(false);

  // Flight Plan State (通常モード)
  const [currentPlan, setCurrentPlan] = useState<FlightPlan | null>(null);
  const [executingStep, setExecutingStep] = useState<number | null>(null);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);

  // ReAct State (自律モード)
  const [reactMode, setReactMode] = useState(false);
  const [reactSteps, setReactSteps] = useState<ReActStep[]>([]);
  const [reactRunning, setReactRunning] = useState(false);
  const [reactResult, setReactResult] = useState<any>(null);

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

        // Check ReAct status
        const reactRes = await axios.get(`${API_URL}/react/status`);
        setReactRunning(reactRes.data.running);
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

    // Check if user wants ReAct mode
    const isReactRequest = userMessage.toLowerCase().includes("自律") ||
      userMessage.toLowerCase().includes("react") ||
      userMessage.toLowerCase().includes("autonomous");

    if (isReactRequest) {
      // ReAct mode
      await startReActMode(userMessage.replace(/自律モードで|自律で|reactで/gi, "").trim(), newMessages);
    } else {
      // Normal mode - use Attendant
      await handleNormalMode(userMessage, newMessages);
    }
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
        setReactMode(false);
      } else if (result.intent === "confirmation" && result.execute_now && result.plan) {
        setCurrentPlan(result.plan);
        await executeCurrentPlan(result.plan);
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

  const startReActMode = async (goal: string, newMessages: Message[]) => {
    setIsThinking(true);
    setReactMode(true);
    setReactSteps([]);
    setReactResult(null);
    setActiveTab("react");

    try {
      setMessages([...newMessages, {
        role: "attendant",
        text: `🧠 自律モードを起動します。ゴール：「${goal}」\n\nAIが画面を見ながらリアルタイムで判断・行動します。ReAct Monitorタブで進行状況を確認できます。`,
        intent: "task"
      }]);

      await axios.post(`${API_URL}/react`, { goal, max_steps: 15 });
    } catch (e: any) {
      setMessages([...newMessages, {
        role: "attendant",
        text: `自律モードの起動に失敗しました: ${e.response?.data?.detail || e.message}`,
        intent: "error"
      }]);
    } finally {
      setIsThinking(false);
    }
  };

  const executeCurrentPlan = async (plan: FlightPlan) => {
    try {
      await axios.post(`${API_URL}/execute`, {
        plan: plan.plan,
        summary: plan.summary
      });
      setActiveTab("live");
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

  const handleTakeOff = async () => {
    if (!currentPlan || currentPlan.plan.length === 0) return;

    setMessages(prev => [...prev, {
      role: "attendant",
      text: "了解！ミッションを開始します。シートベルトをお締めください。🚀",
      intent: "executing"
    }]);

    await executeCurrentPlan(currentPlan);
  };

  const handleResetChat = async () => {
    try {
      await axios.post(`${API_URL}/chat/reset`);
      setMessages([{
        role: "attendant",
        text: "会話をリセットしました。新しいミッションについて話しましょう！\n\n🚀 通常モード or 🧠 自律モード どちらでも対応できます。",
        intent: "greeting"
      }]);
      setCurrentPlan(null);
      setAwaitingConfirmation(false);
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
                ? reactRunning
                  ? "bg-purple-500/20 text-purple-400 border border-purple-500/50"
                  : "bg-green-500/20 text-green-400 border border-green-500/50"
                : "bg-gray-800 text-gray-500"
            )}>
              {reactRunning && <Brain className="w-3 h-3 animate-pulse" />}
              {status === "running" ? (reactRunning ? "AUTONOMOUS" : "RUNNING") : "IDLE"}
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
              placeholder="自然に話しかけてください... (「自律モードで」で自律実行)"
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
            { id: "live", label: "Live Viewport", icon: Monitor },
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
                  currentPlan.plan.map((step, idx) => (
                    <div
                      key={idx}
                      className={clsx(
                        "flex items-center gap-3 p-3 rounded-xl border transition-all",
                        executingStep === step.step ? "bg-sky-500/20 border-sky-500/50" : "bg-gray-950 border-gray-800"
                      )}
                    >
                      <div className={clsx(
                        "w-8 h-8 rounded-full flex items-center justify-center text-xs font-mono font-bold",
                        executingStep === step.step ? "bg-sky-500 text-white animate-pulse" : "bg-gray-800 text-gray-400"
                      )}>
                        {step.step.toString().padStart(2, '0')}
                      </div>
                      {getActionIcon(step.action)}
                      <div className="flex-grow">
                        <span className="text-xs font-mono text-sky-400 uppercase">{step.action}</span>
                        <p className="text-xs text-gray-400 truncate">{getActionDescription(step)}</p>
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
                reactRunning
                  ? "bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/30"
                  : "bg-gradient-to-r from-gray-800/50 to-gray-900/50 border-gray-700"
              )}>
                <div className="flex items-center gap-3 mb-2">
                  <Brain className={clsx("w-5 h-5", reactRunning ? "text-purple-400 animate-pulse" : "text-gray-400")} />
                  <h2 className="text-lg font-orbitron text-white">ReAct Autonomous Agent</h2>
                  {reactRunning && <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />}
                </div>
                <p className="text-sm text-gray-400">
                  {reactRunning
                    ? "AIが画面を観察し、リアルタイムで次のアクションを決定しています..."
                    : reactResult
                      ? `完了: ${reactResult.final_result}`
                      : "「自律モードで〇〇して」と指示すると、AIが動的に判断・行動します。"
                  }
                </p>
              </div>

              <div className="flex-grow overflow-y-auto space-y-3 pr-2 custom-scrollbar">
                {reactSteps.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-gray-600">
                    <Brain className="w-12 h-12 opacity-20 mb-3" />
                    <p className="text-sm">No ReAct steps yet</p>
                    <p className="text-xs opacity-60 mt-1">「自律モードでAmazonでイヤホンを探して」のように指示</p>
                  </div>
                ) : (
                  reactSteps.map((step, idx) => (
                    <div
                      key={idx}
                      className={clsx(
                        "p-4 rounded-xl border transition-all",
                        idx === reactSteps.length - 1 && reactRunning
                          ? "bg-purple-500/10 border-purple-500/50 shadow-[0_0_20px_rgba(168,85,247,0.2)]"
                          : step.action === "done"
                            ? "bg-green-500/10 border-green-500/30"
                            : step.action === "fail"
                              ? "bg-red-500/10 border-red-500/30"
                              : "bg-gray-950 border-gray-800"
                      )}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className={clsx(
                          "w-6 h-6 rounded-full flex items-center justify-center text-xs font-mono font-bold",
                          idx === reactSteps.length - 1 && reactRunning
                            ? "bg-purple-500 text-white animate-pulse"
                            : "bg-gray-800 text-gray-400"
                        )}>
                          {step.step}
                        </div>
                        {getActionIcon(step.action)}
                        <span className="text-xs font-mono text-purple-400 uppercase">{step.action}</span>
                        {idx === reactSteps.length - 1 && reactRunning && (
                          <Loader2 className="w-3 h-3 text-purple-400 animate-spin ml-auto" />
                        )}
                      </div>

                      <div className="space-y-1 text-xs">
                        <div className="flex gap-2">
                          <Eye className="w-3 h-3 text-cyan-400 mt-0.5 flex-shrink-0" />
                          <p className="text-gray-400">{step.observation}</p>
                        </div>
                        <div className="flex gap-2">
                          <Lightbulb className="w-3 h-3 text-yellow-400 mt-0.5 flex-shrink-0" />
                          <p className="text-gray-500">{step.reasoning}</p>
                        </div>
                        {Object.keys(step.params).length > 0 && (
                          <div className="flex gap-2">
                            <Zap className="w-3 h-3 text-orange-400 mt-0.5 flex-shrink-0" />
                            <code className="text-gray-600 text-[10px]">{JSON.stringify(step.params)}</code>
                          </div>
                        )}
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

          {/* LIVE VIEWPORT TAB */}
          {activeTab === "live" && (
            <div className="flex-grow flex flex-col gap-4">
              <div className="flex-grow bg-gray-950 border border-gray-900 rounded-2xl relative overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center text-gray-800 flex-col gap-4">
                  <Monitor className="w-12 h-12 opacity-10" />
                  <p className="text-xs uppercase tracking-[0.2em] opacity-40 font-orbitron">Live stream coming soon</p>
                </div>
                <div className="absolute top-3 left-3 flex gap-2">
                  <div className={clsx(
                    "px-2 py-1 border rounded text-[10px] flex items-center gap-1",
                    status === "running" ? "bg-red-500/20 border-red-500/50 text-red-400 animate-pulse" : "bg-gray-800 border-gray-700 text-gray-500"
                  )}>
                    <div className={clsx("w-1.5 h-1.5 rounded-full", status === "running" ? "bg-red-500" : "bg-gray-600")} />
                    {status === "running" ? "LIVE" : "STANDBY"}
                  </div>
                </div>
              </div>

              <div className="h-1/3 bg-black border border-gray-900 rounded-2xl p-4 font-mono text-[10px] overflow-hidden flex flex-col">
                <div className="flex items-center gap-2 text-sky-900 mb-3 font-bold border-b border-gray-900 pb-2">
                  <Terminal className="w-3 h-3" />
                  TELEMETRY
                </div>
                <div className="flex-grow overflow-y-auto text-sky-400/80 custom-scrollbar">
                  <pre className="whitespace-pre-wrap">{logs || "> Awaiting mission..."}</pre>
                </div>
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
