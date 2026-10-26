"use client";

import { motion } from "framer-motion";
import { ArrowLeft, Lock, Mail, Scale } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    // Implementation placeholder
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center relative overflow-hidden bg-charcoal">
      {/* Background elements */}
      <div className="absolute top-[20%] left-[-10%] w-[40%] h-[40%] bg-gold/10 rounded-full blur-[120px]" />
      <div className="absolute bottom-[10%] right-[-10%] w-[50%] h-[50%] bg-navy/20 rounded-full blur-[120px]" />

      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="w-full max-w-md p-8 md:p-10 glass-dark rounded-2xl z-10 mx-4 shadow-2xl border border-white/5"
      >
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-gold/10 text-gold rounded-full flex items-center justify-center mb-4 border border-gold/20">
            <Lock className="w-6 h-6" />
          </div>
          <h1 className="text-3xl font-serif font-semibold text-ivory mb-2">Reset Password</h1>
          <p className="text-white/50 text-sm text-center">Enter your email to receive recovery instructions</p>
        </div>

        {!submitted ? (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label className="text-xs font-medium text-white/70 uppercase tracking-wider">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg py-3 pl-10 pr-4 placeholder-white/30 focus:outline-none focus:ring-1 focus:ring-gold/50 transition-all"
                  placeholder="counsel@firm.com"
                  required
                />
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              type="submit"
              className="w-full bg-gold text-charcoal font-semibold py-3 rounded-lg mt-6 flex items-center justify-center gap-2 hover:bg-gold/90 transition-all shadow-[0_0_20px_rgba(212,175,55,0.2)]"
            >
              Send Instructions
            </motion.button>
          </form>
        ) : (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center p-4 bg-white/5 border border-white/10 rounded-lg"
          >
            <p className="text-ivory font-medium mb-1">Check your inbox</p>
            <p className="text-sm text-white/50">We've sent password reset instructions to {email}</p>
          </motion.div>
        )}

        <div className="mt-8 text-center">
          <Link href="/login" className="inline-flex items-center gap-2 text-sm text-gold hover:text-gold/80 font-medium transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to login
          </Link>
        </div>
      </motion.div>
    </div>
  );
}

