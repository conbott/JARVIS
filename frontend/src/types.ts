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

export interface HealthStatus {
  status: string;
  ollama_online: boolean;
  llm_model: string;
  embedding_model: string;
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
