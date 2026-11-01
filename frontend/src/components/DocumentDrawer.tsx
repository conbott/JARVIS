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
  const [syncStatus, setSyncStatus] = useState<string>('idle');
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
        text: `Indexed "${data.filename}" (${data.chunks_added} chunks).`,
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
    setSyncStatus('syncing');
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

      const count = data.synced_count ?? stats?.total_chunks ?? 0;
      setSyncStatus(`synced ${count} vectors`);
      setFeedback({
        type: 'success',
        text: data.message || `Successfully synced ${count} vectors to Pinecone!`,
      });
    } catch (err: any) {
      setSyncStatus('idle');
      setFeedback({
        type: 'error',
        text: err.message || 'Pinecone sync failed',
      });
    } finally {
      setIsSyncing(false);
    }
  };

  const handleClearDocuments = async () => {
    if (!confirm('Clear all uploaded documents from ChromaDB?')) return;

    try {
      const res = await fetch('/api/documents/clear', { method: 'DELETE' });
      if (res.ok) {
        setFeedback({ type: 'success', text: 'Document store cleared.' });
        setSyncStatus('idle');
        onRefreshStats();
      }
    } catch (err: any) {
      setFeedback({ type: 'error', text: 'Failed to clear documents' });
    }
  };

  const documents = stats?.documents || [];
  const totalChunks = stats?.total_chunks ?? 0;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="relative w-96 max-w-full bg-[var(--color-surface)] border-l border-[var(--color-border)] p-6 flex flex-col justify-between shadow-2xl z-10 overflow-y-auto font-sans">
        <div>
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-[var(--color-border)]">
            <h2 className="text-sm font-semibold text-[var(--color-text)] flex items-center gap-2">
              <FileText className="w-4 h-4 text-[var(--color-accent)]" />
              <span>Documents & Knowledge Store</span>
            </h2>
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-2)] transition"
              title="Close drawer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Feedback alert */}
          {feedback && (
            <div
              className={`mt-4 p-3 rounded-xl border text-xs flex items-start gap-2 ${
                feedback.type === 'success'
                  ? 'bg-[var(--color-accent)]/10 text-[var(--color-accent)] border-[var(--color-accent)]/20'
                  : 'bg-[var(--color-warn)]/10 text-[var(--color-warn)] border-[var(--color-warn)]/20'
              }`}
            >
              {feedback.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              )}
              <span className="leading-snug">{feedback.text}</span>
            </div>
          )}

          {/* Dropzone */}
          <div className="mt-5">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf,.txt,.md"
              className="hidden"
            />
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-[var(--color-border)] hover:border-[var(--color-accent)]/60 rounded-2xl p-6 text-center transition cursor-pointer bg-[var(--color-surface-2)]/30 group"
            >
              <UploadCloud className="w-7 h-7 mx-auto text-[var(--color-text-muted)] group-hover:text-[var(--color-accent)] transition mb-2" />
              <div className="text-xs font-medium text-[var(--color-text)]">
                {isUploading ? 'Chunking and embedding document...' : 'Click or drop files to index'}
              </div>
              <p className="text-[11px] text-[var(--color-text-muted)] mt-1">
                PDF, TXT, or MD documents
              </p>
            </div>
          </div>

          {/* Uploaded Documents List */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-text-muted)]">
                Indexed Documents ({documents.length})
              </span>
              <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
                {totalChunks} total chunks
              </span>
            </div>

            <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
              {documents.length === 0 ? (
                <div className="p-4 rounded-xl bg-[var(--color-surface-2)]/40 border border-[var(--color-border)] text-center text-xs text-[var(--color-text-muted)]">
                  No documents in local ChromaDB yet.
                </div>
              ) : (
                documents.map((doc, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border)] text-xs text-[var(--color-text)]"
                  >
                    <div className="flex items-center gap-2 truncate">
                      <FileText className="w-3.5 h-3.5 text-[var(--color-accent)] shrink-0" />
                      <span className="truncate font-mono text-[11px]">{doc}</span>
                    </div>
                  </div>
                ))
              )}
            </div>

            {documents.length > 0 && (
              <button
                onClick={handleClearDocuments}
                className="mt-2 text-[11px] text-[var(--color-warn)] hover:underline flex items-center gap-1 transition cursor-pointer"
              >
                <Trash2 className="w-3 h-3" />
                <span>Clear all indexed documents</span>
              </button>
            )}
          </div>

          {/* Pinecone Cloud Sync Section */}
          <div className="mt-6 pt-5 border-t border-[var(--color-border)]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-text-muted)] flex items-center gap-1.5">
                <Cloud className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                Pinecone Cloud Sync
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[var(--color-surface-2)] text-[var(--color-accent)]">
                Status: {syncStatus}
              </span>
            </div>

            <div className="space-y-2 mt-3">
              <input
                type="text"
                placeholder="Optional Pinecone API Key (or env)"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-lg px-3 py-1.5 text-xs text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)] font-mono"
              />
              <input
                type="text"
                placeholder="Pinecone Index Name"
                value={indexName}
                onChange={(e) => setIndexName(e.target.value)}
                className="w-full bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-lg px-3 py-1.5 text-xs text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)] font-mono"
              />

              <button
                onClick={handleSyncPinecone}
                disabled={isSyncing || totalChunks === 0}
                className="w-full mt-1 py-2 px-3 rounded-lg bg-[var(--color-surface-2)] hover:bg-[var(--color-surface)] border border-[var(--color-border)] text-xs text-[var(--color-text)] hover:text-[var(--color-accent)] transition flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                {isSyncing ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-[var(--color-accent)]" />
                    <span>Syncing ChromaDB vectors to Pinecone...</span>
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Sync to Pinecone Cloud</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-[var(--color-border)] text-[11px] text-[var(--color-text-muted)] flex items-center justify-between">
          <span>ChromaDB + Pinecone Dual Store</span>
          <button
            onClick={onRefreshStats}
            className="hover:text-[var(--color-text)] transition flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Refresh</span>
          </button>
        </div>
      </div>
    </div>
  );
};
