import React, { useState, useEffect } from 'react';
import {
  X,
  Cpu,
  Database,
  Cloud,
  Radio,
  Volume2,
  ShieldCheck,
  ChevronDown,
  Server,
  Sparkles,
  Copy,
  Check,
  RefreshCw,
} from 'lucide-react';
import type { HealthStatus, DocumentStats, VoiceOption, ModelInfo } from '../types';

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL
  ? (import.meta as any).env.VITE_API_BASE_URL.replace(/\/$/, '')
  : 'http://localhost:8000';

interface SystemPanelProps {
  isOpen: boolean;
  onClose: () => void;
  health: HealthStatus | null;
  stats: DocumentStats | null;
  selectedVoice: string;
  onSelectVoice?: (voiceId: string) => void;
  availableVoices: VoiceOption[];
  onRefreshHealth?: () => void;
}

export const SystemPanel: React.FC<SystemPanelProps> = ({
  isOpen,
  onClose,
  health,
  stats,
  selectedVoice,
  onSelectVoice,
  availableVoices,
  onRefreshHealth,
}) => {
  const [installedModels, setInstalledModels] = useState<ModelInfo[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [switchingModel, setSwitchingModel] = useState(false);
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    const fetchModels = async () => {
      setLoadingModels(true);
      try {
        const res = await fetch(`${API_BASE}/api/models`);
        if (res.ok) {
          const data = await res.json();
          const models: ModelInfo[] = (data.installed_models || []).filter(
            (m: ModelInfo) => !m.name.toLowerCase().includes('embed')
          );
          setInstalledModels(models);
        }
      } catch (err) {
        console.error('Failed to fetch installed models:', err);
      } finally {
        setLoadingModels(false);
      }
    };
    fetchModels();
  }, [isOpen]);

  if (!isOpen) return null;

  const hardware = health?.device_info?.device_name || 'Dynamic Hardware Detection';
  const vram = health?.device_info?.vram_gb ? `${health.device_info.vram_gb} GB` : 'System RAM';
  const isGpu = health?.device_info?.is_gpu ?? true;
  const vramGb = health?.device_info?.vram_gb;
  const chunkCount = stats?.total_chunks ?? 0;
  const isHosted = health?.hosted || (health?.provider && health.provider !== 'ollama');
  const providerName = health?.provider || 'ollama';
  const modelName = health?.model || health?.llm_model || 'qwen2.5-coder:7b';
  const vectorBackend = health?.vector_backend || 'chroma';

  // Smart Hardware Recommendation
  let recModel = 'qwen2.5-coder:7b';
  let recDesc = '7B params · Best balance of reasoning, coding, and speed for 6GB–10GB VRAM.';
  if (!isGpu || (vramGb !== null && vramGb !== undefined && vramGb < 6)) {
    recModel = 'llama3.2:3b';
    recDesc = '3B params · Ultra-lightweight & fast, tailored for CPU or entry GPUs (<6GB VRAM).';
  } else if (vramGb !== null && vramGb !== undefined && vramGb >= 12) {
    recModel = 'qwen2.5-coder:14b';
    recDesc = '14B params · Advanced deep reasoning & code generation for 12GB+ GPUs.';
  }
  const pullCmd = `ollama pull ${recModel}`;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCmd(text);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  const handleSelectModel = async (newModel: string) => {
    if (!newModel || newModel === modelName || switchingModel) return;
    setSwitchingModel(true);
    try {
      const res = await fetch(`${API_BASE}/api/models/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: newModel }),
      });
      if (res.ok) {
        onRefreshHealth?.();
      }
    } catch (err) {
      console.error('Failed to switch model:', err);
    } finally {
      setSwitchingModel(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      {/* Drawer using --color-surface */}
      <div className="relative w-84 max-w-full bg-[var(--color-surface)] border-l border-[var(--color-border)] p-6 flex flex-col justify-between shadow-2xl z-10 overflow-y-auto font-sans">
        <div>
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-[var(--color-border)]">
            <h2 className="text-sm font-semibold text-[var(--color-text)] flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[var(--color-accent)]" />
              <span>System & Environment</span>
            </h2>
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-[var(--color-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-2)] transition cursor-pointer"
              title="Close panel"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="mt-5 space-y-6 text-xs">
            {/* Compute & Runtime Engine */}
            <div>
              <div className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-muted)] mb-2">
                Compute Engine
              </div>
              <div className="p-3 rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border)] space-y-2">
                {isHosted ? (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                        <Server className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                        Runtime Mode
                      </span>
                      <span className="font-mono text-[var(--color-text)] text-[11px] text-right truncate">
                        API · {providerName} · {modelName}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[var(--color-muted)]">Provider</span>
                      <span className="font-mono text-[var(--color-accent)] text-[11px] font-medium capitalize">
                        {providerName} Hosted API
                      </span>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                        <Cpu className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                        Device
                      </span>
                      <span className="font-mono text-[var(--color-text)] text-[11px] text-right truncate max-w-[160px]">
                        {hardware}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[var(--color-muted)]">Memory Allocation</span>
                      <span className="font-mono text-[var(--color-text)] text-[11px]">{vram}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[var(--color-muted)]">Acceleration</span>
                      <span className="text-[11px] text-[var(--color-accent)] font-medium">
                        {isGpu ? 'NVIDIA CUDA (Active)' : 'CPU Direct'}
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Model & Embeddings */}
            <div>
              <div className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-muted)] mb-2">
                Language & Embeddings
              </div>
              <div className="p-3 rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border)] space-y-3">
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                      <Radio className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                      Active LLM
                    </span>
                    {(switchingModel || loadingModels) && (
                      <span className="text-[10px] text-[var(--color-accent)] flex items-center gap-1 animate-pulse">
                        <RefreshCw className="w-3 h-3 animate-spin" /> {switchingModel ? 'Switching...' : 'Scanning...'}
                      </span>
                    )}
                  </div>
                  {installedModels.length > 0 ? (
                    <div className="relative">
                      <select
                        value={modelName}
                        onChange={(e) => handleSelectModel(e.target.value)}
                        disabled={switchingModel}
                        className="w-full appearance-none bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text)] text-xs rounded-lg px-3 py-2 pr-8 focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)] cursor-pointer disabled:opacity-50"
                      >
                        {installedModels.map((m) => (
                          <option key={m.name} value={m.name} className="bg-[var(--color-surface)] text-[var(--color-text)]">
                            {m.name} {m.size_gb > 0 ? `(${m.size_gb} GB)` : ''}
                          </option>
                        ))}
                      </select>
                      <ChevronDown className="w-3.5 h-3.5 text-[var(--color-muted)] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                    </div>
                  ) : (
                    <div className="font-mono text-[var(--color-text)] text-xs px-2.5 py-1.5 bg-[var(--color-surface)] rounded-lg border border-[var(--color-border)]">
                      {modelName}
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between pt-1 border-t border-[var(--color-border)]/60">
                  <span className="text-[var(--color-muted)]">Embeddings</span>
                  <span className="font-mono text-[var(--color-text)] text-[11px] truncate max-w-[160px]">
                    {health?.embedding_model || 'qwen3-embedding:0.6b'}
                  </span>
                </div>
              </div>
            </div>

            {/* Smart Hardware Model Recommendation (Local Ollama mode only) */}
            {!isHosted && (
              <div>
                <div className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-muted)] mb-2 flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-[var(--color-accent)]" />
                  <span>Hardware Guide & Recommendations</span>
                </div>
                <div className="p-3 rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border)] space-y-2.5">
                  <div className="text-[11px] text-[var(--color-text)] leading-relaxed">
                    <span className="font-semibold text-[var(--color-accent)]">{recModel}</span>
                    <p className="text-[10px] text-[var(--color-muted)] mt-0.5">{recDesc}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 bg-[var(--color-surface)] text-[var(--color-text)] px-2 py-1.5 rounded-md text-[10.5px] font-mono border border-[var(--color-border)] truncate select-all">
                      {pullCmd}
                    </code>
                    <button
                      onClick={() => copyToClipboard(pullCmd)}
                      className="p-1.5 rounded-md bg-[var(--color-surface)] hover:bg-[var(--color-surface-2)] border border-[var(--color-border)] text-[var(--color-muted)] hover:text-[var(--color-text)] transition cursor-pointer shrink-0"
                      title="Copy pull command"
                    >
                      {copiedCmd === pullCmd ? (
                        <Check className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                  <p className="text-[10px] text-[var(--color-muted)] leading-tight">
                    Run in your terminal. Once downloaded, it appears in the model dropdown above automatically!
                  </p>
                </div>
              </div>
            )}

            {/* Vector Storage */}
            <div>
              <div className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-muted)] mb-2">
                Knowledge Stores
              </div>
              <div className="p-3 rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border)] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                    <Database className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                    Primary Backend
                  </span>
                  <span className="font-mono text-[var(--color-text)] text-[11px] font-medium capitalize">
                    {vectorBackend === 'pinecone' ? 'Pinecone (Cloud)' : 'ChromaDB (Local)'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[var(--color-muted)]">Indexed Chunks</span>
                  <span className="font-mono text-[var(--color-text)] text-[11px]">
                    {chunkCount} {chunkCount === 1 ? 'Chunk' : 'Chunks'}
                  </span>
                </div>
                {vectorBackend !== 'pinecone' && (
                  <div className="flex items-center justify-between">
                    <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                      <Cloud className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                      Pinecone Sync Target
                    </span>
                    <span className="font-mono text-[var(--color-text)] text-[11px]">
                      {health?.cloud_sync_target?.index || 'attention-paper'}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Neural Voice Selector */}
            <div>
              <div className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-muted)] mb-2">
                Neural Voice (TTS)
              </div>
              <div className="p-3 rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border)] space-y-2">
                <label className="text-[11px] text-[var(--color-muted)] flex items-center gap-1.5">
                  <Volume2 className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                  Select Voice
                </label>
                <div className="relative">
                  <select
                    value={selectedVoice}
                    onChange={(e) => onSelectVoice && onSelectVoice(e.target.value)}
                    className="w-full appearance-none bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text)] text-xs rounded-lg px-3 py-2 pr-8 focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)] cursor-pointer"
                  >
                    {availableVoices.map((v) => (
                      <option key={v.id} value={v.id} className="bg-[var(--color-surface)] text-[var(--color-text)]">
                        {v.name}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="w-3.5 h-3.5 text-[var(--color-muted)] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
                <p className="text-[10px] text-[var(--color-muted)] leading-normal pt-1">
                  Edge-TTS synthesis running asynchronously on CPU with 0 MB GPU overhead.
                </p>
              </div>
            </div>

            {/* Retrieval Pipeline */}
            <div>
              <div className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-muted)] mb-2">
                Retrieval Pipeline
              </div>
              <div className="p-3 rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border)] text-[11px] text-[var(--color-muted)] leading-relaxed space-y-1.5">
                <p>
                  <span className="text-[var(--color-text)] font-medium">Smart RAG:</span> Checks {vectorBackend === 'pinecone' ? 'Pinecone' : 'ChromaDB'} cosine similarity threshold (0.35).
                </p>
                <p>
                  <span className="text-[var(--color-warn)] font-medium">Fallback:</span> Automatically switches to live DuckDuckGo web search if document confidence is low or real-time external info is needed.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-6 border-t border-[var(--color-border)] flex items-center justify-between text-[11px] text-[var(--color-muted)]">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-[var(--color-accent)]" />
            {isHosted ? `Hosted API (${providerName})` : 'Local-First Private Execution'}
          </span>
          <span className="font-mono">v2.0</span>
        </div>
      </div>
    </div>
  );
};
