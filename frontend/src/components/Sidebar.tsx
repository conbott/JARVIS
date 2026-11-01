import React from 'react';
import {
  MessageSquare,
  Plus,
  Trash2,
  PanelLeftClose,
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
  stats?: DocumentStats | null;
}

const getSessionGroup = (createdAtStr: string): 'Today' | 'Yesterday' | 'Previous 7 days' | 'Older' => {
  const date = new Date(createdAtStr);
  const now = new Date();
  if (isNaN(date.getTime())) return 'Today';

  if (date.toDateString() === now.toDateString()) return 'Today';

  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (date.toDateString() === yesterday.toDateString()) return 'Yesterday';

  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays <= 7) return 'Previous 7 days';

  return 'Older';
};

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onToggle,
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  health,
}) => {
  const modelName = health?.llm_model || 'qwen2.5-coder:7b';

  if (!isOpen) {
    return null;
  }

  // Group sessions
  const groups: Record<string, ChatSession[]> = {
    Today: [],
    Yesterday: [],
    'Previous 7 days': [],
    Older: [],
  };

  sessions.forEach((s) => {
    const groupKey = getSessionGroup(s.createdAt);
    if (!groups[groupKey]) groups[groupKey] = [];
    groups[groupKey].push(s);
  });

  const groupKeys = ['Today', 'Yesterday', 'Previous 7 days', 'Older'].filter(
    (k) => groups[k] && groups[k].length > 0
  );

  return (
    <aside className="w-68 bg-[#181716] border-r border-[var(--color-border)] flex flex-col h-full z-20 shrink-0 select-none font-sans">
      {/* Top Header: Quiet New Chat Button & Close Sidebar */}
      <div className="p-3 border-b border-[var(--color-border)] flex items-center justify-between gap-2">
        <button
          onClick={onNewSession}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-[var(--color-surface)] hover:bg-[var(--color-surface-2)] border border-[var(--color-border)] text-xs text-[var(--color-text)] transition"
        >
          <Plus className="w-3.5 h-3.5 text-[var(--color-accent)]" />
          <span>New chat</span>
        </button>

        <button
          onClick={onToggle}
          title="Close sidebar"
          className="p-2 rounded-xl text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)] transition"
        >
          <PanelLeftClose className="w-4 h-4" />
        </button>
      </div>

      {/* Grouped Session List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-4">
        {sessions.length === 0 ? (
          <div className="px-3 py-8 text-center text-xs text-[var(--color-text-muted)]">
            No previous conversations.
          </div>
        ) : (
          groupKeys.map((group) => (
            <div key={group} className="space-y-1">
              <div className="px-2 py-1 text-[11px] font-medium text-[var(--color-text-muted)]">
                {group}
              </div>
              {groups[group].map((session) => {
                const isActive = session.id === activeSessionId;
                return (
                  <div
                    key={session.id}
                    onClick={() => onSelectSession(session.id)}
                    className={`group flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs cursor-pointer transition ${
                      isActive
                        ? 'bg-[var(--color-surface-2)] text-[var(--color-text)] font-medium'
                        : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)]'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <MessageSquare className="w-3.5 h-3.5 shrink-0 opacity-60" />
                      <span className="truncate">{session.title || 'Untitled'}</span>
                    </div>

                    <button
                      onClick={(e) => onDeleteSession(session.id, e)}
                      title="Delete conversation"
                      className="opacity-0 group-hover:opacity-100 p-1 hover:text-[var(--color-warn)] rounded transition"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                );
              })}
            </div>
          ))
        )}
      </div>

      {/* Footer: Single quiet muted line */}
      <div className="p-3 border-t border-[var(--color-border)] flex items-center justify-between text-xs text-[var(--color-text-muted)]">
        <div className="flex items-center gap-2 truncate">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-accent)] shrink-0" />
          <span className="font-mono text-[11px] truncate">{modelName}</span>
        </div>
        <span className="text-[10px] text-[var(--color-text-muted)] font-mono">Ready</span>
      </div>
    </aside>
  );
};
