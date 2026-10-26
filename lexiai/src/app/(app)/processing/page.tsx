"use client";

import { motion } from "framer-motion";
import { FileText, Loader2, CheckCircle, Database } from "lucide-react";
import { useEffect, useState } from "react";
import Link from "next/link";

export default function ProcessingPage() {
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState(0);

  const steps = [
    { title: "Extracting Text (OCR)", desc: "Parsing document structure and contents." },
    { title: "Semantic Analysis", desc: "Identifying key entities, obligations, and dates." },
    { title: "Risk Assessment", desc: "Comparing against standard playbooks and precedents." },
    { title: "Finalizing Report", desc: "Generating comprehensive analysis summary." }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(timer);
          return 100;
        }
        
        // Update steps based on progress
        if (prev > 75) setStep(3);
        else if (prev > 50) setStep(2);
        else if (prev > 25) setStep(1);
        
        return prev + 1;
      });
    }, 100);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-8rem)] max-w-2xl mx-auto text-center space-y-8">
      
      {/* Visual Indicator */}
      <div className="relative w-40 h-40 flex items-center justify-center">
        <svg className="absolute inset-0 w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          <circle 
            className="text-white/5 stroke-current" 
            strokeWidth="4" 
            cx="50" 
            cy="50" 
            r="48" 
            fill="transparent" 
          />
          <motion.circle 
            className="text-gold stroke-current" 
            strokeWidth="4" 
            strokeLinecap="round"
            cx="50" 
            cy="50" 
            r="48" 
            fill="transparent"
            initial={{ strokeDasharray: "0 300" }}
            animate={{ strokeDasharray: `${progress * 3} 300` }}
            transition={{ duration: 0.1 }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center flex-col">
          {progress < 100 ? (
            <>
              <span className="text-3xl font-bold text-ivory">{progress}%</span>
            </>
          ) : (
            <CheckCircle className="w-12 h-12 text-green-400" />
          )}
        </div>
      </div>

      <div>
        <h1 className="text-2xl font-serif font-semibold text-ivory mb-2">
          {progress < 100 ? "Analyzing Document..." : "Analysis Complete"}
        </h1>
        <p className="text-white/50 text-sm max-w-md mx-auto">
          {progress < 100 
            ? "LEXIAI is processing Smith_v_TechCorp_Initial_Disclosure.pdf. This may take a few moments."
            : "The document has been successfully processed. You can now view the detailed analysis."}
        </p>
      </div>

      <div className="w-full glass p-6 rounded-2xl border border-white/5 bg-white/5 text-left">
        <div className="space-y-6">
          {steps.map((s, i) => (
            <div key={i} className="flex gap-4">
              <div className="mt-1">
                {step > i ? (
                  <CheckCircle className="w-5 h-5 text-green-400" />
                ) : step === i ? (
                  <Loader2 className="w-5 h-5 text-gold animate-spin" />
                ) : (
                  <div className="w-5 h-5 rounded-full border-2 border-white/10" />
                )}
              </div>
              <div>
                <h4 className={`text-sm font-medium ${step >= i ? 'text-ivory' : 'text-white/40'}`}>
                  {s.title}
                </h4>
                <p className="text-xs text-white/50 mt-1">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {progress === 100 && (
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex gap-4 pt-4"
        >
          <Link href="/documents">
            <button className="px-6 py-2.5 rounded-lg border border-white/10 text-white/70 hover:text-ivory hover:bg-white/5 transition-all text-sm font-medium">
              Back to Documents
            </button>
          </Link>
          <Link href="/analysis">
            <button className="px-6 py-2.5 rounded-lg bg-gold text-charcoal hover:bg-gold/90 transition-all text-sm font-semibold shadow-[0_0_15px_rgba(212,175,55,0.2)]">
              View Analysis
            </button>
          </Link>
        </motion.div>
      )}
    </div>
  );
}
