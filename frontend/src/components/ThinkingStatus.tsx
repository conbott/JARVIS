import React from 'react';

interface ThinkingStatusProps {
  statusMessage?: string;
  searchMode: string;
}

export const ThinkingStatus: React.FC<ThinkingStatusProps> = ({
  statusMessage,
  searchMode,
}) => {
  const displayText =
    statusMessage ||
    (searchMode === 'web'
      ? 'Searching the web...'
      : searchMode === 'docs'
      ? 'Reading your documents...'
      : 'Thinking...');

  return (
    <div className="flex items-center gap-2 py-1.5 text-xs text-[var(--color-text-muted)] font-sans select-none">
      <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-accent)] animate-pulse shrink-0" />
      <span>{displayText}</span>
    </div>
  );
};
