"use client";

import { motion } from "framer-motion";
import { ArrowRightLeft, FileText, Check, X, Loader2, Download, Copy } from "lucide-react";
import { useEffect, useState } from "react";
import { apiFetch, getAuthToken } from "@/lib/api";

export default function ComparisonPage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [docAId, setDocAId] = useState<string>("");
  const [docBId, setDocBId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [comparison, setComparison] = useState<any>(null);
  const [exported, setExported] = useState(false);

  useEffect(() => {
    const fetchDocs = async () => {
      const token = getAuthToken();
      if (!token) return;

      try {
        const res = await apiFetch("/api/v1/documents");
        if (res.ok) {
          const docs = await res.json();
          if (Array.isArray(docs) && docs.length > 0) {
            setDocuments(docs);
            const a = docs[0].id;
            const b = docs.length > 1 ? docs[1].id : docs[0].id;
            setDocAId(a);
            setDocBId(b);
            triggerCompare(a, b);
          }
        }
      } catch (err) {
        console.error("Failed to load documents for comparison:", err);
      }
    };

    fetchDocs();
  }, []);

  const triggerCompare = async (aId: string, bId: string) => {
    if (!aId || !bId) return;
    setLoading(true);
    try {
      const res = await apiFetch("/api/v1/comparison", {
        method: "POST",
        body: JSON.stringify({ doc_a_id: aId, doc_b_id: bId })
      });
      if (res.ok) {
        const data = await res.json();
        setComparison(data);
      }
    } catch (err) {
      console.error("Comparison error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDocAChange = (id: string) => {
    setDocAId(id);
    triggerCompare(id, docBId);
  };

  const handleDocBChange = (id: string) => {
    setDocBId(id);
    triggerCompare(docAId, id);
  };

  const docAObj = documents.find(d => d.id === docAId);
  const docBObj = documents.find(d => d.id === docBId);

  const handleExportDiffReport = async () => {
    const timestamp = new Date().toISOString();
    const docAName = docAObj?.filename || "Document_A";
    const docBName = docBObj?.filename || "Document_B";

    const reportContent = `================================================================================
LEXIAI LEGAL INSTRUMENT COMPARISON & AUDIT REPORT
Generated: ${new Date().toLocaleString()} (${timestamp})
================================================================================

AUDIT METADATA:
- Base Instrument (Doc A): ${docAName} [ID: ${docAId}]
- Target Instrument (Doc B): ${docBName} [ID: ${docBId}]
- Audit System: LEXIAI Legal Analysis Engine v2.0

VARIATION METRICS:
- Clause Additions: ${comparison?.additions_count ?? 0}
- Clause Deletions: ${comparison?.deletions_count ?? 0}
- Material Modifications: ${comparison?.modifications_count ?? 0}

--------------------------------------------------------------------------------
BASE INSTRUMENT (DOCUMENT A) EXTRACT:
--------------------------------------------------------------------------------
${comparison?.text_a_sample || "No text available."}

--------------------------------------------------------------------------------
TARGET INSTRUMENT (DOCUMENT B) EXTRACT:
--------------------------------------------------------------------------------
${comparison?.text_b_sample || "No text available."}

================================================================================
CONFIDENTIALITY & LEGAL DISCLAIMER:
This comparison report was generated automatically by LEXIAI for audit and legal 
due-diligence purposes. All rights reserved.
================================================================================`;

    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(reportContent);
      }
    } catch (e) {
      console.warn("Clipboard access failed:", e);
    }

    try {
      const blob = new Blob([reportContent], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `lexiai_diff_audit_${docAName.replace(/\.[^/.]+$/, "")}_vs_${docBName.replace(/\.[^/.]+$/, "")}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Export file creation failed:", e);
    }

    setExported(true);
    setTimeout(() => setExported(false), 3500);
  };

  return (
    <div className="space-y-6 pb-10 max-w-6xl mx-auto flex flex-col">
      <div>
        <h1 className="text-3xl font-serif font-semibold text-ivory mb-2">Document Comparison</h1>
        <p className="text-white/50">
          Compare any two legal instruments from your database to detect clause variations, additions, and deletions.
        </p>
      </div>

      {/* Selectors */}
      <div className="flex flex-col sm:flex-row items-center gap-4 mb-4">
        <div className="flex-1 w-full glass p-3 rounded-lg border border-white/10 bg-white/5 flex items-center justify-between">
          <div className="flex items-center gap-3 w-full">
            <FileText className="w-5 h-5 text-white/50 shrink-0" />
            <select
              value={docAId}
              onChange={(e) => handleDocAChange(e.target.value)}
              className="w-full bg-transparent text-sm font-medium text-ivory focus:outline-none"
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id} className="bg-charcoal text-ivory">
                  {d.filename}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="w-10 h-10 rounded-full bg-gold/10 border border-gold/20 flex items-center justify-center shrink-0">
          <ArrowRightLeft className="w-5 h-5 text-gold" />
        </div>
        
        <div className="flex-1 w-full glass p-3 rounded-lg border border-white/10 bg-white/5 flex items-center justify-between">
          <div className="flex items-center gap-3 w-full">
            <FileText className="w-5 h-5 text-white/50 shrink-0" />
            <select
              value={docBId}
              onChange={(e) => handleDocBChange(e.target.value)}
              className="w-full bg-transparent text-sm font-medium text-ivory focus:outline-none"
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id} className="bg-charcoal text-ivory">
                  {d.filename}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="p-16 glass rounded-2xl border border-white/5 flex justify-center items-center">
          <Loader2 className="w-8 h-8 animate-spin text-gold" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-white/5 border border-white/10 rounded-2xl overflow-hidden p-4">
          {/* Document A Excerpt */}
          <div className="bg-charcoal/80 p-6 rounded-xl border border-white/5 overflow-y-auto max-h-125">
            <h3 className="text-white/70 uppercase tracking-widest text-xs mb-4 font-semibold">
              Original: {docAObj?.filename || "Document A"}
            </h3>
            {comparison?.text_a_sample ? (
              <div className="text-white/80 leading-relaxed whitespace-pre-line font-mono text-xs">
                {comparison.text_a_sample}
              </div>
            ) : (
              <p className="text-sm text-white/40 italic">No text extracted for Document A.</p>
            )}
          </div>

          {/* Document B Excerpt */}
          <div className="bg-charcoal/80 p-6 rounded-xl border border-white/5 overflow-y-auto max-h-125">
            <h3 className="text-white/70 uppercase tracking-widest text-xs mb-4 font-semibold">
              Comparison: {docBObj?.filename || "Document B"}
            </h3>
            {comparison?.text_b_sample ? (
              <div className="text-white/80 leading-relaxed whitespace-pre-line font-mono text-xs">
                {comparison.text_b_sample}
              </div>
            ) : (
              <p className="text-sm text-white/40 italic">No text extracted for Document B.</p>
            )}
          </div>
        </div>
      )}
      
      {/* Metrics Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-center gap-4 bg-white/5 border border-white/10 p-4 rounded-xl mt-4">
        <div className="flex gap-6">
          <div className="flex items-center gap-2 text-sm">
            <span className="w-3 h-3 rounded-sm bg-green-500/50 border border-green-500"></span>
            <span className="text-white/70">Additions ({comparison?.additions_count || 0})</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="w-3 h-3 rounded-sm bg-burgundy/50 border border-burgundy"></span>
            <span className="text-white/70">Deletions ({comparison?.deletions_count || 0})</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="w-3 h-3 rounded-sm bg-gold/50 border border-gold"></span>
            <span className="text-white/70">Modifications ({comparison?.modifications_count || 0})</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {exported && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-1.5 text-xs text-green-400 bg-green-500/10 border border-green-500/30 px-3 py-1.5 rounded-lg"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Copied to Clipboard & Audit Log Exported</span>
            </motion.div>
          )}
          <button 
            onClick={handleExportDiffReport}
            className="text-sm bg-gold text-charcoal px-4 py-2 rounded-lg font-semibold hover:bg-gold/90 transition-colors flex items-center gap-2 shadow-lg shadow-gold/10"
          >
            <Download className="w-4 h-4" />
            <span>Export Diff Report</span>
          </button>
        </div>
      </div>
    </div>
  );
}
