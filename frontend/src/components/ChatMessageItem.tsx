import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Copy,
  Check,
  FileText,
  Globe,
  Volume2,
  Square,
  ExternalLink,
  Loader2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import type { ChatMessage } from '../types';

interface ChatMessageItemProps {
  message: ChatMessage;
  isPlayingAudio?: boolean;
  isSynthesizingAudio?: boolean;
  onTogglePlayAudio?: (messageId: string, text: string) => void;
}

const CodeBlock: React.FC<{ language?: string; value: string }> = ({ language, value }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative my-3.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden font-mono text-xs">
      <div className="flex items-center justify-between px-3.5 py-1.5 border-b border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-muted)] text-[11px]">
        <span>{language || 'code'}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 hover:text-[var(--color-text)] transition cursor-pointer"
          title="Copy code"
        >
          {copied ? <Check className="w-3 h-3 text-[var(--color-accent)]" /> : <Copy className="w-3 h-3" />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
      <pre className="p-3.5 overflow-x-auto text-[var(--color-text)] leading-relaxed font-mono">
        <code>{value}</code>
      </pre>
    </div>
  );
};

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({
  message,
  isPlayingAudio = false,
  isSynthesizingAudio = false,
  onTogglePlayAudio,
}) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [expandedDocIdx, setExpandedDocIdx] = useState<number | null>(null);
  const [showAllSources, setShowAllSources] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getDomain = (url?: string) => {
    if (!url) return '';
    try {
      const parsed = new URL(url);
      return parsed.hostname.replace('www.', '');
    } catch {
      return '';
    }
  };

  const getFallbackExplanation = (reason?: string | null) => {
    switch (reason) {
      case 'low_confidence':
        return 'No strong match in your documents, so I searched the web';
      case 'empty_store':
        return 'No documents uploaded';
      case 'realtime_query':
        return 'Needs live info';
      case 'forced_web':
        return 'Web search requested';
      default:
        return null;
    }
  };

  const allSources = message.sources || [];
  const visibleSources = showAllSources ? allSources : allSources.slice(0, 4);
  const fallbackExplanation = getFallbackExplanation(message.fallback_reason);

  return (
    <div className={`py-1.5 md:py-2 px-4 md:px-0 group ${isUser ? 'flex justify-end' : ''}`}>
      <div className={`w-full ${isUser ? 'flex justify-end' : ''}`}>
        {/* User Message: right-aligned, width fits content (max 80%), accent-soft bg, 1px accent 20% border */}
        {isUser ? (
          <div className="w-fit max-w-[80%] ml-auto bg-[var(--color-accent-soft)] border border-[var(--color-accent)]/20 text-[var(--color-text)] rounded-2xl px-4 py-3 text-sm font-sans leading-relaxed whitespace-pre-wrap">
            {message.content}
          </div>
        ) : (
          /* Assistant Message: NO bubble, plain text on background, warm serif 17px/1.7 */
          <div className="space-y-3.5 max-w-full">
            {/* Assistant Body */}
            <div className="prose-claude text-[17px] leading-[1.7] text-[var(--color-text)] font-serif max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    const isInline = !match && !String(children).includes('\n');
                    if (isInline) {
                      return (
                        <code
                          className="bg-[var(--color-surface-2)] text-[var(--color-text)] px-1.5 py-0.5 rounded text-xs font-mono border border-[var(--color-border)]"
                          {...props}
                        >
                          {children}
                        </code>
                      );
                    }
                    return (
                      <CodeBlock
                        language={match ? match[1] : ''}
                        value={String(children).replace(/\n$/, '')}
                      />
                    );
                  },
                  a({ href, children }) {
                    return (
                      <a
                        href={href}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[var(--color-accent)] hover:underline underline-offset-2"
                      >
                        {children}
                      </a>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>

            {/* Sources Block (Under Assistant Message) */}
            {allSources.length > 0 && (
              <div className="pt-1 font-sans">
                {/* Source Label & Reason Row */}
                <div className="flex flex-wrap items-center gap-2 text-xs mb-2">
                  {message.path === 'web' || message.source_type === 'web' ? (
                    <span className="font-medium text-[var(--color-warn)] flex items-center gap-1.5">
                      <Globe className="w-3.5 h-3.5" />
                      Searched the web
                    </span>
                  ) : (
                    <span className="font-medium text-[var(--color-muted)] flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                      From your documents
                    </span>
                  )}

                  {fallbackExplanation && (
                    <>
                      <span className="text-[var(--color-muted)] opacity-40">•</span>
                      <span className="text-[var(--color-muted)] text-[11px]">
                        {fallbackExplanation}
                      </span>
                    </>
                  )}
                </div>

                {/* Chips Grid */}
                <div className="flex flex-wrap gap-2">
                  {visibleSources.map((src, idx) => {
                    const isDoc = src.source_type === 'document';
                    const domain = src.domain || getDomain(src.url);
                    const isExpanded = expandedDocIdx === idx;

                    if (isDoc) {
                      return (
                        <div key={idx} className="flex flex-col">
                          <button
                            onClick={() => setExpandedDocIdx(isExpanded ? null : idx)}
                            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[var(--color-surface)] hover:bg-[var(--color-surface-2)] border border-[var(--color-border)] hover:border-[var(--color-accent)]/50 text-xs text-[var(--color-text)] transition text-left cursor-pointer"
                          >
                            <FileText className="w-3 h-3 text-[var(--color-accent)] shrink-0" />
                            <span className="font-mono text-[11px] truncate max-w-[150px]">
                              {src.filename || src.title}
                            </span>
                            {src.page && (
                              <span className="text-[10px] text-[var(--color-muted)] font-mono">
                                p.{src.page}
                              </span>
                            )}
                            {src.score != null && (
                              <span className="text-[10px] text-[var(--color-accent)] font-mono ml-0.5">
                                {Math.round(src.score * 100)}%
                              </span>
                            )}
                          </button>

                          {/* Inline Expandable Snippet */}
                          {isExpanded && src.snippet && (
                            <div className="mt-1.5 p-2.5 rounded-lg bg-[var(--color-surface-2)] border border-[var(--color-border)] text-xs text-[var(--color-muted)] leading-relaxed max-w-lg">
                              {src.snippet}
                            </div>
                          )}
                        </div>
                      );
                    }

                    // Web Source Chip
                    return (
                      <a
                        key={idx}
                        href={src.url || '#'}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[var(--color-surface)] hover:bg-[var(--color-surface-2)] border border-[var(--color-border)] hover:border-[var(--color-accent)]/50 text-xs text-[var(--color-text)] transition group/chip"
                        title={src.title}
                      >
                        <Globe className="w-3 h-3 text-[var(--color-warn)] shrink-0" />
                        <span className="font-mono text-[11px] text-[var(--color-muted)] truncate max-w-[110px]">
                          {domain || 'web'}
                        </span>
                        <span className="truncate max-w-[150px] text-[var(--color-text)] font-sans">
                          {src.title}
                        </span>
                        <ExternalLink className="w-2.5 h-2.5 text-[var(--color-muted)] opacity-60 group-hover/chip:opacity-100 transition" />
                      </a>
                    );
                  })}
                </div>

                {/* Collapsible Row if > 4 sources */}
                {allSources.length > 4 && (
                  <button
                    onClick={() => setShowAllSources(!showAllSources)}
                    className="mt-2 text-[11px] text-[var(--color-muted)] hover:text-[var(--color-text)] flex items-center gap-1 transition cursor-pointer"
                  >
                    {showAllSources ? (
                      <>
                        <ChevronUp className="w-3 h-3" />
                        <span>Show fewer sources</span>
                      </>
                    ) : (
                      <>
                        <ChevronDown className="w-3 h-3" />
                        <span>Sources ({allSources.length})</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            )}

            {/* Message Actions (Copy, Speak): small, muted, visible on hover */}
            <div className="flex items-center gap-2 pt-0.5 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity font-sans text-xs">
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 px-2 py-1 rounded-md text-[var(--color-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)] transition cursor-pointer"
                title="Copy response"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                    <span className="text-[11px] text-[var(--color-accent)]">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span className="text-[11px]">Copy</span>
                  </>
                )}
              </button>

              {onTogglePlayAudio && (
                <button
                  onClick={() => onTogglePlayAudio(message.id, message.content)}
                  disabled={isSynthesizingAudio}
                  className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs transition cursor-pointer ${
                    isPlayingAudio
                      ? 'text-[var(--color-accent)] bg-[var(--color-accent-soft)]'
                      : 'text-[var(--color-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface)]'
                  }`}
                  title={isPlayingAudio ? 'Stop speaking' : 'Speak answer aloud'}
                >
                  {isSynthesizingAudio ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-[var(--color-accent)]" />
                      <span className="text-[11px]">Synthesizing...</span>
                    </>
                  ) : isPlayingAudio ? (
                    <>
                      <div className="flex items-center gap-0.5 h-3">
                        <span className="w-0.5 h-2.5 bg-[var(--color-accent)] animate-pulse rounded-full" />
                        <span className="w-0.5 h-3 bg-[var(--color-accent)] animate-pulse rounded-full delay-75" />
                        <span className="w-0.5 h-1.5 bg-[var(--color-accent)] animate-pulse rounded-full delay-150" />
                      </div>
                      <Square className="w-3 h-3 fill-current ml-0.5" />
                      <span className="text-[11px] font-medium">Stop</span>
                    </>
                  ) : (
                    <>
                      <Volume2 className="w-3.5 h-3.5" />
                      <span className="text-[11px]">Speak</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
