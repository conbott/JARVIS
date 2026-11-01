import React, { useState, useRef, useEffect } from 'react';
import {
  Cpu,
  Database,
  Cloud,
  FileText,
  Trash2,
  Activity,
  Zap,
  PanelLeft,
  Volume2,
  Square,
  ChevronDown,
  Check,
} from 'lucide-react';
import type { HealthStatus, DocumentStats, VoiceOption } from '../types';

interface HeaderProps {
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  health: HealthStatus | null;
  stats: DocumentStats | null;
  onOpenDrawer: () => void;
  onClearChat: () => void;
  selectedVoice?: string;
  onSelectVoice?: (voiceId: string) => void;
  availableVoices?: VoiceOption[];
  isPlayingAudio?: boolean;
  onStopAudio?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  isSidebarOpen,
  onToggleSidebar,
  health,
  stats,
  onOpenDrawer,
  onClearChat,
  selectedVoice = 'en-US-GuyNeural',
  onSelectVoice,
  availableVoices = [],
  isPlayingAudio = false,
  onStopAudio,
}) => {
  const hardwareLabel = health?.device_info?.device_name || 'Hardware Accelerated';
  const isGpu = health?.device_info?.is_gpu ?? true;

  const [isVoiceDropdownOpen, setIsVoiceDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicked outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsVoiceDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const currentVoiceObj = availableVoices.find((v) => v.id === selectedVoice);
  const voiceDisplayName = currentVoiceObj ? currentVoiceObj.name.split(' (')[0] : 'Guy';

  return (
    <header className="sticky top-0 z-30 border-b border-white/[0.06] bg-[#08090d]/80 backdrop-blur-xl px-4 py-3 flex items-center justify-between">
      {/* Title & Brand */}
      <div className="flex items-center space-x-3">
        <button
          onClick={onToggleSidebar}
          title={isSidebarOpen ? 'Close sidebar' : 'Open conversations sidebar'}
          className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/[0.05] transition"
        >
          <PanelLeft className="w-4 h-4" />
        </button>

        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-600/20">
          <Activity className="w-4 h-4 text-white animate-pulse" />
        </div>

        <div>
          <h1 className="text-sm font-bold text-white flex items-center gap-2">
            <span>Local RAG & Voice Assistant</span>
            <span
              title={`Detected Hardware: ${hardwareLabel}`}
              className={`hidden sm:inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                isGpu
                  ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
                  : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              }`}
            >
              <Zap className="w-2.5 h-2.5" />
              {hardwareLabel}
            </span>
          </h1>
          <p className="text-[11px] text-slate-400 hidden sm:block">
            Universal Local RAG • Dynamic Device Detection • Dual Vector DB • Live Web Search
          </p>
        </div>
      </div>

      {/* Status Badges */}
      <div className="hidden lg:flex items-center space-x-2.5 text-xs">
        {/* Ollama Status */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-white/[0.03] border border-white/[0.06] text-slate-300">
          <Cpu className="w-3 h-3 text-indigo-400" />
          <span className="text-[11px] font-mono">{health?.llm_model || 'Ollama'}</span>
          {health?.ollama_online ? (
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
          ) : (
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          )}
        </div>

        {/* ChromaDB Status */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-white/[0.03] border border-white/[0.06] text-slate-300">
          <Database className="w-3 h-3 text-cyan-400" />
          <span className="text-[11px] font-mono text-cyan-300">
            {stats?.total_chunks ?? 0} Chunks
          </span>
        </div>

        {/* Pinecone Cloud Target */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-white/[0.03] border border-white/[0.06] text-slate-300">
          <Cloud className="w-3 h-3 text-purple-400" />
          <span className="text-[11px] font-mono text-purple-300">
            {health?.cloud_sync_target?.index || 'attention-paper'}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center space-x-2">
        {/* Global Stop Audio Button (visible whenever audio is speaking) */}
        {isPlayingAudio && onStopAudio && (
          <button
            onClick={onStopAudio}
            className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-xl bg-rose-500/20 text-rose-300 border border-rose-500/30 hover:bg-rose-500/30 text-xs font-medium transition animate-pulse shadow-sm shadow-rose-500/20"
            title="Stop playing audio immediately"
          >
            <Square className="w-3 h-3 fill-rose-400 text-rose-400" />
            <span>Stop Audio</span>
          </button>
        )}

        {/* Voice Selector Dropdown */}
        {availableVoices.length > 0 && onSelectVoice && (
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setIsVoiceDropdownOpen(!isVoiceDropdownOpen)}
              className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.06] text-slate-300 text-xs transition"
              title="Select Neural Text-to-Speech Voice"
            >
              <Volume2 className="w-3.5 h-3.5 text-indigo-400" />
              <span className="hidden sm:inline font-mono text-[11px] text-slate-300">
                Voice: {voiceDisplayName}
              </span>
              <ChevronDown className={`w-3 h-3 text-slate-400 transition-transform ${isVoiceDropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* Dropdown Menu */}
            {isVoiceDropdownOpen && (
              <div className="absolute right-0 mt-2 w-72 rounded-2xl bg-[#0f111a] border border-white/[0.1] shadow-2xl p-2 z-50 text-left backdrop-blur-2xl">
                <div className="px-2.5 py-1.5 border-b border-white/[0.06] mb-1">
                  <div className="text-[11px] font-semibold text-slate-200">Neural Voice Selection</div>
                  <div className="text-[10px] text-slate-400">Lightweight Edge-TTS • 0 MB GPU overhead</div>
                </div>

                <div className="max-h-60 overflow-y-auto space-y-0.5 custom-scrollbar">
                  {availableVoices.map((voice) => {
                    const isSelected = voice.id === selectedVoice;
                    return (
                      <button
                        key={voice.id}
                        onClick={() => {
                          onSelectVoice(voice.id);
                          setIsVoiceDropdownOpen(false);
                        }}
                        className={`w-full flex items-center justify-between px-2.5 py-2 rounded-xl text-xs transition ${
                          isSelected
                            ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                            : 'text-slate-300 hover:bg-white/[0.04]'
                        }`}
                      >
                        <div className="flex flex-col text-left">
                          <span className="font-medium text-slate-200">{voice.name}</span>
                          <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono">
                            {voice.accent} • {voice.gender}
                          </span>
                        </div>
                        {isSelected && <Check className="w-3.5 h-3.5 text-indigo-400 ml-2 shrink-0" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        <button
          onClick={onOpenDrawer}
          className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white shadow-sm shadow-indigo-600/20 transition"
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Documents & Sync</span>
        </button>

        <button
          onClick={onClearChat}
          title="Clear Conversation"
          className="p-2 rounded-xl border border-white/[0.06] hover:bg-white/[0.05] text-slate-400 hover:text-rose-400 transition"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </header>
  );
};
