import { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { ChatMessageItem } from './components/ChatMessageItem';
import { ChatInput } from './components/ChatInput';
import { DocumentDrawer } from './components/DocumentDrawer';
import type { ChatMessage, DocumentStats, HealthStatus, SourceItem } from './types';
import { Sparkles, FileText, Globe, Volume2 } from 'lucide-react';

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

  const handleClearChat = () => {
    if (messages.length === 0 || confirm('Clear the chat history?')) {
      setMessages([]);
    }
  };

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (text: string, isVoice: boolean) => {
    if (!text.trim() || isLoading) return;

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

    setMessages((prev) => [...prev, userMessage, initialAssistantMessage]);
    setIsLoading(true);

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

              if (eventData.type === 'sources') {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? {
                          ...m,
                          source_type: eventData.source_type,
                          sources: eventData.sources as SourceItem[],
                        }
                      : m
                  )
                );
              } else if (eventData.type === 'token') {
                fullGeneratedContent += eventData.content;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId ? { ...m, content: m.content + eventData.content } : m
                  )
                );
              } else if (eventData.type === 'done') {
                break;
              }
            } catch (err) {
              console.error('SSE JSON parse error:', err);
            }
          }
        }
      }

      // If user invoked via Push-to-Talk Voice: synthesize speech and auto-play
      if (isVoice && fullGeneratedContent.trim()) {
        try {
          const voiceRes = await fetch('/api/voice/synthesize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: fullGeneratedContent }),
          });

          if (voiceRes.ok) {
            const audioBlob = await voiceRes.blob();
            const audioUrl = URL.createObjectURL(audioBlob);

            setMessages((prev) =>
              prev.map((m) => (m.id === assistantMsgId ? { ...m, audioUrl } : m))
            );
          }
        } catch (voiceErr) {
          console.error('Failed to synthesize response audio:', voiceErr);
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content:
                    m.content ||
                    'Connection error: Failed to reach the local backend server. Please verify FastAPI is running.',
                }
              : m
          )
        );
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 overflow-hidden">
      {/* Top Header */}
      <Header
        health={health}
        stats={stats}
        onOpenDrawer={() => setIsDrawerOpen(true)}
        onClearChat={handleClearChat}
      />

      {/* Main Conversation Stream */}
      <main className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-6 text-center max-w-2xl mx-auto">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-500 flex items-center justify-center shadow-xl shadow-indigo-500/20 mb-6">
              <Sparkles className="w-8 h-8 text-white" />
            </div>

            <h2 className="text-2xl font-bold text-white mb-2">
              Next-Gen Local RAG & Voice AI
            </h2>
            <p className="text-sm text-slate-400 mb-8 max-w-md">
              Powered by <span className="text-indigo-400 font-semibold">Qwen 2.5 Coder (7B)</span> on your RTX 4050 GPU, local <span className="text-cyan-400 font-semibold">ChromaDB</span>, and automatic web search.
            </p>

            {/* Quick Starters */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 w-full text-left">
              <button
                onClick={() =>
                  handleSendMessage('What are the key capabilities of this local RAG system?', false)
                }
                className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/50 hover:bg-slate-900 hover:border-indigo-500/50 transition group"
              >
                <div className="flex items-center space-x-2 text-indigo-400 font-semibold text-xs mb-1">
                  <Sparkles className="w-4 h-4" />
                  <span>Explore Capabilities</span>
                </div>
                <p className="text-xs text-slate-400">
                  Ask about architecture, models, and zero-cost local execution.
                </p>
              </button>

              <button
                onClick={() => setIsDrawerOpen(true)}
                className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/50 hover:bg-slate-900 hover:border-cyan-500/50 transition group"
              >
                <div className="flex items-center space-x-2 text-cyan-400 font-semibold text-xs mb-1">
                  <FileText className="w-4 h-4" />
                  <span>Upload Documents</span>
                </div>
                <p className="text-xs text-slate-400">
                  Drop PDFs or TXT files to query them locally with high precision.
                </p>
              </button>

              <button
                onClick={() =>
                  handleSendMessage('What were the major AI model releases this week?', false)
                }
                className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/50 hover:bg-slate-900 hover:border-amber-500/50 transition group"
              >
                <div className="flex items-center space-x-2 text-amber-400 font-semibold text-xs mb-1">
                  <Globe className="w-4 h-4" />
                  <span>Live Web Search</span>
                </div>
                <p className="text-xs text-slate-400">
                  Autonomous DuckDuckGo fallback queries live internet data.
                </p>
              </button>
            </div>

            <div className="mt-8 flex items-center space-x-4 text-xs text-slate-500">
              <span className="flex items-center gap-1.5">
                <Volume2 className="w-3.5 h-3.5 text-indigo-400" />
                <span>Push-to-Talk Voice Supported</span>
              </span>
              <span>•</span>
              <span>Pinecone 2GB Cloud Sync Ready</span>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-slate-900/40">
            {messages.map((msg) => (
              <ChatMessageItem key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      {/* Bottom Chat Input */}
      <ChatInput
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        onStopGeneration={handleStopGeneration}
      />

      {/* Slide-out Document Drawer */}
      <DocumentDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        stats={stats}
        onRefreshStats={fetchStats}
      />
    </div>
  );
}
