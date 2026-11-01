import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Sparkles,
  User,
  Copy,
  Check,
  FileText,
  Globe,
  Volume2,
  ExternalLink,
  Loader2,
} from 'lucide-react';
import type { ChatMessage } from '../types';

interface ChatMessageItemProps {
  message: ChatMessage;
  onSynthesizeVoice?: (text: string) => Promise<string | undefined>;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({
  message,
  onSynthesizeVoice,
}) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | undefined>(message.audioUrl);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePlayVoice = async () => {
    if (audioUrl) {
      const audio = new Audio(audioUrl);
      setIsPlayingAudio(true);
      audio.onended = () => setIsPlayingAudio(false);
      audio.onerror = () => setIsPlayingAudio(false);
      audio.play().catch(() => setIsPlayingAudio(false));
      return;
    }

    if (onSynthesizeVoice && message.content) {
      setIsLoadingAudio(true);
      try {
        const url = await onSynthesizeVoice(message.content);
        if (url) {
          setAudioUrl(url);
          const audio = new Audio(url);
          setIsPlayingAudio(true);
          audio.onended = () => setIsPlayingAudio(false);
          audio.onerror = () => setIsPlayingAudio(false);
          audio.play().catch(() => setIsPlayingAudio(false));
        }
      } catch (err) {
        console.error('TTS synthesis error:', err);
      } finally {
        setIsLoadingAudio(false);
      }
    }
  };

  // Extract clean domain for web source badge
  const getDomain = (url?: string) => {
    if (!url) return 'Source';
    try {
      const parsed = new URL(url);
      return parsed.hostname.replace('www.', '');
    } catch {
      return 'Web';
    }
  };

  return (
    <div
      className={`py-5 px-4 md:px-8 flex ${
        isUser ? 'justify-end' : 'justify-start bg-white/[0.015] border-y border-white/[0.04]'
      }`}
    >
      <div className={`flex gap-3 max-w-4xl w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
        {/* Assistant Avatar */}
        {!isUser && (
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-600 flex items-center justify-center shrink-0 text-white shadow-md shadow-indigo-600/20 mt-1">
            <Sparkles className="w-4 h-4" />
          </div>
        )}

        <div className={`flex flex-col space-y-2.5 ${isUser ? 'items-end' : 'items-start'} max-w-3xl w-full`}>
          {/* Header row */}
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <span className="font-semibold text-slate-200">
              {isUser ? 'You' : 'Assistant'}
            </span>
            <span className="text-slate-600">•</span>
            <span className="text-[11px] text-slate-500">{message.timestamp}</span>

            {/* Mode badge for Assistant */}
            {!isUser && message.source_type && message.source_type !== 'direct' && (
              <span
                className={`flex items-center gap-1.5 text-[10px] font-medium px-2 py-0.5 rounded-full border ${
                  message.source_type === 'document'
                    ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/25'
                    : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25'
                }`}
              >
                {message.source_type === 'document' ? (
                  <>
                    <FileText className="w-3 h-3 text-cyan-400" />
                    <span>Local Document Grounding</span>
                  </>
                ) : (
                  <>
                    <Globe className="w-3 h-3 text-emerald-400" />
                    <span>Live Web Grounding</span>
                  </>
                )}
              </span>
            )}
          </div>

          {/* Perplexity-Style Interactive Source Cards (if sources present) */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="w-full space-y-1.5 pt-1">
              <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                {message.source_type === 'document' ? (
                  <>
                    <FileText className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Referenced Document Chunks ({message.sources.length})</span>
                  </>
                ) : (
                  <>
                    <Globe className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Web Sources ({message.sources.length})</span>
                  </>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2">
                {message.sources.map((src, idx) => {
                  const domain = src.source_type === 'web' ? getDomain(src.url) : 'Local Doc';
                  return (
                    <a
                      key={idx}
                      href={src.url || '#'}
                      target={src.url ? '_blank' : undefined}
                      rel="noreferrer"
                      title={src.snippet || src.title}
                      className="group flex flex-col justify-between p-2.5 rounded-xl bg-white/[0.03] hover:bg-white/[0.07] border border-white/[0.06] hover:border-indigo-500/30 transition shadow-sm"
                    >
                      <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                        <span className="flex items-center gap-1 font-mono text-indigo-300 truncate max-w-[120px]">
                          {src.source_type === 'web' ? (
                            <Globe className="w-2.5 h-2.5 shrink-0 text-emerald-400" />
                          ) : (
                            <FileText className="w-2.5 h-2.5 shrink-0 text-cyan-400" />
                          )}
                          <span className="truncate">{domain}</span>
                        </span>
                        {src.url && (
                          <ExternalLink className="w-2.5 h-2.5 text-slate-500 group-hover:text-indigo-400 transition" />
                        )}
                      </div>
                      <div className="text-xs font-medium text-slate-200 line-clamp-2 group-hover:text-white transition leading-snug">
                        {src.title}
                      </div>
                    </a>
                  );
                })}
              </div>
            </div>
          )}

          {/* Message Content Bubble */}
          <div
            className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
              isUser
                ? 'bg-gradient-to-r from-indigo-600 to-indigo-500 text-white rounded-tr-sm shadow-md shadow-indigo-600/20'
                : 'bg-white/[0.02] border border-white/[0.06] text-slate-200 rounded-tl-sm w-full shadow-sm'
            }`}
          >
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-[#07080c] prose-pre:border prose-pre:border-white/[0.08] prose-pre:rounded-xl">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ className, children, ...props }) {
                      return (
                        <code
                          className={`${
                            className || ''
                          } bg-[#0c0d14] text-indigo-300 px-1.5 py-0.5 rounded text-xs border border-white/[0.08] font-mono`}
                          {...props}
                        >
                          {children}
                        </code>
                      );
                    },
                    a({ href, children }) {
                      return (
                        <a
                          href={href}
                          target="_blank"
                          rel="noreferrer"
                          className="text-indigo-400 hover:text-indigo-300 underline underline-offset-2 inline-flex items-center gap-0.5"
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
            )}
          </div>

          {/* Action Row for Assistant Messages */}
          {!isUser && message.content && (
            <div className="flex items-center space-x-2 text-xs text-slate-400 pt-0.5">
              <button
                onClick={handleCopy}
                className="flex items-center space-x-1 px-2 py-1 rounded-lg hover:bg-white/[0.05] hover:text-slate-200 text-slate-400 transition"
                title="Copy response"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-[11px] text-emerald-400">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span className="text-[11px]">Copy</span>
                  </>
                )}
              </button>

              <button
                onClick={handlePlayVoice}
                disabled={isLoadingAudio}
                className={`flex items-center space-x-1 px-2 py-1 rounded-lg transition ${
                  isPlayingAudio
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                    : 'hover:bg-white/[0.05] hover:text-slate-200 text-slate-400'
                }`}
                title="Listen to this response via Neural TTS"
              >
                {isLoadingAudio ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                ) : (
                  <Volume2 className={`w-3.5 h-3.5 ${isPlayingAudio ? 'text-indigo-400 animate-pulse' : ''}`} />
                )}
                <span className="text-[11px]">
                  {isPlayingAudio ? 'Playing...' : isLoadingAudio ? 'Synthesizing...' : 'Speak'}
                </span>
              </button>
            </div>
          )}
        </div>

        {/* User Avatar */}
        {isUser && (
          <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0 text-slate-300 mt-1">
            <User className="w-4 h-4" />
          </div>
        )}
      </div>
    </div>
  );
};
