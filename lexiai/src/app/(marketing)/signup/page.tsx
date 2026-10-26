"use client";

import { motion } from "framer-motion";
import { ArrowRight, Lock, Mail, Scale, User } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

export default function SignupPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email,
          password: password,
          full_name: name
        }),
      });
      const data = await res.json();
      if (res.ok) {
        alert("Account created successfully! Please sign in.");
        window.location.href = "/login";
      } else {
        alert("Signup failed: " + (data.detail || "Unknown error"));
      }
    } catch (err) {
      alert("Signup failed: Could not connect to backend");
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center relative overflow-hidden bg-charcoal">
      {/* Background image from Stitch */}
      <div 
        className="absolute inset-0 z-0 opacity-20"
        style={{
          backgroundImage: "url('/images/library_background_1786025856264.png')",
          backgroundSize: "cover",
          backgroundPosition: "center"
        }}
      />
      <div className="absolute inset-0 bg-charcoal/80 z-0" />

      {/* Decorative blurs */}
      <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-burgundy/40 rounded-full blur-[120px] z-0" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-navy/30 rounded-full blur-[120px] z-0" />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="w-full max-w-md p-8 md:p-10 glass-dark rounded-2xl z-10 mx-4 shadow-2xl border border-white/5"
      >
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-gold/10 text-gold rounded-full flex items-center justify-center mb-4 border border-gold/20">
            <Scale className="w-6 h-6" />
          </div>
          <h1 className="text-3xl font-serif font-semibold text-ivory mb-2">Request Access</h1>
          <p className="text-white/50 text-sm text-center">Join LEXIAI's premier legal workspace</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="text-xs font-medium text-white/70 uppercase tracking-wider">Full Name</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg py-3 pl-10 pr-4 placeholder-white/30 focus:outline-none focus:ring-1 focus:ring-gold/50 transition-all"
                placeholder="Jane Doe"
                required
              />
            </div>
          </div>

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

          <div className="space-y-2">
            <label className="text-xs font-medium text-white/70 uppercase tracking-wider">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg py-3 pl-10 pr-4 placeholder-white/30 focus:outline-none focus:ring-1 focus:ring-gold/50 transition-all"
                placeholder="••••••••"
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
            Create Account
            <ArrowRight className="w-4 h-4" />
          </motion.button>
        </form>

        <p className="mt-8 text-center text-sm text-white/50">
          Already have an account?{" "}
          <Link href="/login" className="text-gold hover:text-gold/80 font-medium transition-colors">
            Sign in
          </Link>
        </p>
      </motion.div>
    </div>
  );
}

