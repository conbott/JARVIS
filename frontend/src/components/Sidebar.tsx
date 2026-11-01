import React from 'react';
import {
  MessageSquare,
  Plus,
  Trash2,
  Cpu,
  Database,
  Cloud,
  PanelLeftClose,
  Zap,
} from 'lucide-react';
import type { ChatSession, HealthStatus, DocumentStats } from '../types';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  sessions: ChatSession[];
  activeSessionId: string;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onDeleteSession: (id: string, e: React.MouseEvent) => void;
  health: HealthStatus | null;
  stats: DocumentStats | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onToggle,
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  health,
  stats,
}) => {
  const hardwareLabel = health?.device_info?.device_name || 'Hardware Accelerated';

  if (!isOpen) {
    return null;
  }

  return (
    <aside className="w-72 bg-[#0c0d14] border-r border-white/[0.06] flex flex-col h-full z-20 shrink-0 transition-all duration-300">
      {/* Top Header */}
      <div className="p-3.5 border-b border-white/[0.06] flex items-center justify-between">
        <button
          onClick={onNewSession}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition group"
        >
          <Plus className="w-4 h-4 group-hover:rotate-90 transition-transform duration-200" />
          <span>New Chat</span>
        </button>

        <button
          onClick={onToggle}
          title="Close Sidebar"
          className="ml-2 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/[0.05] transition"
        >
          <PanelLeftClose className="w-4 h-4" />
        </button>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        <div className="px-2 py-1.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
          Conversations
        </div>

        {sessions.length === 0 ? (
          <div className="px-3 py-6 text-center text-xs text-slate-500">
            No saved conversations yet.
          </div>
        ) : (
          sessions.map((session) => {
            const isActive = session.id === activeSessionId;
            return (
              <div
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                className={`group flex items-center justify-between px-3 py-2 rounded-xl text-xs cursor-pointer transition ${
                  isActive
                    ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/20 font-medium'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                }`}
              >
                <div className="flex items-center gap-2.5 truncate">
                  <MessageSquare
                    className={`w-3.5 h-3.5 shrink-0 ${
                      isActive ? 'text-indigo-400' : 'text-slate-500 group-hover:text-slate-300'
                    }`}
                  />
                  <span className="truncate">{session.title || 'Untitled Chat'}</span>
                </div>

                <button
                  onClick={(e) => onDeleteSession(session.id, e)}
                  title="Delete chat"
                  className="opacity-0 group-hover:opacity-100 p-1 rounded-lg hover:text-rose-400 transition"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Hardware & System Telemetry Card */}
      <div className="p-3 border-t border-white/[0.06] bg-black/20 space-y-2 text-xs">
        <div className="flex items-center justify-between text-slate-400 text-[11px]">
          <span className="flex items-center gap-1.5 font-medium">
            <Zap className="w-3 h-3 text-amber-400" />
            <span>Hardware Engine</span>
          </span>
          <span className="flex items-center gap-1 text-emerald-400 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Active
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.05] space-y-1.5">
          <div className="text-[11px] font-semibold text-slate-200 truncate" title={hardwareLabel}>
            {hardwareLabel}
          </div>

          <div className="flex items-center justify-between text-[10px] text-slate-400">
            <span className="flex items-center gap-1">
              <Cpu className="w-3 h-3 text-indigo-400" />
              <span>{health?.llm_model || 'Local Model'}</span>
            </span>
            <span className="flex items-center gap-1">
              <Database className="w-3 h-3 text-cyan-400" />
              <span>{stats?.total_chunks ?? 0} Chunks</span>
            </span>
          </div>

          <div className="flex items-center justify-between text-[10px] text-slate-500 pt-0.5 border-t border-white/[0.04]">
            <span className="flex items-center gap-1">
              <Cloud className="w-3 h-3 text-purple-400" />
              <span>{health?.cloud_sync_target?.index || 'Pinecone Sync'}</span>
            </span>
            <span>Local RAG</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
