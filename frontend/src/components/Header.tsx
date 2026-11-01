import React from 'react';
import {
  Cpu,
  Database,
  Cloud,
  FileText,
  Trash2,
  Activity,
  Zap,
  PanelLeft,
} from 'lucide-react';
import type { HealthStatus, DocumentStats } from '../types';

interface HeaderProps {
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  health: HealthStatus | null;
  stats: DocumentStats | null;
  onOpenDrawer: () => void;
  onClearChat: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  isSidebarOpen,
  onToggleSidebar,
  health,
  stats,
  onOpenDrawer,
  onClearChat,
}) => {
  const hardwareLabel = health?.device_info?.device_name || 'Hardware Accelerated';
  const isGpu = health?.device_info?.is_gpu ?? true;

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
