import { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatMessageItem } from './components/ChatMessageItem';
import { ChatInput } from './components/ChatInput';
import { DocumentDrawer } from './components/DocumentDrawer';
import { ThinkingStatus } from './components/ThinkingStatus';
import type { ChatMessage, ChatSession, DocumentStats, HealthStatus, SourceItem, SearchMode } from './types';
import { Sparkles, FileText, Globe, Volume2 } from 'lucide-react';

export default function App() {
  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    try {
      const saved = localStorage.getItem('rag_assistant_sessions');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [activeSessionId, setActiveSessionId] = useState<string>(() => {
    try {
      const saved = localStorage.getItem('rag_assistant_active_id');
      return saved || '';
    } catch {
      return '';
    }
  });

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [liveStatus, setLiveStatus] = useState<string>('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [searchMode, setSearchMode] = useState<SearchMode>('auto');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Sync sessions to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('rag_assistant_sessions', JSON.stringify(sessions));
    } catch (e) {
      console.error('Error saving sessions to localStorage:', e);
    }
  }, [sessions]);

  useEffect(() => {
    try {
      localStorage.setItem('rag_assistant_active_id', activeSessionId);
    } catch (e) {
      console.error('Error saving active session ID:', e);
    }
  }, [activeSessionId]);

  // Load active session messages
  useEffect(() => {
    if (activeSessionId) {
      const active = sessions.find((s) => s.id === activeSessionId);
      if (active) {
        setMessages(active.messages);
      }
    } else if (sessions.length > 0) {
      setActiveSessionId(sessions[0].id);
      setMessages(sessions[0].messages);
    } else {
      setMessages([]);
    }
  }, [activeSessionId]);

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, liveStatus]);

  // Fetch initial system health & document stats
  const fetchStats = async () => {
    try {
      const res = await fetch('/api/documents/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (e) {
      console.error('Error fetching document stats:', e);
    }
  };

  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch (e) {
      console.error('Error fetching system health:', e);
    }
  };

  useEffect(() => {
    fetchHealth();
    fetchStats();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  // Session Handlers
  const handleNewSession = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: 'New Conversation',
      createdAt: new Date().toISOString(),
      messages: [],
    };
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
    setMessages([]);
  };

  const handleDeleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSessions((prev) => prev.filter((s) => s.id !== id));
    if (activeSessionId === id) {
      const remaining = sessions.filter((s) => s.id !== id);
      if (remaining.length > 0) {
        setActiveSessionId(remaining[0].id);
      } else {
        setActiveSessionId('');
        setMessages([]);
      }
    }
  };

  const handleClearChat = () => {
    if (messages.length === 0 || confirm('Clear this conversation?')) {
      setMessages([]);
      if (activeSessionId) {
        setSessions((prev) =>
          prev.map((s) => (s.id === activeSessionId ? { ...s, messages: [] } : s))
        );
      }
    }
  };

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
      setLiveStatus('');
    }
  };

  const handleSynthesizeVoice = async (text: string): Promise<string | undefined> => {
    try {
      const voiceRes = await fetch('/api/voice/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      if (voiceRes.ok) {
        const blob = await voiceRes.blob();
        return URL.createObjectURL(blob);
      }
    } catch (e) {
      console.error('Error synthesizing voice:', e);
    }
    return undefined;
  };

  const handleSendMessage = async (text: string, isVoice: boolean, forcedMode?: SearchMode) => {
    if (!text.trim() || isLoading) return;

    const activeMode = forcedMode || searchMode;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const assistantMsgId = (Date.now() + 1).toString();
    const initialAssistantMessage: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const nextMessages = [...messages, userMessage, initialAssistantMessage];
    setMessages(nextMessages);
    setIsLoading(true);
    setLiveStatus('Preparing request...');

    // If no active session, create one
    let currentId = activeSessionId;
    if (!currentId) {
      const newSession: ChatSession = {
        id: Date.now().toString(),
        title: text.slice(0, 32) + (text.length > 32 ? '...' : ''),
        createdAt: new Date().toISOString(),
        messages: nextMessages,
      };
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      currentId = newSession.id;
    } else {
      setSessions((prev) =>
        prev.map((s) =>
          s.id === currentId
            ? {
                ...s,
                title: s.title === 'New Conversation' ? text.slice(0, 32) : s.title,
                messages: nextMessages,
              }
            : s
        )
      );
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    let fullGeneratedContent = '';

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: text,
          chat_history: messages.map((m) => ({ role: m.role, content: m.content })),
          search_mode: activeMode,
        }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`Chat API error (HTTP ${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data:')) {
            const jsonStr = trimmed.replace('data:', '').trim();
            if (!jsonStr) continue;

            try {
              const eventData = JSON.parse(jsonStr);

              if (eventData.type === 'status') {
                setLiveStatus(eventData.message);
              } else if (eventData.type === 'sources') {
                setMessages((prev) => {
                  const updated = prev.map((m) =>
                    m.id === assistantMsgId
                      ? {
                          ...m,
                          source_type: eventData.source_type,
                          sources: eventData.sources as SourceItem[],
                        }
                      : m
                  );
                  return updated;
                });
              } else if (eventData.type === 'token') {
                setLiveStatus(''); // Clear thinking once streaming begins
                fullGeneratedContent += eventData.content;
                setMessages((prev) => {
                  const updated = prev.map((m) =>
                    m.id === assistantMsgId ? { ...m, content: m.content + eventData.content } : m
                  );
                  return updated;
                });
              } else if (eventData.type === 'done') {
                setLiveStatus('');
                break;
              }
            } catch (err) {
              console.error('SSE JSON parse error:', err);
            }
          }
        }
      }

      // Update session state in localStorage
      setSessions((prev) =>
        prev.map((s) =>
          s.id === currentId
            ? {
                ...s,
                messages: s.messages.map((m) =>
                  m.id === assistantMsgId ? { ...m, content: fullGeneratedContent } : m
                ),
              }
            : s
        )
      );

      // If Push-to-Talk voice used: auto-synthesize and play
      if (isVoice && fullGeneratedContent.trim()) {
        const voiceUrl = await handleSynthesizeVoice(fullGeneratedContent);
        if (voiceUrl) {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantMsgId ? { ...m, audioUrl: voiceUrl } : m))
          );
          const audio = new Audio(voiceUrl);
          audio.play().catch((e) => console.log('Audio autoplay policy:', e));
        }
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: `⚠️ **Error generating response:** ${error.message || 'Unknown network error'}. Please verify backend connection.`,
                }
              : m
          )
        );
      }
    } finally {
      setIsLoading(false);
      setLiveStatus('');
      abortControllerRef.current = null;
    }
  };

  const modelLabel = health?.llm_model || 'Local LLM';
  const hardwareLabel = health?.device_info?.device_name || 'Hardware Accelerated System';

  return (
    <div className="flex h-screen bg-[#07080c] text-slate-100 overflow-hidden font-sans selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Background Ambient Glow */}
      <div className="pointer-events-none fixed inset-0 z-0 bg-[radial-gradient(ellipse_80%_40%_at_50%_-10%,_var(--tw-gradient-stops))] from-indigo-900/15 via-transparent to-transparent" />

      {/* Collapsible Session Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        health={health}
        stats={stats}
      />

      {/* Main Chat Workspace */}
      <div className="flex-1 flex flex-col h-full z-10 relative overflow-hidden">
        {/* Top Header */}
        <Header
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          health={health}
          stats={stats}
          onOpenDrawer={() => setIsDrawerOpen(true)}
          onClearChat={handleClearChat}
        />

        {/* Messages Stream */}
        <main className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center p-6 text-center max-w-2xl mx-auto">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-600 flex items-center justify-center shadow-xl shadow-indigo-600/30 mb-5">
                <Sparkles className="w-7 h-7 text-white" />
              </div>

              <h2 className="text-2xl font-bold text-white mb-2 tracking-tight">
                Studio-Grade Local RAG & Voice AI
              </h2>
              <p className="text-sm text-slate-400 mb-8 max-w-md leading-relaxed">
                Powered by <span className="text-indigo-400 font-semibold">{modelLabel}</span> running on{' '}
                <span className="text-purple-400 font-semibold">{hardwareLabel}</span> with live web citations.
              </p>

              {/* Quick Starters */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full text-left">
                <button
                  onClick={() =>
                    handleSendMessage('What is Pokemon Fire Ash, and what is its latest release?', false, 'auto')
                  }
                  className="p-3.5 rounded-2xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.05] hover:border-indigo-500/30 transition group shadow-sm"
                >
                  <div className="flex items-center space-x-2 text-indigo-400 font-semibold text-xs mb-1">
                    <Sparkles className="w-4 h-4" />
                    <span>Pokemon Fire Ash</span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Test multi-turn conversational query reformulation & web search.
                  </p>
                </button>

                <button
                  onClick={() => setIsDrawerOpen(true)}
                  className="p-3.5 rounded-2xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.05] hover:border-cyan-500/30 transition group shadow-sm"
                >
                  <div className="flex items-center space-x-2 text-cyan-400 font-semibold text-xs mb-1">
                    <FileText className="w-4 h-4" />
                    <span>Document Analysis</span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Upload PDFs or TXT files to query them locally with ChromaDB.
                  </p>
                </button>

                <button
                  onClick={() => {
                    setSearchMode('web');
                    handleSendMessage('What is the current date and time today?', false, 'auto');
                  }}
                  className="p-3.5 rounded-2xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.05] hover:border-emerald-500/30 transition group shadow-sm"
                >
                  <div className="flex items-center space-x-2 text-emerald-400 font-semibold text-xs mb-1">
                    <Globe className="w-4 h-4" />
                    <span>Live Clock & Info</span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Zero hallucinations: grounded real-time system clock.
                  </p>
                </button>
              </div>

              <div className="mt-8 flex items-center space-x-4 text-xs text-slate-500 font-mono">
                <span className="flex items-center gap-1.5">
                  <Volume2 className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Push-to-Talk Voice</span>
                </span>
                <span>•</span>
                <span>Dual Chroma & Pinecone</span>
              </div>
            </div>
          ) : (
            <div className="divide-y divide-white/[0.02]">
              {messages.map((msg) => (
                <ChatMessageItem
                  key={msg.id}
                  message={msg}
                  onSynthesizeVoice={handleSynthesizeVoice}
                />
              ))}

              {/* Live Thinking Status */}
              {isLoading && liveStatus && (
                <div className="py-4 px-4 md:px-8">
                  <ThinkingStatus statusMessage={liveStatus} searchMode={searchMode} />
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </main>

        {/* Bottom Chat Input */}
        <ChatInput
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          onStopGeneration={handleStopGeneration}
          searchMode={searchMode}
          onSearchModeChange={setSearchMode}
          health={health}
        />

        {/* Slide-out Document Drawer */}
        <DocumentDrawer
          isOpen={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
          stats={stats}
          onRefreshStats={fetchStats}
        />
      </div>
    </div>
  );
}
