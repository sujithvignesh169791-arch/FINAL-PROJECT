"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  FileSearch,
  Filter,
  Loader2,
  FileText,
  RefreshCw,
  ExternalLink
} from "lucide-react";
import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { apiFetch, getAuthToken } from "@/lib/api";

interface ClauseItem {
  clause_type: string;
  title: string;
  text: string;
  source_page?: number | null;
}

interface AnalysisSectionItem {
  term: string;
  status: "Critical" | "Warning" | "Standard";
  description: string;
}

interface AnalysisSection {
  category: string;
  items: AnalysisSectionItem[];
}

export default function AnalysisPage() {
  const [expanded, setExpanded] = useState<number | null>(0);
  const [analysisResults, setAnalysisResults] = useState<AnalysisSection[]>([]);
  const [summaryData, setSummaryData] = useState({
    score: 75,
    summaryText: "Loading document analysis...",
    docName: "",
    criticalCount: 0,
    warningCount: 0,
    standardCount: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const inFlightDocId = useRef<string | null>(null);

  // Load document list and determine active document
  useEffect(() => {
    const handleAuthExpired = () => {
      setError("Your session has expired. Please sign in again.");
      setLoading(false);
    };
    window.addEventListener("lexiai:auth-expired", handleAuthExpired);

    const init = async () => {
      const token = getAuthToken();
      if (!token) {
        setLoading(false);
        setError("Please sign in to view your analyzed documents.");
        setSummaryData(prev => ({
          ...prev,
          summaryText: "Authentication required to load legal analyses."
        }));
        return;
      }

      try {
        const docsRes = await apiFetch("/api/v1/documents");
        if (docsRes.status === 401) {
          throw new Error("Your session has expired. Please sign in again.");
        }
        if (!docsRes.ok) {
          throw new Error("Failed to load documents list.");
        }
        const docs = await docsRes.json();
        if (!Array.isArray(docs) || docs.length === 0) {
          setLoading(false);
          setDocuments([]);
          setError("No documents found. Please upload a contract or legal document first.");
          setSummaryData(prev => ({
            ...prev,
            summaryText: "No documents available for analysis."
          }));
          return;
        }

        setDocuments(docs);

        // Check if docId is provided in URL query params
        let targetId = docs[docs.length - 1].id;
        if (typeof window !== "undefined") {
          const urlParams = new URLSearchParams(window.location.search);
          const paramId = urlParams.get("docId");
          if (paramId && docs.some(d => d.id === paramId)) {
            targetId = paramId;
          }
        }

        setSelectedDocId(targetId);
        loadAnalysis(targetId, docs);
      } catch (err: any) {
        console.error("Initialization error:", err);
        setLoading(false);
        setError(err.message || "Failed to initialize document analysis.");
      }
    };

    init();
    return () => {
      window.removeEventListener("lexiai:auth-expired", handleAuthExpired);
    };
  }, []);

  const loadAnalysis = async (docId: string, currentDocs: any[] = documents, forceRetry: boolean = false) => {
    if (!docId) return;
    if (inFlightDocId.current === docId && !forceRetry) return;
    inFlightDocId.current = docId;

    setLoading(true);
    setError(null);

    const docObj = currentDocs.find(d => d.id === docId);
    const docName = docObj ? docObj.filename : "Legal Document";

    setSummaryData(prev => ({
      ...prev,
      docName,
      summaryText: `Checking analysis status for ${docName}...`
    }));

    try {
      // 1. If document upload extraction is still in progress, poll until ready
      if (docObj && docObj.upload_status === "processing") {
        setSummaryData(prev => ({
          ...prev,
          summaryText: `Extracting text from ${docName}...`
        }));
        
        let attempts = 0;
        let isDone = false;
        while (attempts < 20 && !isDone) {
          await new Promise(r => setTimeout(r, 1500));
          attempts++;
          try {
            const jobRes = await apiFetch(`/api/v1/documents/jobs/${docId}`);
            if (jobRes.ok) {
              const jobData = await jobRes.json();
              if (jobData.status === "completed") {
                isDone = true;
                break;
              } else if (jobData.status === "failed") {
                throw new Error(jobData.message || "Document text extraction failed.");
              }
            }
          } catch (jobErr: any) {
            if (jobErr.message && jobErr.message.includes("failed")) throw jobErr;
          }
        }
      }

      setSummaryData(prev => ({
        ...prev,
        summaryText: `Analyzing ${docName} with AI Engine...`
      }));

      // 2. Fetch analysis record
      let analysisRes = await apiFetch(`/api/v1/documents/${docId}/analysis`);
      let data: any = null;

      if (analysisRes.ok) {
        data = await analysisRes.json().catch(() => null);
      }

      // If backend reports analysis actively running in another thread (409 or 425), wait briefly
      if (analysisRes.status === 409 || analysisRes.status === 425) {
        await new Promise(r => setTimeout(r, 2000));
        analysisRes = await apiFetch(`/api/v1/documents/${docId}/analysis`);
        if (analysisRes.ok) {
          data = await analysisRes.json().catch(() => null);
        }
      }

      // If no analysis exists yet or summary is missing, trigger analyze endpoint once
      if (!data || !data.summary) {
        const analyzeTrigger = await apiFetch(`/api/v1/documents/${docId}/analyze`, {
          method: "POST"
        });
        if (!analyzeTrigger.ok) {
          if (analyzeTrigger.status === 401) {
            throw new Error("Your session has expired. Please sign in again.");
          }
          const errData = await analyzeTrigger.json().catch(() => ({}));
          throw new Error(errData.detail || "Document analysis failed.");
        }
        data = await analyzeTrigger.json();
      }

      if (!data || !data.summary) {
        throw new Error("Unable to retrieve complete legal analysis.");
      }

      parseAndSetAnalysis(data, docName);
    } catch (err: any) {
      console.error("Analysis load error:", err);
      setError(err.message || "Could not complete legal analysis.");
      setSummaryData(prev => ({
        ...prev,
        summaryText: "Analysis could not be generated."
      }));
    } finally {
      inFlightDocId.current = null;
      setLoading(false);
    }
  };

  const parseAndSetAnalysis = (data: any, docName: string) => {
    const sections: AnalysisSection[] = [];
    let crit = 0;
    let warn = 0;
    let std = 0;

    const summary = data.summary || "Document review completed successfully.";
    const entities = data.extracted_entities || {};

    // 1. Key Obligations & Important Points
    const points: AnalysisSectionItem[] = [];
    if (Array.isArray(entities.important_points)) {
      entities.important_points.forEach((pt: string) => {
        points.push({ term: "Key Finding", status: "Warning", description: pt });
        warn++;
      });
    }
    if (Array.isArray(entities.obligations)) {
      entities.obligations.forEach((ob: string) => {
        points.push({ term: "Obligation", status: "Standard", description: ob });
        std++;
      });
    }
    if (points.length > 0) {
      sections.push({ category: "Key Findings & Obligations", items: points });
    }

    // 2. Extracted Clauses
    if (Array.isArray(data.clauses) && data.clauses.length > 0) {
      const clauseItems: AnalysisSectionItem[] = data.clauses.map((c: ClauseItem) => {
        const isCritical = /liability|indemnity|penalty|breach/i.test(c.clause_type || c.title);
        const status = isCritical ? "Critical" : "Standard";
        if (isCritical) crit++;
        else std++;

        const pageLabel = c.source_page ? ` [Page ${c.source_page}]` : "";
        return {
          term: `${c.title || c.clause_type}${pageLabel}`,
          status,
          description: c.text
        };
      });
      sections.push({ category: "Extracted Legal Clauses", items: clauseItems });
    }

    // 3. Parties, Entities & Jurisdiction
    const entityItems: AnalysisSectionItem[] = [];
    if (entities.parties?.length) {
      entityItems.push({ term: "Named Parties", status: "Standard", description: entities.parties.join(", ") });
      std++;
    }
    if (entities.organizations?.length) {
      entityItems.push({ term: "Organizations", status: "Standard", description: entities.organizations.join(", ") });
      std++;
    }
    if (entities.dates?.length) {
      entityItems.push({ term: "Important Dates & Deadlines", status: "Standard", description: entities.dates.join("; ") });
      std++;
    }
    if (entities.jurisdiction?.length) {
      entityItems.push({ term: "Governing Jurisdiction", status: "Standard", description: entities.jurisdiction.join(", ") });
      std++;
    }
    if (entities.dispute_resolution?.length) {
      entityItems.push({ term: "Dispute Resolution", status: "Standard", description: entities.dispute_resolution.join(", ") });
      std++;
    }
    if (entityItems.length > 0) {
      sections.push({ category: "Parties, Jurisdiction & Dates", items: entityItems });
    }

    // 4. Commercial & Risk Terms
    const termItems: AnalysisSectionItem[] = [];
    if (entities.payment_terms?.length) {
      termItems.push({ term: "Payment Terms", status: "Standard", description: entities.payment_terms.join("; ") });
      std++;
    }
    if (entities.penalties?.length) {
      termItems.push({ term: "Penalties & Default", status: "Warning", description: entities.penalties.join("; ") });
      warn++;
    }
    const termConditions = entities.termination_conditions || entities.termination_terms || [];
    if (termConditions.length) {
      termItems.push({ term: "Termination Conditions", status: "Warning", description: termConditions.join("; ") });
      warn++;
    }
    const liabTerms = entities.liability_and_indemnity || entities.liability_terms || [];
    if (liabTerms.length) {
      termItems.push({ term: "Liability & Indemnity", status: "Critical", description: liabTerms.join("; ") });
      crit++;
    }
    const confTerms = entities.confidentiality || entities.confidentiality_terms || [];
    if (confTerms.length) {
      termItems.push({ term: "Confidentiality Scope", status: "Standard", description: confTerms.join("; ") });
      std++;
    }
    if (termItems.length > 0) {
      sections.push({ category: "Financial, Risk & Termination Terms", items: termItems });
    }

    // 5. Explicit Legal Acts & Statutory Sections
    const legalItems: AnalysisSectionItem[] = [];
    if (entities.legal_acts?.length) {
      legalItems.push({ term: "Referenced Acts", status: "Standard", description: entities.legal_acts.join(", ") });
      std++;
    }
    if (entities.legal_sections?.length) {
      legalItems.push({ term: "Referenced Statutory Sections", status: "Standard", description: entities.legal_sections.join(", ") });
      std++;
    }
    if (legalItems.length > 0) {
      sections.push({ category: "Legal Acts & Statutory References", items: legalItems });
    }

    if (sections.length === 0) {
      sections.push({
        category: "Analysis Summary",
        items: [{ term: "Summary", status: "Standard", description: summary }]
      });
      std++;
    }

    const finalScore = typeof data.risk_score === "number" ? Math.round(data.risk_score) : 78;

    setAnalysisResults(sections);
    setSummaryData({
      score: finalScore,
      summaryText: summary,
      docName,
      criticalCount: crit,
      warningCount: warn,
      standardCount: std
    });
  };

  const handleDocumentChange = (docId: string) => {
    setSelectedDocId(docId);
    loadAnalysis(docId, documents);
  };

  return (
    <div className="space-y-6 pb-10 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-serif font-semibold text-ivory mb-2">Document Analysis</h1>
          <p className="text-white/50 text-sm max-w-2xl leading-relaxed">
            {summaryData.summaryText}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {documents.length > 0 && (
            <select
              value={selectedDocId}
              onChange={(e) => handleDocumentChange(e.target.value)}
              className="px-3 py-2 rounded-lg bg-charcoal/80 border border-white/10 text-ivory text-sm focus:outline-none focus:ring-1 focus:ring-gold"
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id} className="bg-charcoal text-ivory">
                  {d.filename}
                </option>
              ))}
            </select>
          )}

          <button
            onClick={() => selectedDocId && loadAnalysis(selectedDocId)}
            disabled={loading || !selectedDocId}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors text-sm font-medium text-ivory disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Re-Analyze
          </button>

          <Link href="/ask">
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gold text-charcoal border border-gold hover:bg-gold/90 transition-colors text-sm font-semibold">
              Ask Document
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-burgundy/10 border border-burgundy/30 text-ivory flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-burgundy shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => selectedDocId && loadAnalysis(selectedDocId, documents, true)}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-ivory transition-colors flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Retry
            </button>
            {error.toLowerCase().includes("sign in") || error.toLowerCase().includes("session") || error.toLowerCase().includes("credential") ? (
              <Link href="/login" className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-gold text-charcoal hover:bg-gold/90 transition-colors">
                Sign In
              </Link>
            ) : (
              <Link href="/upload" className="text-xs font-semibold text-gold underline hover:text-gold/80">
                Upload New Document
              </Link>
            )}
          </div>
        </div>
      )}

      {loading && (
        <div className="p-12 glass rounded-xl border border-white/5 flex flex-col items-center justify-center space-y-4">
          <Loader2 className="w-8 h-8 text-gold animate-spin" />
          <p className="text-sm text-white/60">Analyzing clauses, liabilities, and legal obligations with AI Engine...</p>
        </div>
      )}

      {!loading && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Left Column: Summary Card */}
          <div className="md:col-span-1 space-y-4">
            <div className="glass p-5 rounded-xl border border-white/5 bg-white/5">
              <h3 className="text-sm font-medium text-white/70 uppercase tracking-wider mb-4">Summary</h3>
              <div className="space-y-4">
                <div>
                  <div className="text-2xl font-bold text-ivory">{summaryData.score}%</div>
                  <div className="text-xs text-white/50">Favorability Score</div>
                </div>
                <div className="w-full bg-white/10 rounded-full h-1.5">
                  <div className="bg-gold h-1.5 rounded-full" style={{ width: `${summaryData.score}%` }}></div>
                </div>
              </div>

              <div className="mt-6 space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/60">Critical Risks</span>
                  <span className="text-burgundy font-bold">{summaryData.criticalCount}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/60">Warnings</span>
                  <span className="text-gold font-bold">{summaryData.warningCount}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/60">Standard Terms</span>
                  <span className="text-green-400 font-bold">{summaryData.standardCount}</span>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-white/5">
                <span className="text-[11px] text-white/40 block leading-relaxed">
                  Generated via Gemini AI structured analysis. Always verify important legal citations with counsel.
                </span>
              </div>
            </div>
          </div>

          {/* Right Column: Accordion Sections */}
          <div className="md:col-span-3 space-y-4">
            {analysisResults.map((section, idx) => (
              <div key={idx} className="glass rounded-xl border border-white/5 bg-white/5 overflow-hidden">
                <button
                  onClick={() => setExpanded(expanded === idx ? null : idx)}
                  className="w-full px-6 py-4 flex items-center justify-between bg-white/5 hover:bg-white/10 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <FileSearch className="w-5 h-5 text-gold" />
                    <h3 className="text-lg font-medium text-ivory">{section.category}</h3>
                  </div>
                  <ChevronDown
                    className={`w-5 h-5 text-white/50 transition-transform ${
                      expanded === idx ? "rotate-180" : ""
                    }`}
                  />
                </button>

                {expanded === idx && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className="px-6 pb-6 pt-2 border-t border-white/5"
                  >
                    <div className="space-y-4 mt-4">
                      {section.items.map((item, i) => (
                        <div key={i} className="p-4 rounded-lg bg-charcoal/50 border border-white/5 flex gap-4">
                          <div className="pt-0.5">
                            {item.status === "Critical" && <AlertTriangle className="w-5 h-5 text-burgundy shrink-0" />}
                            {item.status === "Warning" && <AlertTriangle className="w-5 h-5 text-gold shrink-0" />}
                            {item.status === "Standard" && <CheckCircle className="w-5 h-5 text-green-400 shrink-0" />}
                          </div>
                          <div className="flex-1">
                            <h4 className="text-sm font-semibold text-ivory mb-1">{item.term}</h4>
                            <p className="text-sm text-white/70 leading-relaxed whitespace-pre-line">{item.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
