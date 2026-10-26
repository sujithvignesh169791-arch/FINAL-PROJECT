"use client";

import { motion } from "framer-motion";
import { Activity, AlertOctagon, TrendingUp, ShieldAlert, CheckCircle, Loader2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, getAuthToken } from "@/lib/api";

export default function RiskAnalysisPage() {
  const [loading, setLoading] = useState(true);
  const [riskData, setRiskData] = useState<any>({
    portfolio_risk_level: "Moderate",
    average_risk_score: 76.0,
    total_documents: 0,
    critical_risk_count: 0,
    warning_risk_count: 0,
    risk_timeline: [70, 72, 75, 76, 78, 76, 75, 77, 76, 78, 75, 76],
    critical_risk_areas: []
  });

  useEffect(() => {
    const fetchRiskSummary = async () => {
      const token = getAuthToken();
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const res = await apiFetch("/api/v1/risk/summary");
        if (res.ok) {
          const data = await res.json();
          setRiskData(data);
        }
      } catch (err) {
        console.error("Failed to load risk analysis data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchRiskSummary();
  }, []);

  const getRiskColor = (level: string) => {
    if (level === "High") return "text-burgundy";
    if (level === "Moderate") return "text-gold";
    return "text-green-400";
  };

  return (
    <div className="space-y-6 pb-10 max-w-6xl mx-auto">
      <div>
        <h1 className="text-3xl font-serif font-semibold text-ivory mb-2">Risk Analysis</h1>
        <p className="text-white/50">
          Real-time risk assessment and exposure metrics aggregated across your database portfolio.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Risk Card */}
        <div className="glass p-6 rounded-2xl border border-burgundy/30 bg-burgundy/5 flex flex-col items-center justify-center text-center">
          <AlertOctagon className={`w-10 h-10 mb-4 ${getRiskColor(riskData.portfolio_risk_level)}`} />
          <h3 className="text-4xl font-bold text-ivory mb-1">
            {loading ? <Loader2 className="w-8 h-8 animate-spin text-gold" /> : riskData.portfolio_risk_level}
          </h3>
          <p className={`text-sm font-medium uppercase tracking-wider ${getRiskColor(riskData.portfolio_risk_level)}`}>
            Overall Portfolio Risk
          </p>
          <div className="mt-4 pt-3 border-t border-white/5 text-xs text-white/50">
            Average Score: <span className="font-semibold text-ivory">{riskData.average_risk_score}%</span> across {riskData.total_documents} matters
          </div>
        </div>
        
        {/* Risk Factors Over Time Chart */}
        <div className="md:col-span-2 glass p-6 rounded-2xl border border-white/5 bg-white/5">
          <h3 className="text-lg font-semibold text-ivory mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-gold" />
            Portfolio Favorability Timeline
          </h3>
          <div className="h-48 flex items-end gap-2 mt-8">
            {riskData.risk_timeline.map((val: number, i: number) => (
              <motion.div 
                key={i}
                initial={{ height: 0 }}
                animate={{ height: `${val}%` }}
                transition={{ delay: i * 0.04 }}
                title={`Score: ${val}%`}
                className={`flex-1 rounded-t-sm opacity-80 hover:opacity-100 transition-opacity ${
                  val < 60 ? 'bg-burgundy' : val < 80 ? 'bg-gold' : 'bg-green-400'
                }`}
              />
            ))}
          </div>
          <div className="flex justify-between mt-4 text-xs text-white/40">
            <span>Historical Ingestion</span>
            <span>Active Reviews</span>
            <span>Current Benchmark</span>
          </div>
        </div>
      </div>

      <h3 className="text-xl font-serif font-semibold text-ivory mt-8 mb-4">Critical Risk Areas Identified</h3>
      
      {loading ? (
        <div className="p-12 glass rounded-2xl border border-white/5 flex justify-center items-center">
          <Loader2 className="w-8 h-8 animate-spin text-gold" />
        </div>
      ) : riskData.critical_risk_areas.length === 0 ? (
        <div className="p-8 glass rounded-2xl border border-white/5 text-center text-white/50">
          No critical risks detected. All contracts and documents adhere to standard covenants.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {riskData.critical_risk_areas.map((risk: any, i: number) => {
            const isCrit = risk.severity === "Critical";
            const Icon = isCrit ? ShieldAlert : risk.severity === "Warning" ? AlertOctagon : CheckCircle;
            return (
              <motion.div 
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className={`glass p-6 rounded-2xl border ${risk.bg} flex gap-4`}
              >
                <div className="pt-1">
                  <Icon className={`w-6 h-6 ${risk.color}`} />
                </div>
                <div className="flex-1">
                  <h4 className="text-lg font-medium text-ivory mb-1">{risk.title}</h4>
                  <p className="text-sm text-white/60 leading-relaxed mb-4">{risk.desc}</p>
                  <Link href="/documents">
                    <button className={`text-xs font-semibold uppercase tracking-wider ${risk.color} hover:underline`}>
                      View Affected Documents &rarr;
                    </button>
                  </Link>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
