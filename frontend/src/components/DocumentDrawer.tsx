import React, { useState, useRef } from 'react';
import {
  X,
  UploadCloud,
  FileText,
  Cloud,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import type { DocumentStats } from '../types';

interface DocumentDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  stats: DocumentStats | null;
  onRefreshStats: () => void;
}

export const DocumentDrawer: React.FC<DocumentDrawerProps> = ({
  isOpen,
  onClose,
  stats,
  onRefreshStats,
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [indexName, setIndexName] = useState('attention-paper');
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setFeedback(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      setFeedback({
        type: 'success',
        text: `Indexed "${data.filename}" into ChromaDB (${data.chunks_added} chunks).`,
      });
      onRefreshStats();
    } catch (err: any) {
      setFeedback({
        type: 'error',
        text: err.message || 'Error uploading file',
      });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleSyncPinecone = async () => {
    setIsSyncing(true);
    setFeedback(null);

    try {
      const res = await fetch('/api/documents/sync-pinecone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: apiKey || undefined,
          index_name: indexName || undefined,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Pinecone sync failed');
      }

      setFeedback({
        type: 'success',
        text: data.message || `Successfully synced ${data.synced_count} vectors to Pinecone!`,
      });
    } catch (err: any) {
      setFeedback({
        type: 'error',
        text: err.message || 'Pinecone sync failed',
      });
    } finally {
      setIsSyncing(false);
    }
  };

  const handleClearDocuments = async () => {
    if (!confirm('Are you sure you want to clear all local documents from ChromaDB?')) return;

    try {
      const res = await fetch('/api/documents/clear', { method: 'DELETE' });
      if (res.ok) {
        setFeedback({ type: 'success', text: 'Local ChromaDB collection cleared.' });
        onRefreshStats();
      }
    } catch (err: any) {
      setFeedback({ type: 'error', text: 'Failed to clear documents' });
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm transition-opacity">
      <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 h-full flex flex-col shadow-2xl p-6 overflow-y-auto">
        {/* Drawer Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 text-indigo-400 flex items-center justify-center">
              <FileText className="w-4 h-4" />
            </div>
            <h2 className="text-base font-bold text-white">Knowledge Base & Sync</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Feedback Alert */}
        {feedback && (
          <div
            className={`mt-4 p-3 rounded-xl border flex items-start gap-2.5 text-xs ${
              feedback.type === 'success'
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
                : 'bg-rose-500/10 border-rose-500/20 text-rose-300'
            }`}
          >
            {feedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            )}
            <p className="leading-relaxed">{feedback.text}</p>
          </div>
        )}

        {/* Section 1: Upload Documents to Local ChromaDB */}
        <div className="mt-6">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            1. Ingest Documents (Local ChromaDB)
          </h3>

          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-700 hover:border-indigo-500/60 rounded-2xl p-6 text-center cursor-pointer transition bg-slate-950/40 hover:bg-slate-950/70 group"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.md"
              onChange={handleFileUpload}
              className="hidden"
            />
            {isUploading ? (
              <div className="flex flex-col items-center justify-center py-2 space-y-2">
                <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
                <span className="text-xs text-slate-300 font-medium">Extracting & Embedding Chunks...</span>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center space-y-2">
                <div className="w-12 h-12 rounded-full bg-indigo-500/10 group-hover:bg-indigo-500/20 text-indigo-400 flex items-center justify-center transition">
                  <UploadCloud className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-200">
                    Click or drag PDF / TXT / MD
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Chunked & stored offline in local ChromaDB
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Section 2: Indexed Documents List */}
        <div className="mt-6 flex-1">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Indexed Files ({stats?.document_count ?? 0})
            </h3>
            <button
              onClick={onRefreshStats}
              title="Refresh"
              className="text-slate-500 hover:text-slate-300 transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="bg-slate-950 rounded-xl border border-slate-800 p-3 max-h-48 overflow-y-auto space-y-1.5">
            {stats && stats.documents.length > 0 ? (
              stats.documents.map((doc, i) => (
                <div
                  key={i}
                  className="flex items-center space-x-2 text-xs text-slate-300 py-1 px-2 rounded hover:bg-slate-900 transition"
                >
                  <FileText className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                  <span className="truncate flex-1 font-medium">{doc}</span>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-600 text-center py-4">
                No documents uploaded yet.
              </p>
            )}
          </div>

          {stats && stats.total_chunks > 0 && (
            <button
              onClick={handleClearDocuments}
              className="mt-2 flex items-center space-x-1 text-xs text-rose-400 hover:text-rose-300 transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear ChromaDB ({stats.total_chunks} chunks)</span>
            </button>
          )}
        </div>

        {/* Section 3: Sync to Cloud Pinecone */}
        <div className="mt-6 pt-5 border-t border-slate-800">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
            <Cloud className="w-3.5 h-3.5 text-purple-400" />
            <span>2. Cloud Replicate (Pinecone)</span>
          </h3>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Pinecone Target Index
              </label>
              <input
                type="text"
                value={indexName}
                onChange={(e) => setIndexName(e.target.value)}
                placeholder="attention-paper"
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-purple-500"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Pinecone API Key (Optional if set in .env)
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="pcsk_..."
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-purple-500"
              />
            </div>

            <button
              onClick={handleSyncPinecone}
              disabled={isSyncing || !stats || stats.total_chunks === 0}
              className={`w-full py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-2 transition ${
                isSyncing || !stats || stats.total_chunks === 0
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-md shadow-purple-600/20'
              }`}
            >
              {isSyncing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Pushing Vectors to Pinecone...</span>
                </>
              ) : (
                <>
                  <Cloud className="w-3.5 h-3.5" />
                  <span>Sync {stats?.total_chunks ?? 0} Vectors to Pinecone</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
