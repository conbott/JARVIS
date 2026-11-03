import { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatMessageItem } from './components/ChatMessageItem';
import { ChatInput } from './components/ChatInput';
import { DocumentDrawer } from './components/DocumentDrawer';
import { SystemPanel } from './components/SystemPanel';
import { ThinkingStatus } from './components/ThinkingStatus';
import type {
  ChatMessage,
  ChatSession,
  DocumentStats,
  HealthStatus,
  SourceItem,
  SearchMode,
  VoiceOption,
} from './types';
import { UploadCloud, ArrowUpRight, Sparkles, FileText, Globe } from 'lucide-react';

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL
  ? (import.meta as any).env.VITE_API_BASE_URL.replace(/\/$/, '')
  : '';

const getSessionId = (): string => {
  try {
    let sid = localStorage.getItem('rag_assistant_user_session_id');
    if (!sid) {
      sid = 'sess_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
      localStorage.setItem('rag_assistant_user_session_id', sid);
    }
    return sid;
  } catch {
    return 'default';
  }
};

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
  const [isSystemOpen, setIsSystemOpen] = useState(false);
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [searchMode, setSearchMode] = useState<SearchMode>('auto');

  // Voice & Audio Playback State
  const [availableVoices, setAvailableVoices] = useState<VoiceOption[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<string>(() => {
    return localStorage.getItem('rag_assistant_voice') || 'en-US-GuyNeural';
  });
  const [playingMessageId, setPlayingMessageId] = useState<string | null>(null);
  const [synthesizingMessageId, setSynthesizingMessageId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const audioInstanceRef = useRef<HTMLAudioElement | null>(null);

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

  // Auto-scroll to bottom of conversation
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, liveStatus]);

  // Fetch system health & document stats on initial mount
  useEffect(() => {
    fetchHealth();
    fetchStats();
    fetchVoices();
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/health`, {
        headers: { 'X-Session-Id': getSessionId() },
      });
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch (err) {
      console.error('Failed to fetch system health:', err);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/documents/stats`, {
        headers: { 'X-Session-Id': getSessionId() },
      });
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch document stats:', err);
    }
  };

  const fetchVoices = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/voice/voices`, {
        headers: { 'X-Session-Id': getSessionId() },
      });
      if (res.ok) {
        const data = await res.json();
        setAvailableVoices(data.voices || []);
      }
    } catch (err) {
      console.error('Failed to fetch voices:', err);
    }
  };

  const handleSelectVoice = (voiceId: string) => {
    setSelectedVoice(voiceId);
    localStorage.setItem('rag_assistant_voice', voiceId);
  };

  const stopActiveAudio = () => {
    if (audioInstanceRef.current) {
      audioInstanceRef.current.pause();
      audioInstanceRef.current.currentTime = 0;
      audioInstanceRef.current = null;
    }
    setPlayingMessageId(null);
  };

  const handleSynthesizeVoice = async (text: string, voice?: string): Promise<string | undefined> => {
    try {
      const voiceRes = await fetch(`${API_BASE}/api/voice/synthesize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Id': getSessionId(),
        },
        body: JSON.stringify({ text, voice: voice || selectedVoice }),
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

  const handleTogglePlayAudio = async (messageId: string, text: string) => {
    if (playingMessageId === messageId) {
      stopActiveAudio();
      return;
    }

    stopActiveAudio();

    const targetMsg = messages.find((m) => m.id === messageId);
    let url = targetMsg?.audioUrl;

    if (!url) {
      setSynthesizingMessageId(messageId);
      url = await handleSynthesizeVoice(text, selectedVoice);
      setSynthesizingMessageId(null);

      if (url) {
        setMessages((prev) =>
          prev.map((m) => (m.id === messageId ? { ...m, audioUrl: url } : m))
        );
      }
    }

    if (url) {
      const audio = new Audio(url);
      audioInstanceRef.current = audio;
      setPlayingMessageId(messageId);

      audio.onended = () => {
        if (audioInstanceRef.current === audio) {
          setPlayingMessageId(null);
          audioInstanceRef.current = null;
        }
      };

      audio.onerror = () => {
        if (audioInstanceRef.current === audio) {
          setPlayingMessageId(null);
          audioInstanceRef.current = null;
        }
      };

      audio.play().catch((err) => {
        console.error('Audio playback error:', err);
        setPlayingMessageId(null);
      });
    }
  };

  // Session Handlers
  const handleNewSession = () => {
    stopActiveAudio();
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: 'New conversation',
      createdAt: new Date().toISOString(),
      messages: [],
    };
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
    setMessages([]);
  };

  const handleDeleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    stopActiveAudio();
    const filtered = sessions.filter((s) => s.id !== id);
    setSessions(filtered);
    if (activeSessionId === id) {
      if (filtered.length > 0) {
        setActiveSessionId(filtered[0].id);
        setMessages(filtered[0].messages);
      } else {
        setActiveSessionId('');
        setMessages([]);
      }
    }
  };

  const handleClearChat = () => {
    stopActiveAudio();
    setMessages([]);
    if (activeSessionId) {
      setSessions((prev) =>
        prev.map((s) => (s.id === activeSessionId ? { ...s, messages: [] } : s))
      );
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

  const handleSendMessage = async (text: string, isVoice: boolean, forcedMode?: SearchMode) => {
    if (!text.trim() || isLoading) return;

    stopActiveAudio();

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
    setLiveStatus('Thinking...');

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
                title: s.title === 'New conversation' ? text.slice(0, 32) : s.title,
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
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Id': getSessionId(),
        },
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
                          path: eventData.path,
                          retrieval: eventData.retrieval,
                          fallback_reason: eventData.fallback_reason,
                          best_score: eventData.best_score,
                          threshold: eventData.threshold,
                          sources: eventData.sources as SourceItem[],
                        }
                      : m
                  );
                  return updated;
                });
              } else if (eventData.type === 'token') {
                setLiveStatus('');
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

      // RULE 1: If message was sent via push-to-talk mic (isVoice = true), auto-play assistant's reply
      if (isVoice && fullGeneratedContent.trim()) {
        stopActiveAudio();
        const voiceUrl = await handleSynthesizeVoice(fullGeneratedContent, selectedVoice);
        if (voiceUrl) {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantMsgId ? { ...m, audioUrl: voiceUrl } : m))
          );
          const audio = new Audio(voiceUrl);
          audioInstanceRef.current = audio;
          setPlayingMessageId(assistantMsgId);

          audio.onended = () => {
            if (audioInstanceRef.current === audio) {
              setPlayingMessageId(null);
              audioInstanceRef.current = null;
            }
          };

          audio.onerror = () => {
            if (audioInstanceRef.current === audio) {
              setPlayingMessageId(null);
              audioInstanceRef.current = null;
            }
          };

          audio.play().catch((e) => {
            console.log('Audio autoplay policy:', e);
            setPlayingMessageId(null);
          });
        }
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: `⚠️ **Error generating response:** ${error.message || 'Unknown network error'}.`,
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

  return (
    <div className="flex h-screen bg-[var(--color-bg)] text-[var(--color-text)] overflow-hidden font-sans select-text selection:bg-[var(--color-accent-soft)] selection:text-[var(--color-text)]">
      {/* Collapsible Session Sidebar using --color-sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        health={health}
      />

      {/* Main Chat Workspace using --color-bg */}
      <div className="flex-1 flex flex-col h-full z-10 relative overflow-hidden bg-[var(--color-bg)]">
        {/* Slim Top Header */}
        <Header
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          health={health}
          stats={stats}
          onOpenDrawer={() => setIsDrawerOpen(true)}
          onClearChat={handleClearChat}
          isPlayingAudio={playingMessageId !== null}
          onStopAudio={stopActiveAudio}
          onOpenSystem={() => setIsSystemOpen(true)}
        />

        {/* Messages Stream - Centered column max-w ~720px */}
        <main className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center p-6 text-center max-w-[720px] mx-auto w-full select-none">
              {/* Jarvis HUD Avatar */}
              <div className="w-16 h-16 rounded-full bg-black/80 border border-[var(--color-border)] flex items-center justify-center mb-5 overflow-hidden shadow-lg ring-2 ring-[var(--color-accent)]/20">
                <img src="/jarvis.png" alt="Jarvis" className="w-14 h-14 rounded-full object-contain" />
              </div>

              {/* Centered Serif Greeting */}
              <h2 className="font-serif text-3xl font-medium text-[var(--color-text)] mb-2 tracking-tight">
                What would you like to explore?
              </h2>
              <p className="text-sm font-sans text-[var(--color-muted)] mb-8">
                Search live web topics, or query your uploaded knowledge documents.
              </p>

              {/* 3 Suggested Prompts as small cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full text-left">
                <button
                  onClick={() =>
                    handleSendMessage('Summarize the key findings from my uploaded documents.', false, 'docs')
                  }
                  className="p-3.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-2)] hover:border-[var(--color-accent)]/50 transition text-left cursor-pointer group"
                >
                  <div className="flex items-center justify-between text-xs text-[var(--color-text)] font-medium mb-1">
                    <span className="flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                      Summarize
                    </span>
                    <ArrowUpRight className="w-3.5 h-3.5 text-[var(--color-muted)] group-hover:text-[var(--color-accent)] transition" />
                  </div>
                  <p className="text-[11px] text-[var(--color-muted)] leading-relaxed">
                    Query local ChromaDB vectors for document summaries.
                  </p>
                </button>

                <button
                  onClick={() =>
                    handleSendMessage('What are the key technical points and takeaways?', false, 'auto')
                  }
                  className="p-3.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-2)] hover:border-[var(--color-accent)]/50 transition text-left cursor-pointer group"
                >
                  <div className="flex items-center justify-between text-xs text-[var(--color-text)] font-medium mb-1">
                    <span className="flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                      Key takeaways
                    </span>
                    <ArrowUpRight className="w-3.5 h-3.5 text-[var(--color-muted)] group-hover:text-[var(--color-accent)] transition" />
                  </div>
                  <p className="text-[11px] text-[var(--color-muted)] leading-relaxed">
                    Extract structured bullet points and insights.
                  </p>
                </button>

                <button
                  onClick={() =>
                    handleSendMessage('Search the web for the latest updates on this topic.', false, 'web')
                  }
                  className="p-3.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-2)] hover:border-[var(--color-accent)]/50 transition text-left cursor-pointer group"
                >
                  <div className="flex items-center justify-between text-xs text-[var(--color-text)] font-medium mb-1">
                    <span className="flex items-center gap-1.5">
                      <Globe className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                      Search the web
                    </span>
                    <ArrowUpRight className="w-3.5 h-3.5 text-[var(--color-muted)] group-hover:text-[var(--color-accent)] transition" />
                  </div>
                  <p className="text-[11px] text-[var(--color-muted)] leading-relaxed">
                    Fetch live web information via DuckDuckGo.
                  </p>
                </button>
              </div>

              {/* Dashed Accent-Tinted Dropzone Hint */}
              <button
                onClick={() => setIsDrawerOpen(true)}
                className="w-full mt-6 border border-dashed border-[var(--color-accent)]/30 hover:border-[var(--color-accent)]/60 rounded-xl p-3.5 text-xs text-[var(--color-muted)] hover:text-[var(--color-text)] transition cursor-pointer flex items-center justify-center gap-2"
              >
                <UploadCloud className="w-4 h-4 text-[var(--color-accent)]" />
                <span>Drop documents or click to open knowledge drawer</span>
              </button>
            </div>
          ) : (
            <div className="max-w-[720px] mx-auto w-full py-4 space-y-6">
              {messages.map((msg) => (
                <ChatMessageItem
                  key={msg.id}
                  message={msg}
                  isPlayingAudio={playingMessageId === msg.id}
                  isSynthesizingAudio={synthesizingMessageId === msg.id}
                  onTogglePlayAudio={handleTogglePlayAudio}
                />
              ))}

              {/* Calm Inline Thinking Status */}
              {isLoading && liveStatus && (
                <div className="py-1">
                  <ThinkingStatus statusMessage={liveStatus} searchMode={searchMode} />
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </main>

        {/* Bottom Chat Input (Centered 720px) */}
        <div className="pb-4 pt-1 bg-[var(--color-bg)]">
          <ChatInput
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            onStopGeneration={handleStopGeneration}
            searchMode={searchMode}
            onSearchModeChange={setSearchMode}
            onStopAudio={stopActiveAudio}
            stats={stats}
            sttEnabled={health?.stt_enabled !== false}
          />
        </div>

        {/* Slide-out Document Drawer */}
        <DocumentDrawer
          isOpen={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
          stats={stats}
          onRefreshStats={fetchStats}
        />

        {/* Slide-out System Panel */}
        <SystemPanel
          isOpen={isSystemOpen}
          onClose={() => setIsSystemOpen(false)}
          health={health}
          stats={stats}
          selectedVoice={selectedVoice}
          onSelectVoice={handleSelectVoice}
          availableVoices={availableVoices}
        />
      </div>
    </div>
  );
}
