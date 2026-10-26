"use client";

import { motion } from "framer-motion";
import { Briefcase, ChevronRight, Gavel, Scale, Loader2, FileText } from "lucide-react";
import { useEffect, useState } from "react";
import { apiFetch, getAuthToken } from "@/lib/api";

export default function CaseRecommendationPage() {
  const [loading, setLoading] = useState(true);
  const [caseData, setCaseData] = useState<any>({
    active_document: null,
    legal_context: "Loading legal context from database...",
    matter_type: "Corporate & Judicial",
    available_documents: [],
    precedents: []
  });
  const [selectedDocId, setSelectedDocId] = useState<string>("");

  const fetchRecommendations = async (docId?: string) => {
    setLoading(true);
    const token = getAuthToken();
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const endpoint = docId ? `/api/v1/cases/recommendations?doc_id=${docId}` : `/api/v1/cases/recommendations`;
      const res = await apiFetch(endpoint);
      if (res.ok) {
        const data = await res.json();
        setCaseData(data);
        if (data.active_document && !selectedDocId) {
          setSelectedDocId(data.active_document.id);
        }
      }
    } catch (err) {
      console.error("Failed to load case recommendations:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const handleDocChange = (id: string) => {
    setSelectedDocId(id);
    fetchRecommendations(id);
  };

  return (
    <div className="space-y-6 pb-10 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-serif font-semibold text-ivory mb-2">Case Recommendation</h1>
          <p className="text-white/50">AI & database-matched precedents and case laws tailored to your uploaded matters.</p>
        </div>

        {caseData.available_documents?.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-white/40">Matter:</span>
            <select
              value={selectedDocId}
              onChange={(e) => handleDocChange(e.target.value)}
              className="px-3 py-2 rounded-lg bg-charcoal/80 border border-white/10 text-ivory text-sm focus:outline-none focus:ring-1 focus:ring-gold"
            >
              {caseData.available_documents.map((d: any) => (
                <option key={d.id} value={d.id} className="bg-charcoal text-ivory">
                  {d.filename}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {loading ? (
        <div className="p-12 glass rounded-2xl border border-white/5 flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 text-gold animate-spin" />
          <p className="text-sm text-white/50">Matching database matter with judicial precedents...</p>
        </div>
      ) : (
        <>
          <div className="glass p-6 rounded-2xl border border-white/5 bg-white/5 mb-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-ivory">
                Context: {caseData.active_document ? caseData.active_document.filename : "Active Legal Matter"}
              </h3>
              <span className="text-xs font-medium bg-gold/10 text-gold px-3 py-1 rounded-full border border-gold/20">
                {caseData.matter_type}
              </span>
            </div>
            <p className="text-sm text-white/60 leading-relaxed max-w-3xl">
              {caseData.legal_context}
            </p>
          </div>

          <h3 className="text-xl font-serif font-semibold text-ivory mb-4">Recommended Precedents & Authorities</h3>

          <div className="space-y-4">
            {caseData.precedents?.length === 0 ? (
              <div className="p-8 text-center text-white/50 border border-white/5 rounded-xl">
                No precedent matches available. Upload relevant legal documents to populate recommendations.
              </div>
            ) : (
              caseData.precedents.map((precedent: any, i: number) => (
                <motion.div 
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="glass p-5 rounded-xl border border-white/5 bg-white/5 hover:bg-white/10 transition-colors group cursor-pointer"
                >
                  <div className="flex flex-col md:flex-row justify-between gap-4">
                    <div className="flex items-start gap-4">
                      <div className="mt-1 w-10 h-10 rounded-full bg-navy border border-white/10 flex items-center justify-center shrink-0">
                        <Gavel className="w-5 h-5 text-gold/70" />
                      </div>
                      <div>
                        <h4 className="text-lg font-medium text-ivory group-hover:text-gold transition-colors">{precedent.name}</h4>
                        <div className="flex items-center gap-3 text-xs text-white/40 mt-1 mb-2">
                          <span className="flex items-center gap-1"><Scale className="w-3 h-3" /> {precedent.court}</span>
                          <span>&bull;</span>
                          <span>{precedent.year}</span>
                        </div>
                        <p className="text-sm text-white/60">{precedent.desc}</p>
                      </div>
                    </div>
                    
                    <div className="flex md:flex-col items-center justify-between md:justify-center md:items-end md:w-32 shrink-0 border-t md:border-t-0 md:border-l border-white/10 pt-4 md:pt-0 md:pl-4 mt-2 md:mt-0">
                      <div className="text-center">
                        <span className="block text-2xl font-bold text-ivory">{precedent.match}</span>
                        <span className="text-[10px] text-white/50 uppercase tracking-wider">Match</span>
                      </div>
                      <ChevronRight className="w-5 h-5 text-white/30 group-hover:text-ivory md:mt-2 transition-colors" />
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
