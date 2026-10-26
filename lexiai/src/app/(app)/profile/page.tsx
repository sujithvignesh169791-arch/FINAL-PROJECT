"use client";

import { motion } from "framer-motion";
import { User } from "lucide-react";

export default function ProfilePage() {
  return (
    <div className="space-y-6 pb-10 max-w-3xl mx-auto">
      <div>
        <h1 className="text-3xl font-serif font-semibold text-ivory mb-2">Profile</h1>
        <p className="text-white/50">Manage your personal information and credentials.</p>
      </div>

      <div className="glass rounded-2xl border border-white/5 bg-white/5 overflow-hidden">
        <div className="p-6 sm:p-8 flex items-start gap-6 border-b border-white/5">
          <div className="w-24 h-24 rounded-full bg-navy border border-gold/30 flex items-center justify-center shrink-0 shadow-xl">
            <User className="w-10 h-10 text-gold" />
          </div>
          <div>
            <h2 className="text-2xl font-medium text-ivory">Jane Doe, Esq.</h2>
            <p className="text-gold/80 mb-4 text-sm font-medium">Senior Counsel &bull; Corporate Litigation</p>
            <div className="flex gap-3">
              <button className="px-4 py-2 rounded-lg bg-gold text-charcoal text-xs font-semibold hover:bg-gold/90 transition-colors">
                Upload Photo
              </button>
              <button className="px-4 py-2 rounded-lg border border-white/10 text-white/70 hover:text-ivory hover:bg-white/10 text-xs font-medium transition-colors">
                Remove
              </button>
            </div>
          </div>
        </div>
        
        <div className="p-6 sm:p-8 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-xs font-medium text-white/50 uppercase tracking-wider">First Name</label>
              <input type="text" defaultValue="Jane" className="w-full bg-charcoal/50 border border-white/10 rounded-lg py-2.5 px-4 text-sm text-ivory focus:outline-none" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Last Name</label>
              <input type="text" defaultValue="Doe" className="w-full bg-charcoal/50 border border-white/10 rounded-lg py-2.5 px-4 text-sm text-ivory focus:outline-none" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Email Address</label>
              <input type="email" defaultValue="jane.doe@firm.com" className="w-full bg-charcoal/50 border border-white/10 rounded-lg py-2.5 px-4 text-sm text-ivory focus:outline-none" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Bar Number</label>
              <input type="text" defaultValue="NY-943021" className="w-full bg-charcoal/50 border border-white/10 rounded-lg py-2.5 px-4 text-sm text-ivory focus:outline-none" />
            </div>
          </div>
          
          <div className="pt-4 border-t border-white/5 flex justify-end">
            <button className="px-6 py-2.5 rounded-lg bg-gold text-charcoal hover:bg-gold/90 transition-all text-sm font-semibold shadow-[0_0_15px_rgba(212,175,55,0.2)]">
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

