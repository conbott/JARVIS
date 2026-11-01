import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Square, Globe, FileText, Sparkles, X, Check, Loader2 } from 'lucide-react';
import type { HealthStatus, SearchMode } from '../types';

interface ChatInputProps {
  onSendMessage: (text: string, isVoice: boolean) => void;
  isLoading: boolean;
  onStopGeneration?: () => void;
  searchMode: SearchMode;
  onSearchModeChange: (mode: SearchMode) => void;
  health: HealthStatus | null;
  onStopAudio?: () => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading,
  onStopGeneration,
  searchMode,
  onSearchModeChange,
  health,
  onStopAudio,
}) => {
  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [isTranscribing, setIsTranscribing] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<any>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Clean up recording streams on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const startRecording = async () => {
    // If any audio response is currently playing, stop it so it doesn't leak into the mic
    if (onStopAudio) {
      onStopAudio();
    }

    try {
      audioChunksRef.current = [];
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream;

      // Determine best supported mime type
      const mimeType = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/mp4',
      ].find((type) => MediaRecorder.isTypeSupported(type)) || '';

      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        // Clean up mic track stream
        if (audioStreamRef.current) {
          audioStreamRef.current.getTracks().forEach((t) => t.stop());
          audioStreamRef.current = null;
        }

        const mime = recorder.mimeType || 'audio/webm';
        const audioBlob = new Blob(audioChunksRef.current, { type: mime });

        // If audio blob is tiny (< 1000 bytes, likely just click noise), skip
        if (audioBlob.size < 1000) {
          setIsRecording(false);
          return;
        }

        await processTranscription(audioBlob, mime);
      };

      recorder.start(250);
      setIsRecording(true);
      setRecordingDuration(0);

      timerRef.current = setInterval(() => {
        setRecordingDuration((prev) => prev + 1);
      }, 1000);
    } catch (err: any) {
      console.error('Microphone access error:', err);
      alert(
        'Could not access microphone. Please ensure microphone permissions are granted in your browser settings (Opera GX / Chrome / Edge).'
      );
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  };

  const cancelRecording = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach((t) => t.stop());
      audioStreamRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.ondataavailable = null;
      mediaRecorderRef.current.onstop = null;
      mediaRecorderRef.current.stop();
    }

    audioChunksRef.current = [];
    setIsRecording(false);
    setRecordingDuration(0);
  };

  const processTranscription = async (blob: Blob, mimeType: string) => {
    setIsTranscribing(true);
    try {
      const ext = mimeType.includes('ogg') ? 'ogg' : mimeType.includes('mp4') ? 'mp4' : 'webm';
      const formData = new FormData();
      formData.append('audio', blob, `speech.${ext}`);

      const res = await fetch('/api/voice/transcribe', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`STT failed (HTTP ${res.status})`);
      }

      const data = await res.json();
      if (data.text && data.text.trim()) {
        onSendMessage(data.text.trim(), true);
      } else {
        console.warn('Whisper STT: No speech detected.');
      }
    } catch (err) {
      console.error('Whisper transcription error:', err);
      alert('Speech transcription encountered an error. Please try speaking again.');
    } finally {
      setIsTranscribing(false);
      setRecordingDuration(0);
    }
  };

  const toggleMic = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if (isRecording) {
      stopRecording();
      return;
    }
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

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
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
      <div className="max-w-4xl mx-auto flex items-end gap-2 bg-[#0c0d14] border border-white/[0.08] focus-within:border-indigo-500/50 rounded-2xl p-2 shadow-2xl shadow-black/50 transition relative">
        {/* Recording Overlay banner if recording or transcribing */}
        {isRecording && (
          <div className="absolute inset-x-2 top-2 bottom-2 bg-[#12141e] rounded-xl flex items-center justify-between px-3 border border-rose-500/30 z-20 shadow-xl">
            <div className="flex items-center space-x-3">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500" />
              </span>
              <span className="text-xs font-semibold text-rose-300 font-mono">
                Recording... {formatTime(recordingDuration)}
              </span>
              {/* Dynamic waveform visualizer bars */}
              <div className="hidden sm:flex items-center space-x-0.5">
                <span className="w-1 h-3 bg-rose-400 animate-pulse" />
                <span className="w-1 h-5 bg-rose-400 animate-pulse delay-75" />
                <span className="w-1 h-2 bg-rose-400 animate-pulse delay-150" />
                <span className="w-1 h-6 bg-rose-400 animate-pulse delay-100" />
                <span className="w-1 h-4 bg-rose-400 animate-pulse delay-200" />
              </div>
              <span className="hidden md:inline text-[11px] text-slate-400">
                (Click Stop or Check to transcribe with Whisper)
              </span>
            </div>

            <div className="flex items-center space-x-1.5">
              <button
                type="button"
                onClick={cancelRecording}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.08] transition"
                title="Discard audio"
              >
                <X className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={stopRecording}
                className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-md shadow-rose-600/30 transition"
                title="Done speaking, send to Whisper"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Send</span>
              </button>
            </div>
          </div>
        )}

        {isTranscribing && (
          <div className="absolute inset-x-2 top-2 bottom-2 bg-[#12141e] rounded-xl flex items-center justify-center space-x-2.5 px-3 border border-indigo-500/30 z-20 shadow-xl">
            <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
            <span className="text-xs font-medium text-indigo-200">
              Transcribing audio with faster-whisper (CPU INT8)...
            </span>
          </div>
        )}

        {/* Push-to-Talk Mic Button */}
        <button
          onClick={toggleMic}
          disabled={isLoading || isTranscribing}
          title={isRecording ? 'Finish Speaking' : 'Push-to-Talk (Record Voice -> Whisper STT)'}
          className={`p-2.5 rounded-xl transition shrink-0 relative ${
            isRecording
              ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/30'
              : 'text-slate-400 hover:text-indigo-400 hover:bg-white/[0.05]'
          }`}
        >
          <Mic className="w-4 h-4" />
        </button>

        {/* Text Area */}
        <textarea
          ref={textareaRef}
          rows={1}
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={
            searchMode === 'web'
              ? 'Search live internet data with DuckDuckGo (e.g. current releases, news, facts)...'
              : searchMode === 'docs'
              ? 'Ask questions strictly grounded in your uploaded documents...'
              : 'Ask anything, query uploaded documents, or speak with push-to-talk mic...'
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
