"use client";

import { motion } from "framer-motion";
import { Download, Eye, FileText, Filter, MoreHorizontal, Plus, Search, Trash2, Loader2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, getAuthToken } from "@/lib/api";

export default function DocumentsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDocs = async () => {
    const token = getAuthToken();
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const res = await apiFetch("/api/v1/documents");
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          const mapped = data.map((d: any) => ({
            id: d.id,
            name: d.filename,
            type: (d.file_type || "pdf").toUpperCase(),
            date: d.created_at ? new Date(d.created_at).toLocaleDateString() : "Recent",
            size: "-",
            status: d.upload_status === "completed" ? "Analyzed" : 
                    d.upload_status === "failed" ? "Error" : "Processing"
          }));
          setDocuments(mapped);
        }
      }
    } catch (err) {
      console.error("Failed to fetch documents:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to remove ${name} from the database?`)) return;
    try {
      const res = await apiFetch(`/api/v1/documents/${id}`, { method: "DELETE" });
      if (res.ok) {
        setDocuments(prev => prev.filter(d => d.id !== id));
      } else {
        alert("Failed to delete document.");
      }
    } catch (err) {
      console.error("Error deleting doc:", err);
    }
  };

  const filtered = documents.filter(d => 
    d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 pb-10">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-serif font-semibold text-ivory mb-2">Documents</h1>
          <p className="text-white/50">Manage and analyze your legal documents stored in database.</p>
        </div>
        <div className="flex gap-3">
          <Link href="/upload">
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gold text-charcoal border border-gold hover:bg-gold/90 transition-colors text-sm font-semibold">
              <Plus className="w-4 h-4" />
              Upload Document
            </button>
          </Link>
        </div>
      </div>

      <div className="glass rounded-2xl border border-white/5 bg-white/5 overflow-hidden flex flex-col">
        {/* Toolbar */}
        <div className="p-4 border-b border-white/5 flex flex-col sm:flex-row gap-4 justify-between">
          <div className="relative w-full max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
            <input 
              type="text" 
              placeholder="Search by name, type, or citation..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-charcoal/50 border border-white/10 rounded-lg py-2 pl-9 pr-4 text-sm placeholder:text-white/30 focus:outline-none focus:ring-1 focus:ring-gold/50 transition-all text-ivory"
            />
          </div>
          <div className="flex items-center text-xs text-white/40">
            Total Ingested: <span className="font-semibold text-ivory ml-1">{documents.length}</span>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          {loading ? (
            <div className="p-16 flex justify-center items-center">
              <Loader2 className="w-8 h-8 animate-spin text-gold" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="p-12 text-center text-white/40">
              No matching documents found in database.
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/5 bg-charcoal/30">
                  <th className="py-3 px-6 text-xs font-semibold text-white/50 uppercase tracking-wider">Document Name</th>
                  <th className="py-3 px-6 text-xs font-semibold text-white/50 uppercase tracking-wider">Type</th>
                  <th className="py-3 px-6 text-xs font-semibold text-white/50 uppercase tracking-wider">Date Added</th>
                  <th className="py-3 px-6 text-xs font-semibold text-white/50 uppercase tracking-wider">Status</th>
                  <th className="py-3 px-6 text-xs font-semibold text-white/50 uppercase tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filtered.map((doc, i) => (
                  <motion.tr 
                    key={doc.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className="hover:bg-white/5 transition-colors group"
                  >
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-3">
                        <FileText className="w-5 h-5 text-gold/80 shrink-0" />
                        <span className="text-sm font-medium text-ivory group-hover:text-gold transition-colors">{doc.name}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span className="text-xs text-white/70 bg-white/5 px-2 py-1 rounded-md">{doc.type}</span>
                    </td>
                    <td className="py-4 px-6 text-sm text-white/50">{doc.date}</td>
                    <td className="py-4 px-6">
                      <span className={`text-xs px-2.5 py-1 rounded-full ${
                        doc.status === 'Analyzed' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 
                        doc.status === 'Processing' ? 'bg-gold/10 text-gold border border-gold/20' :
                        'bg-burgundy/20 text-burgundy border border-burgundy/30'
                      }`}>
                        {doc.status}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link href={`/analysis?docId=${doc.id}`}>
                          <button className="p-1.5 rounded hover:bg-white/10 text-white/50 hover:text-ivory transition-colors" title="View Analysis">
                            <Eye className="w-4 h-4" />
                          </button>
                        </Link>
                        <button 
                          onClick={() => handleDelete(doc.id, doc.name)}
                          className="p-1.5 rounded hover:bg-burgundy/20 text-white/50 hover:text-burgundy transition-colors" 
                          title="Delete from Database"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        
        {/* Pagination Info */}
        <div className="p-4 border-t border-white/5 flex items-center justify-between text-sm text-white/50">
          <span>Showing 1 to {filtered.length} of {documents.length} entries</span>
        </div>
      </div>
    </div>
  );
}
