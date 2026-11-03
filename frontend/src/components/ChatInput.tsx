import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Mic,
  Square,
  Globe,
  FileText,
  Sparkles,
  X,
  Check,
  Loader2,
} from 'lucide-react';
import type { SearchMode, DocumentStats } from '../types';

interface ChatInputProps {
  onSendMessage: (text: string, isVoice: boolean) => void;
  isLoading: boolean;
  onStopGeneration?: () => void;
  searchMode: SearchMode;
  onSearchModeChange: (mode: SearchMode) => void;
  onStopAudio?: () => void;
  stats?: DocumentStats | null;
  sttEnabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading,
  onStopGeneration,
  searchMode,
  onSearchModeChange,
  onStopAudio,
  stats,
  sttEnabled = true,
}) => {
  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isFocused, setIsFocused] = useState(false);

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
    if (onStopAudio) {
      onStopAudio();
    }

    try {
      audioChunksRef.current = [];
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream;

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
        if (audioStreamRef.current) {
          audioStreamRef.current.getTracks().forEach((t) => t.stop());
          audioStreamRef.current = null;
        }

        const mime = recorder.mimeType || 'audio/webm';
        const audioBlob = new Blob(audioChunksRef.current, { type: mime });

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
        'Could not access microphone. Please ensure microphone permissions are granted in your browser settings.'
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
        // Send message with isVoice = true so response auto-plays
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

  const docCount = stats?.document_count ?? 0;
  const chunkCount = stats?.total_chunks ?? 0;

  return (
    <div className="w-full max-w-[720px] mx-auto px-4 md:px-0">
      {/* Attached Documents Chips */}
      {docCount > 0 && stats?.documents && (
        <div className="flex items-center gap-1.5 mb-2 overflow-x-auto py-1 text-xs text-[var(--color-muted)] font-sans">
          <span className="text-[11px] shrink-0">Attached:</span>
          {stats.documents.slice(0, 3).map((doc, idx) => (
            <span
              key={idx}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[var(--color-surface)] border border-[var(--color-border)] text-[11px] font-mono text-[var(--color-text)] truncate max-w-[180px]"
            >
              <FileText className="w-2.5 h-2.5 text-[var(--color-accent)] shrink-0" />
              <span className="truncate">{doc}</span>
            </span>
          ))}
          {stats.documents.length > 3 && (
            <span className="text-[10px] text-[var(--color-muted)] font-mono">
              +{stats.documents.length - 3} more
            </span>
          )}
          <span className="text-[10px] text-[var(--color-muted)] font-mono ml-auto shrink-0">
            {chunkCount} {chunkCount === 1 ? 'chunk' : 'chunks'}
          </span>
        </div>
      )}

      {/* Main Floating Box using --color-surface */}
      <div
        className={`relative rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-3 transition-all shadow-sm ${
          isFocused ? 'ring-1 ring-[var(--color-accent)]/60 border-[var(--color-accent)]/40' : ''
        }`}
      >
        {/* Recording Waveform State */}
        {isRecording ? (
          <div className="flex items-center justify-between py-2 px-1 text-sm font-sans">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1 h-5">
                <span className="w-1 h-3 bg-[var(--color-accent)] rounded-full animate-pulse" />
                <span className="w-1 h-5 bg-[var(--color-accent)] rounded-full animate-pulse delay-75" />
                <span className="w-1 h-2 bg-[var(--color-accent)] rounded-full animate-pulse delay-150" />
                <span className="w-1 h-4 bg-[var(--color-accent)] rounded-full animate-pulse delay-200" />
              </div>
              <span className="text-xs text-[var(--color-text)] font-medium">
                Listening... ({formatTime(recordingDuration)})
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={cancelRecording}
                className="p-1.5 rounded-lg text-[var(--color-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-2)] transition text-xs cursor-pointer"
                title="Cancel recording"
              >
                <X className="w-4 h-4" />
              </button>
              <button
                onClick={stopRecording}
                className="px-3 py-1 rounded-lg bg-[var(--color-accent)] text-[var(--color-accent-fg)] text-xs font-medium hover:opacity-90 transition flex items-center gap-1 cursor-pointer"
                title="Finish recording and transcribe"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Send</span>
              </button>
            </div>
          </div>
        ) : isTranscribing ? (
          <div className="flex items-center gap-2 py-2 px-1 text-xs text-[var(--color-muted)] font-sans">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-[var(--color-accent)]" />
            <span>Transcribing with local Whisper...</span>
          </div>
        ) : (
          /* Normal Textarea Row */
          <div className="flex items-end gap-2">
            {/* Mic Push-to-Talk Button (hidden when STT is disabled) */}
            {sttEnabled !== false && (
              <button
                onClick={toggleMic}
                disabled={isLoading}
                title="Speak message (Whisper STT)"
                className="p-2 rounded-xl text-[var(--color-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-2)] transition shrink-0 cursor-pointer disabled:opacity-40"
              >
                <Mic className="w-4 h-4" />
              </button>
            )}

            {/* Auto-resizing Textarea */}
            <textarea
              ref={textareaRef}
              value={text}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="Ask anything, query your documents, or search the web..."
              rows={1}
              className="flex-1 bg-transparent text-[var(--color-text)] placeholder-[var(--color-muted)] text-sm font-sans leading-relaxed focus:outline-none resize-none max-h-44 py-1.5"
            />

            {/* Send / Stop Button: Solid Accent Fill */}
            {isLoading ? (
              <button
                onClick={onStopGeneration}
                title="Stop generation"
                className="w-8 h-8 rounded-full bg-[var(--color-surface-2)] text-[var(--color-text)] border border-[var(--color-border)] flex items-center justify-center hover:bg-[var(--color-surface)] transition shrink-0 cursor-pointer"
              >
                <Square className="w-3 h-3 fill-current" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={!text.trim()}
                title="Send message"
                className="w-8 h-8 rounded-full bg-[var(--color-accent)] text-[var(--color-accent-fg)] flex items-center justify-center hover:opacity-90 transition disabled:opacity-20 disabled:cursor-not-allowed shrink-0 cursor-pointer shadow-xs"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}

        {/* Bottom Control Bar: Segmented Search Mode Control + Focus Hint */}
        <div className="flex items-center justify-between pt-2.5 mt-2 border-t border-[var(--color-border)]">
          {/* Segmented Control */}
          <div className="flex items-center p-0.5 rounded-lg bg-[var(--color-surface-2)] border border-[var(--color-border)] text-xs">
            <button
              onClick={() => onSearchModeChange('auto')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-sans transition cursor-pointer ${
                searchMode === 'auto'
                  ? 'bg-[var(--color-accent-soft)] text-[var(--color-accent)] font-medium'
                  : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'
              }`}
              title="Smart RAG: automatically searches documents or falls back to web"
            >
              <Sparkles className="w-3 h-3" />
              <span>Auto</span>
            </button>

            <button
              onClick={() => onSearchModeChange('web')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-sans transition cursor-pointer ${
                searchMode === 'web'
                  ? 'bg-[var(--color-accent-soft)] text-[var(--color-accent)] font-medium'
                  : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'
              }`}
              title="Force live web search"
            >
              <Globe className="w-3 h-3" />
              <span>Web</span>
            </button>

            <button
              onClick={() => onSearchModeChange('docs')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-sans transition cursor-pointer ${
                searchMode === 'docs'
                  ? 'bg-[var(--color-accent-soft)] text-[var(--color-accent)] font-medium'
                  : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'
              }`}
              title="Force query only uploaded documents"
            >
              <FileText className="w-3 h-3" />
              <span>Docs</span>
            </button>
          </div>

          {/* Single muted Enter hint, visible on focus */}
          <div
            className={`text-[10px] text-[var(--color-muted)] font-mono transition-opacity duration-150 ${
              isFocused ? 'opacity-80' : 'opacity-0'
            }`}
          >
            Enter to send · Shift+Enter for new line
          </div>
        </div>
      </div>
    </div>
  );
};
