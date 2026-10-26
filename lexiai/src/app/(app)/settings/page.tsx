"use client";

import { motion } from "framer-motion";
import { Bell, Lock, Monitor, Shield } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-6 pb-10 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-serif font-semibold text-ivory mb-2">Settings</h1>
        <p className="text-white/50">Manage workspace preferences, security, and notifications.</p>
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        {/* Settings Navigation */}
        <div className="w-full md:w-64 shrink-0 space-y-1">
          {[
            { icon: Monitor, label: "Appearance", active: true },
            { icon: Bell, label: "Notifications", active: false },
            { icon: Shield, label: "Privacy & Data", active: false },
            { icon: Lock, label: "Security", active: false },
          ].map((item, i) => (
            <button 
              key={i} 
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-colors ${
                item.active 
                  ? 'bg-gold/10 text-gold font-medium border border-gold/20' 
                  : 'text-white/60 hover:bg-white/5 hover:text-ivory border border-transparent'
              }`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </button>
          ))}
        </div>

        {/* Settings Content */}
        <div className="flex-1 glass rounded-2xl border border-white/5 bg-white/5 overflow-hidden">
          <div className="p-6 border-b border-white/5">
            <h2 className="text-xl font-medium text-ivory">Appearance</h2>
            <p className="text-sm text-white/50 mt-1">Customize how LEXIAI looks on your device.</p>
          </div>
          
          <div className="p-6 space-y-8">
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-white/70 uppercase tracking-wider">Theme</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="border-2 border-gold rounded-xl p-4 cursor-pointer relative overflow-hidden bg-charcoal">
                  <div className="absolute inset-0 bg-linear-to-br from-white/5 to-transparent"></div>
                  <div className="h-20 bg-white/5 rounded border border-white/10 mb-2"></div>
                  <p className="text-xs text-center text-ivory font-medium">Dark (Default)</p>
                  <div className="absolute top-2 right-2 w-4 h-4 rounded-full bg-gold flex items-center justify-center">
                    <div className="w-1.5 h-1.5 rounded-full bg-charcoal"></div>
                  </div>
                </div>
                <div className="border border-white/10 hover:border-white/30 rounded-xl p-4 cursor-pointer relative overflow-hidden bg-[#FDFBF7]">
                  <div className="h-20 bg-black/5 rounded border border-black/10 mb-2"></div>
                  <p className="text-xs text-center text-charcoal font-medium">Light</p>
                </div>
                <div className="border border-white/10 hover:border-white/30 rounded-xl p-4 cursor-pointer relative overflow-hidden bg-charcoal/50">
                  <div className="h-20 bg-linear-to-r from-charcoal to-[#FDFBF7] rounded border border-white/10 mb-2 opacity-50"></div>
                  <p className="text-xs text-center text-ivory font-medium">System</p>
                </div>
              </div>
            </div>

            <div className="space-y-4 pt-6 border-t border-white/5">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-ivory">Compact Mode</h3>
                  <p className="text-xs text-white/50 mt-1">Reduce spacing in tables and lists to fit more content.</p>
                </div>
                <div className="w-12 h-6 bg-white/10 rounded-full relative cursor-pointer">
                  <div className="absolute left-1 top-1 w-4 h-4 bg-white/40 rounded-full"></div>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-ivory">High Contrast Text</h3>
                  <p className="text-xs text-white/50 mt-1">Increase contrast for better readability.</p>
                </div>
                <div className="w-12 h-6 bg-gold rounded-full relative cursor-pointer">
                  <div className="absolute right-1 top-1 w-4 h-4 bg-charcoal rounded-full"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

