import React from 'react';
import { PanelLeft, FileText, Square, Settings2 } from 'lucide-react';
import type { HealthStatus, DocumentStats, VoiceOption } from '../types';

interface HeaderProps {
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  health: HealthStatus | null;
  stats: DocumentStats | null;
  onOpenDrawer: () => void;
  onClearChat?: () => void;
  selectedVoice?: string;
  onSelectVoice?: (voiceId: string) => void;
  availableVoices?: VoiceOption[];
  isPlayingAudio?: boolean;
  onStopAudio?: () => void;
  onOpenSystem?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  isSidebarOpen,
  onToggleSidebar,
  health,
  stats,
  onOpenDrawer,
  isPlayingAudio = false,
  onStopAudio,
  onOpenSystem,
}) => {
  const modelName = health?.llm_model || 'qwen2.5-coder:7b';
  const docCount = stats?.document_count ?? 0;

  return (
    <header className="sticky top-0 z-30 h-14 border-b border-[var(--color-border)] bg-[var(--color-bg)]/90 backdrop-blur-md px-4 flex items-center justify-between">
      {/* Left: Sidebar Toggle + Serif Title */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          title={isSidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
          className="p-1.5 rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)] transition"
        >
          <PanelLeft className="w-4 h-4" />
        </button>

        <span className="font-serif text-base tracking-tight text-[var(--color-text)] font-medium">
          Assistant
        </span>
      </div>

      {/* Right: Stop Audio (when playing) + Status chip + Documents button */}
      <div className="flex items-center gap-2">
        {/* Global Stop Audio Button (only when playing) */}
        {isPlayingAudio && onStopAudio && (
          <button
            onClick={onStopAudio}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-xs text-[var(--color-warn)] hover:bg-[var(--color-surface-2)] transition animate-pulse"
            title="Stop audio playback"
          >
            <Square className="w-3 h-3 fill-current" />
            <span>Stop Audio</span>
          </button>
        )}

        {/* Documents Button */}
        <button
          onClick={onOpenDrawer}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-sans text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)] border border-transparent hover:border-[var(--color-border)] transition"
          title="Manage uploaded documents"
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Documents</span>
          {docCount > 0 && (
            <span className="px-1.5 py-0.2 rounded-full bg-[var(--color-surface-2)] text-[10px] font-mono text-[var(--color-text)]">
              {docCount}
            </span>
          )}
        </button>

        {/* Single System Status Chip */}
        <button
          onClick={onOpenSystem}
          className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-[var(--color-surface)] hover:bg-[var(--color-surface-2)] border border-[var(--color-border)] text-xs font-sans text-[var(--color-text)] transition cursor-pointer"
          title="Open system configuration & status"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-accent)] animate-pulse" />
          <span className="font-mono text-[11px] text-[var(--color-text-muted)] truncate max-w-[130px]">
            {modelName}
          </span>
          <Settings2 className="w-3 h-3 text-[var(--color-text-muted)] ml-0.5" />
        </button>
      </div>
    </header>
  );
};
