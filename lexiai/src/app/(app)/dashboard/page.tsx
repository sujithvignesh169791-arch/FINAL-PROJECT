"use client";

import { motion } from "framer-motion";
import { ArrowUpRight, BarChart3, Clock, FileText, Scale, Upload, MessageSquare, FileSearch, Loader2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, getAuthToken } from "@/lib/api";

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [userName, setUserName] = useState("Counsel");
  const [docsCount, setDocsCount] = useState(0);
  const [activeCasesCount, setActiveCasesCount] = useState(0);
  const [riskAlertsCount, setRiskAlertsCount] = useState(0);
  const [recentDocs, setRecentDocs] = useState<any[]>([]);

  useEffect(() => {
    const loadDashboardData = async () => {
      const token = getAuthToken();
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        // Fetch current user info
        const userRes = await apiFetch("/api/v1/auth/me").catch(() => null);
        if (userRes && userRes.ok) {
          const userData = await userRes.json();
          const emailName = userData.email ? userData.email.split("@")[0] : "Counsel";
          setUserName(emailName.charAt(0).toUpperCase() + emailName.slice(1));
        }

        // Fetch documents
        const docsRes = await apiFetch("/api/v1/documents");
        if (docsRes.ok) {
          const docs = await docsRes.json();
          if (Array.isArray(docs)) {
            const completed = docs.filter((d: any) => d.upload_status === "completed");
            setDocsCount(completed.length);
            setActiveCasesCount(docs.length);

            // Sort recent docs by created_at desc
            const sorted = [...docs].sort((a: any, b: any) => 
              new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
            );
            setRecentDocs(sorted.slice(0, 5));
          }
        }

        // Fetch risk summary
        const riskRes = await apiFetch("/api/v1/risk/summary").catch(() => null);
        if (riskRes && riskRes.ok) {
          const riskData = await riskRes.json();
          setRiskAlertsCount(riskData.critical_risk_count || 0);
        }
      } catch (err) {
        console.error("Failed to load dashboard metrics:", err);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  const stats = [
    {
      title: "Active Legal Matters",
      value: String(activeCasesCount),
      change: `${docsCount} fully indexed`,
      icon: Scale,
      alert: false
    },
    {
      title: "Documents Analyzed",
      value: String(docsCount),
      change: "AI Structured Review",
      icon: FileText,
      alert: false
    },
    {
      title: "Critical Risk Alerts",
      value: String(riskAlertsCount),
      change: riskAlertsCount > 0 ? "Requires review" : "Optimal governance",
      icon: BarChart3,
      alert: riskAlertsCount > 0
    },
  ];

  return (
    <div className="space-y-8 pb-10">
      <div>
        <h1 className="text-3xl font-serif font-semibold text-ivory mb-2">Dashboard</h1>
        <p className="text-white/50">
          Welcome back, {userName}. Here's the live overview of your legal portfolio and database.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              className={`glass p-6 rounded-2xl border ${stat.alert ? 'border-burgundy/30 bg-burgundy/5' : 'border-white/5 bg-white/5'} flex flex-col`}
            >
              <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-xl ${stat.alert ? 'bg-burgundy/20 text-burgundy' : 'bg-gold/10 text-gold'}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <ArrowUpRight className="w-4 h-4 text-white/30" />
              </div>
              <h3 className="text-3xl font-semibold text-ivory mb-1">
                {loading ? <Loader2 className="w-6 h-6 animate-spin text-gold" /> : stat.value}
              </h3>
              <p className="text-sm text-white/50 mb-2">{stat.title}</p>
              <span className={`text-xs font-medium ${stat.alert ? 'text-burgundy' : 'text-gold/80'}`}>
                {stat.change}
              </span>
            </motion.div>
          );
        })}
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <div className="lg:col-span-2 glass rounded-2xl border border-white/5 p-6 bg-white/5">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-ivory">Recent Activity & Ingested Files</h2>
            <Link href="/documents" className="text-sm text-gold hover:text-gold/80 transition-colors">
              View All Documents &rarr;
            </Link>
          </div>
          
          <div className="space-y-4">
            {loading ? (
              <div className="py-12 flex justify-center items-center">
                <Loader2 className="w-6 h-6 animate-spin text-gold" />
              </div>
            ) : recentDocs.length === 0 ? (
              <div className="p-8 text-center border border-white/5 rounded-xl bg-charcoal/30">
                <FileText className="w-8 h-8 text-white/30 mx-auto mb-2" />
                <p className="text-sm text-white/60 mb-3">No documents in database yet.</p>
                <Link href="/upload" className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-gold text-charcoal hover:bg-gold/90 transition-colors inline-block">
                  Upload First Document
                </Link>
              </div>
            ) : (
              recentDocs.map((doc, i) => (
                <Link key={doc.id || i} href={`/analysis?docId=${doc.id}`}>
                  <motion.div 
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 + (i * 0.05) }}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors cursor-pointer group mb-3"
                  >
                    <div className="flex items-start gap-4 mb-3 sm:mb-0">
                      <div className="p-2 rounded-lg bg-navy text-gold mt-1">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-ivory group-hover:text-gold transition-colors">{doc.filename}</h4>
                        <p className="text-xs text-white/50">{doc.file_type ? doc.file_type.toUpperCase() : "PDF"} Document &bull; Database Record</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4 sm:flex-col sm:items-end justify-between sm:justify-center ml-12 sm:ml-0">
                      <span className={`text-xs px-2.5 py-1 rounded-full ${
                        doc.upload_status === 'completed' 
                          ? 'bg-green-500/10 text-green-400 border border-green-500/20' 
                          : doc.upload_status === 'processing'
                          ? 'bg-gold/10 text-gold border border-gold/20'
                          : 'bg-burgundy/10 text-burgundy border border-burgundy/20'
                      }`}>
                        {doc.upload_status === 'completed' ? 'Analyzed' : doc.upload_status}
                      </span>
                      <div className="flex items-center gap-1 text-xs text-white/40">
                        <Clock className="w-3 h-3" />
                        {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : "Recent"}
                      </div>
                    </div>
                  </motion.div>
                </Link>
              ))
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="glass rounded-2xl border border-white/5 p-6 bg-white/5 flex flex-col">
          <h2 className="text-lg font-semibold text-ivory mb-6">Quick Actions</h2>
          <div className="space-y-3 flex-1">
            <Link href="/upload">
              <div className="w-full text-left p-4 rounded-xl bg-gold/10 border border-gold/20 hover:bg-gold/20 transition-all flex items-center gap-3 group mb-3">
                <div className="p-2 rounded-lg bg-gold/20 text-gold">
                  <Upload className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gold">Upload Document</h4>
                  <p className="text-xs text-gold/60 mt-0.5">Start a new analysis</p>
                </div>
              </div>
            </Link>

            <Link href="/ask">
              <div className="w-full text-left p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all flex items-center gap-3 group mb-3">
                <div className="p-2 rounded-lg bg-white/10 text-ivory">
                  <MessageSquare className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-ivory">Ask LEXIAI</h4>
                  <p className="text-xs text-white/50 mt-0.5">Chat with legal assistant</p>
                </div>
              </div>
            </Link>

            <Link href="/comparison">
              <div className="w-full text-left p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all flex items-center gap-3 group">
                <div className="p-2 rounded-lg bg-white/10 text-ivory">
                  <FileSearch className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-ivory">Compare Versions</h4>
                  <p className="text-xs text-white/50 mt-0.5">Find changes across docs</p>
                </div>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
