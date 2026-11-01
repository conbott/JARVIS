import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Square } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (text: string, isVoice: boolean) => void;
  isLoading: boolean;
  onStopGeneration?: () => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading,
  onStopGeneration,
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

  return (
    <div className="border-t border-slate-800 bg-slate-900/90 backdrop-blur-md p-4">
      <div className="max-w-4xl mx-auto flex items-end gap-2 bg-slate-950 border border-slate-800 rounded-2xl p-2 shadow-lg focus-within:border-indigo-500/50 transition">
        {/* Push-to-Talk Mic Button */}
        <button
          onClick={toggleSpeech}
          disabled={isLoading}
          title={isListening ? 'Stop Listening' : 'Push-to-Talk (Mic Input -> Voice Output)'}
          className={`p-2.5 rounded-xl transition shrink-0 ${
            isListening
              ? 'bg-rose-500 text-white animate-pulse shadow-md shadow-rose-500/30'
              : 'text-slate-400 hover:text-indigo-400 hover:bg-slate-900'
          }`}
        >
          {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
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
              : 'Ask anything, explore documents, or query live info...'
          }
          className="flex-1 bg-transparent border-0 text-sm text-slate-100 placeholder-slate-500 focus:ring-0 focus:outline-none resize-none py-2 px-1 max-h-44"
        />

        {/* Send / Stop Action */}
        {isLoading && onStopGeneration ? (
          <button
            onClick={onStopGeneration}
            title="Stop generation"
            className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-400 transition shrink-0"
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
                ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-600 bg-slate-900 cursor-not-allowed'
            }`}
          >
            <Send className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="max-w-4xl mx-auto flex items-center justify-between text-[11px] text-slate-500 mt-2 px-2">
        <span>Press <kbd className="bg-slate-800 text-slate-400 px-1 py-0.5 rounded">Enter</kbd> to send, <kbd className="bg-slate-800 text-slate-400 px-1 py-0.5 rounded">Shift+Enter</kbd> for new line</span>
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
          <span>Local Qwen 2.5 Coder + Qwen3 Embeddings</span>
        </span>
      </div>
    </div>
  );
};
