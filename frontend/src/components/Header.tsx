import React from 'react';
import { Cpu, Database, Cloud, FileText, Trash2, Activity, Zap } from 'lucide-react';
import type { HealthStatus, DocumentStats } from '../types';

interface HeaderProps {
  health: HealthStatus | null;
  stats: DocumentStats | null;
  onOpenDrawer: () => void;
  onClearChat: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  stats,
  onOpenDrawer,
  onClearChat,
}) => {
  const hardwareLabel = health?.device_info?.device_name || 'Hardware Accelerated';
  const isGpu = health?.device_info?.is_gpu ?? true;

  return (
    <header className="sticky top-0 z-30 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-4 py-3 flex items-center justify-between">
      {/* Title & Brand */}
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <Activity className="w-5 h-5 text-white animate-pulse" />
        </div>
        <div>
          <h1 className="text-base font-bold text-white flex items-center gap-2">
            Local RAG & Voice Assistant
            <span
              title={`Detected Hardware: ${hardwareLabel}`}
              className={`text-[10px] uppercase font-semibold border px-2 py-0.5 rounded-full flex items-center gap-1 ${
                isGpu
                  ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
                  : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              }`}
            >
              <Zap className="w-2.5 h-2.5" />
              {hardwareLabel}
            </span>
          </h1>
          <p className="text-xs text-slate-400">
            Universal Local RAG • Dynamic Device Detection • Dual Vector DB (Chroma + Pinecone) • Live Search
          </p>
        </div>
      </div>

      {/* Status Badges */}
      <div className="hidden md:flex items-center space-x-3 text-xs">
        {/* Ollama Status */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 text-slate-300">
          <Cpu className="w-3.5 h-3.5 text-indigo-400" />
          <span className="font-medium">Ollama:</span>
          {health?.ollama_online ? (
            <span className="flex items-center gap-1 text-emerald-400 font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              {health.llm_model}
            </span>
          ) : (
            <span className="text-amber-400">Connecting...</span>
          )}
        </div>

        {/* ChromaDB Status */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 text-slate-300">
          <Database className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-medium">Chroma:</span>
          <span className="text-cyan-300 font-semibold">
            {stats?.total_chunks ?? 0} Chunks
          </span>
        </div>

        {/* Pinecone Cloud Target */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 text-slate-300">
          <Cloud className="w-3.5 h-3.5 text-purple-400" />
          <span className="font-medium">Pinecone:</span>
          <span className="text-purple-300">
            {health?.cloud_sync_target?.index || 'attention-paper'}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center space-x-2">
        <button
          onClick={onOpenDrawer}
          className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm transition"
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Documents & Sync</span>
        </button>

        <button
          onClick={onClearChat}
          title="Clear Conversation"
          className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-rose-400 transition"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
