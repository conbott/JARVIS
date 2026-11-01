import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Square, Globe, FileText, Sparkles } from 'lucide-react';
import type { HealthStatus, SearchMode } from '../types';

interface ChatInputProps {
  onSendMessage: (text: string, isVoice: boolean) => void;
  isLoading: boolean;
  onStopGeneration?: () => void;
  searchMode: SearchMode;
  onSearchModeChange: (mode: SearchMode) => void;
  health: HealthStatus | null;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading,
  onStopGeneration,
  searchMode,
  onSearchModeChange,
  health,
}) => {
  const [text, setText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Setup Web Speech API if supported in browser
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript.trim()) {
          onSendMessage(transcript.trim(), true);
        }
        setIsListening(false);
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, [onSendMessage]);

  const toggleSpeech = () => {
    if (!recognitionRef.current) {
      alert('Speech Recognition is not supported in this browser. Please use Google Chrome or Edge.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      setIsListening(true);
      recognitionRef.current.start();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if (!text.trim() || isLoading) return;
    onSendMessage(text.trim(), false);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  // Auto-resize textarea
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 180)}px`;
  };

  const modelDisplay = health?.llm_model || 'Local LLM';
  const hardwareDisplay = health?.device_info?.device_name || 'Hardware System';

  return (
    <div className="border-t border-white/[0.06] bg-[#08090d]/80 backdrop-blur-xl p-4">
      {/* Search Mode Pill Group */}
      <div className="max-w-4xl mx-auto flex items-center justify-between mb-2.5 px-1">
        <div className="flex items-center gap-1.5 bg-[#0e1017] p-1 rounded-xl border border-white/[0.06] text-xs shadow-inner">
          <button
            type="button"
            onClick={() => onSearchModeChange('auto')}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-medium transition ${
              searchMode === 'auto'
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
            }`}
            title="Smart RAG: Checks uploaded documents first, falls back to Web Search if confidence is low"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Auto (Smart RAG)</span>
          </button>

          <button
            type="button"
            onClick={() => onSearchModeChange('web')}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-medium transition ${
              searchMode === 'web'
                ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
            }`}
            title="Force Live Web Search: Query DuckDuckGo directly for real-time live information"
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Live Web Search</span>
          </button>

          <button
            type="button"
            onClick={() => onSearchModeChange('docs')}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-medium transition ${
              searchMode === 'docs'
                ? 'bg-cyan-600 text-white shadow-sm shadow-cyan-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
            }`}
            title="Documents Only: Restrict answers strictly to uploaded ChromaDB documents"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Documents Only</span>
          </button>
        </div>

        {/* Dynamic Model & Hardware Badge */}
        <div className="hidden sm:flex items-center gap-2 text-[11px] text-slate-400 font-mono">
          <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-white/[0.03] border border-white/[0.05]">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span className="text-slate-300">{modelDisplay}</span>
          </span>
        </div>
      </div>

      {/* Main Input Floating Bar */}
      <div className="max-w-4xl mx-auto flex items-end gap-2 bg-[#0c0d14] border border-white/[0.08] focus-within:border-indigo-500/50 rounded-2xl p-2 shadow-2xl shadow-black/50 transition">
        {/* Push-to-Talk Mic Button */}
        <button
          onClick={toggleSpeech}
          disabled={isLoading}
          title={isListening ? 'Stop Listening' : 'Push-to-Talk (Mic Input -> Voice Output)'}
          className={`p-2.5 rounded-xl transition shrink-0 relative ${
            isListening
              ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/30 animate-pulse'
              : 'text-slate-400 hover:text-indigo-400 hover:bg-white/[0.05]'
          }`}
        >
          {isListening ? (
            <div className="flex items-center gap-1">
              <span className="w-1 h-3 bg-white animate-bounce" />
              <span className="w-1 h-4 bg-white animate-bounce [animation-delay:0.1s]" />
              <span className="w-1 h-2 bg-white animate-bounce [animation-delay:0.2s]" />
            </div>
          ) : (
            <Mic className="w-4 h-4" />
          )}
        </button>

        {/* Text Area */}
        <textarea
          ref={textareaRef}
          rows={1}
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={
            isListening
              ? 'Listening to your voice... (speak clearly)'
              : searchMode === 'web'
              ? 'Search live internet data with DuckDuckGo (e.g. current releases, stock prices, news)...'
              : searchMode === 'docs'
              ? 'Ask questions strictly grounded in your uploaded documents...'
              : 'Ask anything, query uploaded documents, or search the live web...'
          }
          className="flex-1 bg-transparent border-0 text-sm text-slate-100 placeholder-slate-500 focus:ring-0 focus:outline-none resize-none py-2 px-1 max-h-44"
        />

        {/* Send / Stop Action */}
        {isLoading && onStopGeneration ? (
          <button
            onClick={onStopGeneration}
            title="Stop generation"
            className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 hover:bg-amber-500/20 text-amber-400 transition shrink-0"
          >
            <Square className="w-4 h-4 fill-amber-400" />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!text.trim() || isLoading}
            title="Send Message"
            className={`p-2.5 rounded-xl transition shrink-0 ${
              text.trim() && !isLoading
                ? 'bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-600 bg-white/[0.02] cursor-not-allowed'
            }`}
          >
            <Send className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="max-w-4xl mx-auto flex items-center justify-between text-[11px] text-slate-500 mt-2 px-2">
        <span>
          Press <kbd className="bg-white/[0.05] border border-white/[0.08] text-slate-300 px-1 py-0.5 rounded font-mono text-[10px]">Enter</kbd> to send, <kbd className="bg-white/[0.05] border border-white/[0.08] text-slate-300 px-1 py-0.5 rounded font-mono text-[10px]">Shift+Enter</kbd> for newline
        </span>
        <span className="flex items-center gap-1.5 text-slate-400 font-mono text-[10px]">
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
          <span>{hardwareDisplay}</span>
        </span>
      </div>
    </div>
  );
};
