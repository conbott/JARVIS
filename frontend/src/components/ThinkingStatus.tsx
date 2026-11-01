import React from 'react';
import { Loader2, Globe, FileText, Sparkles, Clock } from 'lucide-react';

interface ThinkingStatusProps {
  statusMessage?: string;
  searchMode: string;
}

export const ThinkingStatus: React.FC<ThinkingStatusProps> = ({
  statusMessage,
  searchMode,
}) => {
  const getIcon = () => {
    if (statusMessage?.includes('Searching the web') || statusMessage?.includes('web')) {
      return <Globe className="w-3.5 h-3.5 text-emerald-400 animate-spin" />;
    }
    if (statusMessage?.includes('document') || statusMessage?.includes('ChromaDB')) {
      return <FileText className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />;
    }
    if (statusMessage?.includes('clock') || statusMessage?.includes('time')) {
      return <Clock className="w-3.5 h-3.5 text-amber-400 animate-pulse" />;
    }
    return <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />;
  };

  const displayText =
    statusMessage ||
    (searchMode === 'web'
      ? 'Querying live web sources...'
      : searchMode === 'docs'
      ? 'Scanning ChromaDB document index...'
      : 'Analyzing query and grounding context...');

  return (
    <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-white/[0.03] border border-white/[0.06] text-xs text-slate-300 w-fit max-w-md animate-pulse">
      {getIcon()}
      <span className="font-mono text-[11px] truncate">{displayText}</span>
      <Loader2 className="w-3 h-3 text-slate-500 animate-spin shrink-0 ml-1" />
    </div>
  );
};
