import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Bot,
  User,
  Copy,
  Check,
  FileText,
  Globe,
  Volume2,
  ChevronDown,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import type { ChatMessage, SourceItem } from '../types';

interface ChatMessageItemProps {
  message: ChatMessage;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [showSources, setShowSources] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={`py-4 px-4 md:px-6 flex gap-4 ${
        isUser ? 'bg-transparent justify-end' : 'bg-slate-900/40 border-y border-slate-900/60'
      }`}
    >
      <div className={`flex gap-3 max-w-4xl w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
        {/* Avatar */}
        {!isUser && (
          <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shrink-0 text-indigo-400 mt-0.5">
            <Bot className="w-4 h-4" />
          </div>
        )}

        <div className={`flex flex-col space-y-2 ${isUser ? 'items-end' : 'items-start'} max-w-3xl`}>
          {/* Header row */}
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <span className="font-semibold text-slate-300">
              {isUser ? 'You' : 'Assistant'}
            </span>
            <span>•</span>
            <span>{message.timestamp}</span>

            {/* Source Type Indicator Tag */}
            {!isUser && message.source_type && message.source_type !== 'direct' && (
              <span
                className={`flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full border ${
                  message.source_type === 'document'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                }`}
              >
                {message.source_type === 'document' ? (
                  <>
                    <FileText className="w-3 h-3" />
                    <span>Grounded in Local Docs</span>
                  </>
                ) : (
                  <>
                    <Globe className="w-3 h-3" />
                    <span>Live Web Search</span>
                  </>
                )}
              </span>
            )}
          </div>

          {/* Message Content Bubble */}
          <div
            className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
              isUser
                ? 'bg-indigo-600 text-white rounded-tr-sm shadow-md'
                : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-sm w-full shadow-sm'
            }`}
          >
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-slate-950 prose-pre:border prose-pre:border-slate-800 prose-pre:rounded-xl">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ className, children, ...props }) {
                      return (
                        <code
                          className={`${className || ''} bg-slate-950 text-indigo-300 px-1.5 py-0.5 rounded text-xs border border-slate-800`}
                          {...props}
                        >
                          {children}
                        </code>
                      );
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>

          {/* Sources Dropdown / Accordion */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="w-full mt-1">
              <button
                onClick={() => setShowSources(!showSources)}
                className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 font-medium py-1 transition"
              >
                {showSources ? (
                  <ChevronDown className="w-3.5 h-3.5" />
                ) : (
                  <ChevronRight className="w-3.5 h-3.5" />
                )}
                <span>
                  {message.sources.length} Referenced {message.source_type === 'document' ? 'Document Chunks' : 'Web Sources'}
                </span>
              </button>

              {showSources && (
                <div className="mt-2 space-y-2 border-l-2 border-indigo-500/40 pl-3">
                  {message.sources.map((src: SourceItem, idx: number) => (
                    <div
                      key={idx}
                      className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-2.5 text-xs text-slate-300"
                    >
                      <div className="flex items-center justify-between font-semibold text-indigo-300 mb-1">
                        <span className="truncate">{src.title}</span>
                        {src.url && (
                          <a
                            href={src.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-[11px] text-cyan-400 hover:underline shrink-0"
                          >
                            <span>Link</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                      {src.snippet && (
                        <p className="text-slate-400 text-[11px] leading-relaxed line-clamp-3">
                          {src.snippet}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Action Row for Assistant (Audio Player & Copy) */}
          {!isUser && (
            <div className="flex items-center space-x-3 pt-1">
              {message.audioUrl && (
                <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-2.5 py-1 rounded-full text-xs text-indigo-300">
                  <Volume2 className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
                  <audio controls src={message.audioUrl} autoPlay className="h-6 w-48" />
                </div>
              )}

              <button
                onClick={handleCopy}
                className="flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-300 transition"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
          )}
        </div>

        {/* Avatar for User */}
        {isUser && (
          <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0 text-slate-300 mt-0.5">
            <User className="w-4 h-4" />
          </div>
        )}
      </div>
    </div>
  );
};
