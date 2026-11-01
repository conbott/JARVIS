export interface SourceItem {
  title: string;
  url?: string;
  snippet?: string;
  source_type: 'document' | 'web' | 'direct';
  score?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  source_type?: 'document' | 'web' | 'direct';
  sources?: SourceItem[];
  audioUrl?: string;
  timestamp: string;
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
  ollama_online: boolean;
  llm_model: string;
  embedding_model: string;
  device_info?: DeviceInfo;
  vector_store: {
    type: string;
    total_chunks: number;
    documents: string[];
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
