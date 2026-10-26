"use client";

import { Bell, Menu, Search } from "lucide-react";
import { motion } from "framer-motion";

export default function AppHeader() {
  return (
    <header className="h-16 border-b border-white/5 bg-charcoal/80 backdrop-blur-xl flex items-center justify-between px-6 sticky top-0 z-30">
      <div className="flex items-center gap-4">
        <button className="md:hidden text-white/60 hover:text-ivory transition-colors">
          <Menu className="w-5 h-5" />
        </button>
        
        <div className="hidden md:flex relative items-center">
          <Search className="w-4 h-4 text-white/40 absolute left-3" />
          <input 
            type="text" 
            placeholder="Search cases, documents, analysis..." 
            className="bg-white/5 border border-white/10 rounded-full py-1.5 pl-9 pr-4 text-sm placeholder-white/30 focus:outline-none focus:ring-1 focus:ring-gold/50 transition-all w-64 lg:w-96"
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <motion.button 
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="relative p-2 text-white/60 hover:text-ivory transition-colors rounded-full hover:bg-white/5"
        >
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-burgundy rounded-full border border-charcoal"></span>
        </motion.button>
        
        <button className="bg-gold/10 text-gold border border-gold/20 px-4 py-1.5 rounded-full text-sm font-medium hover:bg-gold hover:text-charcoal transition-all">
          Upgrade Plan
        </button>
      </div>
    </header>
  );
}

