"use client";

import { motion } from "framer-motion";
import {
  Download,
  Eye,
  FileText,
  Filter,
  Plus,
  Search,
  Trash2,
  Loader2,
  RefreshCw,
  MessageSquare,
  AlertTriangle,
  CheckCircle,
  Clock,
  X,
  ArrowUpDown
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, getAuthToken } from "@/lib/api";

interface DocItem {
  id: string;
  name: string;
  type: string;
  date: string;
  rawDate: string;
  size: string;
  rawSize?: number | null;
  status: "Analyzed" | "Processing" | "Error";
}

function formatBytes(bytes?: number | null): string {
  if (!bytes || bytes <= 0) return "-";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"newest" | "oldest" | "name">("newest");
  const [documents, setDocuments] = useState<DocItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [authRequired, setAuthRequired] = useState(false);

  const fetchDocs = async (isRefresh = false) => {
    const token = getAuthToken();
    if (!token) {
      setLoading(false);
      setAuthRequired(true);
      return;
    }

    setAuthRequired(false);
    if (isRefresh) setRefreshing(true);
    else setLoading(true);

    try {
      const res = await apiFetch("/api/v1/documents");
      if (res.status === 401) {
        setAuthRequired(true);
        setDocuments([]);
        return;
      }
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          const mapped: DocItem[] = data.map((d: any) => ({
            id: d.id,
            name: d.filename,
            type: (d.file_type || "pdf").toUpperCase(),
            rawDate: d.created_at || "",
            date: d.created_at ? new Date(d.created_at).toLocaleDateString(undefined, {
              year: "numeric",
              month: "short",
              day: "numeric"
            }) : "Recent",
            rawSize: d.file_size,
            size: formatBytes(d.file_size),
            status: d.upload_status === "completed" ? "Analyzed" : 
                    d.upload_status === "failed" ? "Error" : "Processing"
          }));
          setDocuments(mapped);
        }
      }
    } catch (err) {
      console.error("Failed to fetch documents:", err);
      setFeedback({ type: "error", message: "Failed to load documents list from server." });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDocs();

    const handleAuthExpired = () => {
      setAuthRequired(true);
      setLoading(false);
    };
    window.addEventListener("lexiai:auth-expired", handleAuthExpired);
    return () => {
      window.removeEventListener("lexiai:auth-expired", handleAuthExpired);
    };
  }, []);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to permanently delete "${name}" and its vector indices?`)) return;
    setDeletingId(id);
    try {
      const res = await apiFetch(`/api/v1/documents/${id}`, { method: "DELETE" });
      if (res.ok) {
        setDocuments(prev => prev.filter(d => d.id !== id));
        setFeedback({ type: "success", message: `"${name}" removed successfully.` });
        setTimeout(() => setFeedback(null), 4000);
      } else {
        const err = await res.json().catch(() => ({}));
        setFeedback({ type: "error", message: err.detail || "Failed to delete document." });
      }
    } catch (err: any) {
      console.error("Error deleting doc:", err);
      setFeedback({ type: "error", message: err.message || "Failed to delete document." });
    } finally {
      setDeletingId(null);
    }
  };

  const handleDownload = async (id: string, name: string) => {
    setDownloadingId(id);
    try {
      const res = await apiFetch(`/api/v1/documents/${id}/download`);
      if (!res.ok) {
        throw new Error("Could not download original document from server.");
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error("Download failed:", err);
      setFeedback({ type: "error", message: err.message || "Failed to download document." });
      setTimeout(() => setFeedback(null), 4000);
    } finally {
      setDownloadingId(null);
    }
  };

  // Filter & Sort
  const filtered = documents
    .filter(d => {
      const matchesSearch = 
        d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.type.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStatus = 
        statusFilter === "all" ? true :
        statusFilter === "analyzed" ? d.status === "Analyzed" :
        statusFilter === "processing" ? d.status === "Processing" :
        statusFilter === "error" ? d.status === "Error" : true;

      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      if (sortBy === "newest") {
        return new Date(b.rawDate).getTime() - new Date(a.rawDate).getTime();
      } else if (sortBy === "oldest") {
        return new Date(a.rawDate).getTime() - new Date(b.rawDate).getTime();
      } else {
        return a.name.localeCompare(b.name);
      }
    });

  const analyzedCount = documents.filter(d => d.status === "Analyzed").length;
  const processingCount = documents.filter(d => d.status === "Processing").length;
  const errorCount = documents.filter(d => d.status === "Error").length;

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-serif font-semibold text-ivory mb-2">Legal Documents</h1>
          <p className="text-white/50 text-sm">
            Manage, inspect, analyze, and query your uploaded legal contracts and case files.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchDocs(true)}
            disabled={refreshing || loading}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors text-sm font-medium text-ivory disabled:opacity-50"
            title="Refresh documents list"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin text-gold" : ""}`} />
            Refresh
          </button>
          <Link href="/upload">
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gold text-charcoal border border-gold hover:bg-gold/90 transition-colors text-sm font-semibold shadow-lg shadow-gold/10">
              <Plus className="w-4 h-4" />
              Upload Document
            </button>
          </Link>
        </div>
      </div>

      {/* Auth Banner */}
      {authRequired && (
        <div className="p-4 rounded-xl bg-burgundy/10 border border-burgundy/30 text-ivory flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-burgundy shrink-0" />
            <span className="text-sm">Please sign in to access your uploaded documents and analyses.</span>
          </div>
          <Link href="/login" className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-gold text-charcoal hover:bg-gold/90 transition-colors">
            Sign In
          </Link>
        </div>
      )}

      {/* Feedback Alert */}
      {feedback && (
        <div className={`p-4 rounded-xl text-sm flex items-center justify-between border ${
          feedback.type === "success" 
            ? "bg-green-500/10 border-green-500/20 text-green-400" 
            : "bg-burgundy/10 border-burgundy/30 text-ivory"
        }`}>
          <span>{feedback.message}</span>
          <button onClick={() => setFeedback(null)} className="text-white/40 hover:text-white/80">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Repository Container */}
      <div className="glass rounded-2xl border border-white/5 bg-white/5 overflow-hidden flex flex-col shadow-xl">
        {/* Toolbar & Filter Tabs */}
        <div className="p-4 border-b border-white/5 flex flex-col lg:flex-row gap-4 justify-between items-stretch lg:items-center">
          {/* Search */}
          <div className="relative w-full max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
            <input 
              type="text" 
              placeholder="Search by filename or type (e.g. PDF, agreement)..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-charcoal/50 border border-white/10 rounded-lg py-2 pl-9 pr-9 text-sm placeholder:text-white/30 focus:outline-none focus:ring-1 focus:ring-gold/50 transition-all text-ivory"
            />
            {searchTerm && (
              <button 
                onClick={() => setSearchTerm("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/70"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Filters & Sorting */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Status Pills */}
            <div className="flex items-center p-1 rounded-lg bg-charcoal/60 border border-white/10 text-xs">
              <button
                onClick={() => setStatusFilter("all")}
                className={`px-3 py-1 rounded-md transition-colors ${
                  statusFilter === "all" ? "bg-white/10 text-gold font-semibold" : "text-white/50 hover:text-ivory"
                }`}
              >
                All ({documents.length})
              </button>
              <button
                onClick={() => setStatusFilter("analyzed")}
                className={`px-3 py-1 rounded-md transition-colors ${
                  statusFilter === "analyzed" ? "bg-green-500/20 text-green-400 font-semibold" : "text-white/50 hover:text-ivory"
                }`}
              >
                Analyzed ({analyzedCount})
              </button>
              <button
                onClick={() => setStatusFilter("processing")}
                className={`px-3 py-1 rounded-md transition-colors ${
                  statusFilter === "processing" ? "bg-gold/20 text-gold font-semibold" : "text-white/50 hover:text-ivory"
                }`}
              >
                Processing ({processingCount})
              </button>
              {errorCount > 0 && (
                <button
                  onClick={() => setStatusFilter("error")}
                  className={`px-3 py-1 rounded-md transition-colors ${
                    statusFilter === "error" ? "bg-burgundy/30 text-burgundy font-semibold" : "text-white/50 hover:text-ivory"
                  }`}
                >
                  Error ({errorCount})
                </button>
              )}
            </div>

            {/* Sort Dropdown */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-charcoal/60 border border-white/10 text-xs text-white/60">
              <ArrowUpDown className="w-3.5 h-3.5 text-gold" />
              <select
                value={sortBy}
                onChange={(e: any) => setSortBy(e.target.value)}
                className="bg-transparent text-ivory text-xs focus:outline-none cursor-pointer"
              >
                <option value="newest" className="bg-charcoal text-ivory">Newest First</option>
                <option value="oldest" className="bg-charcoal text-ivory">Oldest First</option>
                <option value="name" className="bg-charcoal text-ivory">Name (A-Z)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Table Content */}
        <div className="overflow-x-auto">
          {loading ? (
            <div className="p-16 flex flex-col justify-center items-center gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-gold" />
              <span className="text-sm text-white/50">Loading legal documents repository...</span>
            </div>
          ) : documents.length === 0 ? (
            <div className="p-16 text-center flex flex-col items-center justify-center space-y-4">
              <div className="w-14 h-14 rounded-2xl bg-gold/10 border border-gold/20 flex items-center justify-center text-gold">
                <FileText className="w-7 h-7" />
              </div>
              <div>
                <h3 className="text-lg font-serif font-semibold text-ivory mb-1">No Documents Uploaded</h3>
                <p className="text-sm text-white/40 max-w-sm">
                  Upload contracts, litigation briefs, or legal instruments to initiate AI extraction and grounded Q&A.
                </p>
              </div>
              <Link href="/upload">
                <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gold text-charcoal border border-gold hover:bg-gold/90 transition-colors text-sm font-semibold">
                  <Plus className="w-4 h-4" />
                  Upload Your First Document
                </button>
              </Link>
            </div>
          ) : filtered.length === 0 ? (
            <div className="p-12 text-center text-white/40 flex flex-col items-center gap-3">
              <p>No documents match your current search or status filter.</p>
              <button
                onClick={() => { setSearchTerm(""); setStatusFilter("all"); }}
                className="text-xs text-gold underline hover:text-gold/80"
              >
                Clear Filters
              </button>
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/5 bg-charcoal/40">
                  <th className="py-3.5 px-6 text-xs font-semibold text-white/50 uppercase tracking-wider">Document Name</th>
                  <th className="py-3.5 px-6 text-xs font-semibold text-white/50 uppercase tracking-wider">Type</th>
                  <th className="py-3.5 px-6 text-xs font-semibold text-white/50 uppercase tracking-wider">Size</th>
                  <th className="py-3.5 px-6 text-xs font-semibold text-white/50 uppercase tracking-wider">Date Added</th>
                  <th className="py-3.5 px-6 text-xs font-semibold text-white/50 uppercase tracking-wider">Status</th>
                  <th className="py-3.5 px-6 text-xs font-semibold text-white/50 uppercase tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm">
                {filtered.map((doc, i) => (
                  <motion.tr 
                    key={doc.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: Math.min(i * 0.03, 0.3) }}
                    className="hover:bg-white/5 transition-colors group"
                  >
                    {/* Name */}
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-3 max-w-md">
                        <div className={`p-2 rounded-lg border ${
                          doc.type === "PDF" ? "bg-red-500/10 border-red-500/20 text-red-400" :
                          doc.type === "DOCX" ? "bg-blue-500/10 border-blue-500/20 text-blue-400" :
                          "bg-gold/10 border-gold/20 text-gold"
                        }`}>
                          <FileText className="w-4 h-4 shrink-0" />
                        </div>
                        <div className="truncate">
                          <Link href={`/analysis?docId=${doc.id}`} className="font-medium text-ivory hover:text-gold transition-colors truncate block">
                            {doc.name}
                          </Link>
                          <span className="text-[11px] text-white/30 font-mono">ID: {doc.id.slice(0, 8)}...</span>
                        </div>
                      </div>
                    </td>

                    {/* Type */}
                    <td className="py-4 px-6">
                      <span className="text-xs font-mono font-medium text-white/70 bg-white/5 border border-white/10 px-2 py-0.5 rounded">
                        {doc.type}
                      </span>
                    </td>

                    {/* Size */}
                    <td className="py-4 px-6 text-xs text-white/50 font-mono">
                      {doc.size}
                    </td>

                    {/* Date */}
                    <td className="py-4 px-6 text-xs text-white/50">
                      {doc.date}
                    </td>

                    {/* Status */}
                    <td className="py-4 px-6">
                      <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium ${
                        doc.status === "Analyzed" ? "bg-green-500/10 text-green-400 border border-green-500/20" : 
                        doc.status === "Processing" ? "bg-gold/10 text-gold border border-gold/20" :
                        "bg-burgundy/20 text-burgundy border border-burgundy/30"
                      }`}>
                        {doc.status === "Analyzed" && <CheckCircle className="w-3 h-3 text-green-400" />}
                        {doc.status === "Processing" && <Loader2 className="w-3 h-3 animate-spin text-gold" />}
                        {doc.status === "Error" && <AlertTriangle className="w-3 h-3 text-burgundy" />}
                        {doc.status}
                      </span>
                    </td>

                    {/* Actions */}
                    <td className="py-4 px-6 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {/* View Analysis */}
                        <Link href={`/analysis?docId=${doc.id}`}>
                          <button 
                            className="p-2 rounded-lg hover:bg-white/10 text-white/60 hover:text-gold transition-colors" 
                            title="View Legal Analysis"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </Link>

                        {/* Ask AI Chat */}
                        <Link href={`/ask?docId=${doc.id}`}>
                          <button 
                            className="p-2 rounded-lg hover:bg-white/10 text-white/60 hover:text-cyan-400 transition-colors" 
                            title="Ask Document (RAG AI)"
                          >
                            <MessageSquare className="w-4 h-4" />
                          </button>
                        </Link>

                        {/* Download Original File */}
                        <button
                          onClick={() => handleDownload(doc.id, doc.name)}
                          disabled={downloadingId === doc.id}
                          className="p-2 rounded-lg hover:bg-white/10 text-white/60 hover:text-ivory transition-colors disabled:opacity-50"
                          title="Download Original File"
                        >
                          {downloadingId === doc.id ? (
                            <Loader2 className="w-4 h-4 animate-spin text-gold" />
                          ) : (
                            <Download className="w-4 h-4" />
                          )}
                        </button>

                        {/* Delete */}
                        <button 
                          onClick={() => handleDelete(doc.id, doc.name)}
                          disabled={deletingId === doc.id}
                          className="p-2 rounded-lg hover:bg-burgundy/20 text-white/50 hover:text-burgundy transition-colors disabled:opacity-50" 
                          title="Delete from Database"
                        >
                          {deletingId === doc.id ? (
                            <Loader2 className="w-4 h-4 animate-spin text-burgundy" />
                          ) : (
                            <Trash2 className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        
        {/* Footer / Count Info */}
        <div className="p-4 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-white/40">
          <span>
            Showing <strong className="text-ivory font-medium">{filtered.length}</strong> of <strong className="text-ivory font-medium">{documents.length}</strong> legal documents
          </span>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-400 inline-block"></span> {analyzedCount} Analyzed
            </span>
            {processingCount > 0 && (
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-gold inline-block"></span> {processingCount} In Progress
              </span>
            )}
            <Link href="/upload" className="text-gold hover:underline font-medium">
              + Ingest New File
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
