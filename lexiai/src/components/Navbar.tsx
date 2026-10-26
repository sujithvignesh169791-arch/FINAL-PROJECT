"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Menu, X } from "lucide-react";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { name: "Home", href: "/" },
    { name: "Practice Areas", href: "#practice-areas" },
    { name: "For Lawyers", href: "#for-lawyers" },
    { name: "For Students", href: "#for-students" },
    { name: "Insights", href: "#insights" },
    { name: "Community", href: "#community" },
  ];

  return (
    <header
      className={`fixed top-0 left-0 w-full z-50 transition-all duration-500 ${
        scrolled ? "py-4 glass-dark" : "py-6 bg-transparent"
      }`}
    >
      <div className="container mx-auto px-6 md:px-12 flex justify-between items-center">
        <Link href="/" className="text-2xl font-serif text-[var(--color-ivory)]">
          Lex<span className="text-[var(--color-gold)]">Nova</span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden lg:flex items-center space-x-8">
          {navLinks.map((link) => (
            <Link
              key={link.name}
              href={link.href}
              className="text-sm uppercase tracking-widest text-[var(--color-ivory)]/80 hover:text-[var(--color-gold)] transition-colors relative group"
            >
              {link.name}
              <span className="absolute -bottom-1 left-0 w-0 h-px bg-[var(--color-gold)] transition-all duration-300 group-hover:w-full"></span>
            </Link>
          ))}
        </nav>

        <div className="hidden lg:block">
          <button className="px-6 py-2 border border-[var(--color-gold)]/50 text-[var(--color-gold)] hover:bg-[var(--color-gold)] hover:text-[var(--color-navy)] transition-colors duration-300 text-sm uppercase tracking-widest">
            Get Started
          </button>
        </div>

        {/* Mobile Toggle */}
        <button
          className="lg:hidden text-[var(--color-ivory)]"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="lg:hidden absolute top-full left-0 w-full glass-dark py-6 flex flex-col items-center space-y-6"
        >
          {navLinks.map((link) => (
            <Link
              key={link.name}
              href={link.href}
              onClick={() => setMobileMenuOpen(false)}
              className="text-sm uppercase tracking-widest text-[var(--color-ivory)]"
            >
              {link.name}
            </Link>
          ))}
          <button className="px-6 py-2 border border-[var(--color-gold)] text-[var(--color-gold)] text-sm uppercase tracking-widest">
            Get Started
          </button>
        </motion.div>
      )}
    </header>
  );
}
