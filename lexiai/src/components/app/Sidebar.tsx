"use client";

import { motion } from "framer-motion";
import { 
  BarChart3, 
  Briefcase, 
  FileSearch, 
  FileText, 
  LayoutDashboard, 
  MessageSquare, 
  Settings, 
  ShieldAlert, 
  Upload, 
  User
} from "lucide-react";
import { useEffect, useState } from "react";
import { apiFetch, getAuthToken } from "@/lib/api";
import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const navItems = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Documents", href: "/documents", icon: FileText },
  { name: "Upload", href: "/upload", icon: Upload },
  { name: "Analysis", href: "/analysis", icon: FileSearch },
  { name: "Risk Analysis", href: "/risk-analysis", icon: ShieldAlert },
  { name: "Case Recommendation", href: "/case-recommendation", icon: Briefcase },
  { name: "Document Comparison", href: "/comparison", icon: FileText },
  { name: "Ask LEXIAI", href: "/ask", icon: MessageSquare },
  { name: "Reports", href: "/reports", icon: BarChart3 },
];

const bottomNavItems = [
  { name: "Profile", href: "/profile", icon: User },
  { name: "Settings", href: "/settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [userName, setUserName] = useState("Counsel");
  const [userRole, setUserRole] = useState("Legal Workspace");

  useEffect(() => {
    const token = getAuthToken();
    if (!token) return;

    apiFetch("/api/v1/auth/me")
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data && data.email) {
          const namePart = data.email.split("@")[0];
          setUserName(namePart.charAt(0).toUpperCase() + namePart.slice(1));
          setUserRole(data.email);
        }
      })
      .catch(() => {});
  }, []);

  return (
    <div className="w-64 h-screen border-r border-white/5 bg-charcoal/80 backdrop-blur-xl hidden flex-col md:flex sticky top-0">
      <div className="p-6">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gold text-charcoal rounded-md flex items-center justify-center font-serif font-bold text-xl">
            L
          </div>
          <span className="text-xl font-serif font-semibold text-ivory tracking-wider">LEXIAI</span>
        </Link>
      </div>

      <div className="flex-1 overflow-y-auto py-4 px-3 flex flex-col gap-1 no-scrollbar">
        <div className="text-xs font-semibold text-white/30 uppercase tracking-widest px-3 mb-2">
          Workspace
        </div>
        
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          
          return (
            <Link key={item.href} href={item.href}>
              <motion.div
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.98 }}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200",
                  isActive 
                    ? "bg-gold/10 text-gold font-medium" 
                    : "text-white/60 hover:text-ivory hover:bg-white/5"
                )}
              >
                <Icon className={clsx("w-4 h-4", isActive ? "text-gold" : "text-white/40")} />
                {item.name}
              </motion.div>
            </Link>
          );
        })}

        <div className="mt-8 mb-2 text-xs font-semibold text-white/30 uppercase tracking-widest px-3">
          Preferences
        </div>
        
        {bottomNavItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          
          return (
            <Link key={item.href} href={item.href}>
              <motion.div
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.98 }}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200",
                  isActive 
                    ? "bg-gold/10 text-gold font-medium" 
                    : "text-white/60 hover:text-ivory hover:bg-white/5"
                )}
              >
                <Icon className={clsx("w-4 h-4", isActive ? "text-gold" : "text-white/40")} />
                {item.name}
              </motion.div>
            </Link>
          );
        })}
      </div>
      
      <div className="p-4 border-t border-white/5">
        <Link href="/profile">
          <div className="flex items-center gap-3 p-2 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors cursor-pointer">
            <div className="w-8 h-8 rounded-full bg-navy border border-gold/30 flex items-center justify-center shrink-0">
              <User className="w-4 h-4 text-gold" />
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-medium text-ivory truncate">{userName}</p>
              <p className="text-[11px] text-white/40 truncate">{userRole}</p>
            </div>
          </div>
        </Link>
      </div>
    </div>
  );
}

