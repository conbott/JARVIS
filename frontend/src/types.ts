export interface SourceItem {
  title: string;
  url?: string;
  domain?: string;
  filename?: string;
  page?: number | null;
  snippet?: string;
  source_type: 'document' | 'web' | 'direct';
  score?: number; // Normalized cosine similarity [0.0, 1.0]
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  source_type?: 'document' | 'web' | 'direct';
  path?: 'document' | 'web' | 'direct';
  retrieval?: 'spread' | 'similarity' | null;
  fallback_reason?: 'low_confidence' | 'empty_store' | 'realtime_query' | 'forced_web' | null;
  best_score?: number | null;
  threshold?: number;
  sources?: SourceItem[];
  audioUrl?: string;
  timestamp: string;
  statusMessage?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  messages: ChatMessage[];
}

export interface DocumentStats {
  total_chunks: number;
  document_count: number;
  documents: string[];
  error?: string;
}

export interface DeviceInfo {
  device_name: string;
  device_type: string;
  is_gpu: boolean;
  vram_gb?: number | null;
}

export interface HealthStatus {
  status: string;
  provider?: string;
  model?: string;
  embedding_provider?: string;
  vector_backend?: string;
  stt_enabled?: boolean;
  hosted?: boolean;
  ollama_online: boolean;
  llm_model: string;
  embedding_model: string;
  device_info?: DeviceInfo;
  vector_store: {
    type: string;
    total_chunks: number;
    documents: string[];
    collection?: string;
  };
  cloud_sync_target: {
    type: string;
    index: string;
    configured: boolean;
  };
}

export interface ModelInfo {
  name: string;
  size_gb: number;
  parameter_size: string;
  quantization: string;
  family: string;
}

export interface ModelsResponse {
  current_llm: string;
  current_embedding: string;
  installed_models: ModelInfo[];
}

export type SearchMode = 'auto' | 'web' | 'docs';

export interface VoiceOption {
  id: string;
  name: string;
  gender: string;
  accent: string;
}
