import Link from "next/link";
import { Globe, MessageCircle, Mail } from "lucide-react";

export default function Footer() {
  return (
    <footer className="relative border-t border-white/5 pt-20 pb-10 section-crossfade">
      <div className="absolute inset-0 bg-[var(--color-charcoal)]/80 backdrop-blur-md"></div>
      <div className="container relative z-10 mx-auto px-6 md:px-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
          <div className="md:col-span-1">
            <Link href="/" className="text-3xl font-serif text-[var(--color-ivory)] mb-6 inline-block">
              Lex<span className="text-[var(--color-gold)]">Nova</span>
            </Link>
            <p className="text-[var(--color-ivory)]/60 text-sm leading-relaxed mb-6 max-w-xs">
              A premium digital platform for lawyers, legal professionals, and law students. Where legal excellence meets modern practice.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="text-[var(--color-ivory)]/60 hover:text-[var(--color-gold)] transition-colors">
                <Globe size={20} />
              </a>
              <a href="#" className="text-[var(--color-ivory)]/60 hover:text-[var(--color-gold)] transition-colors">
                <MessageCircle size={20} />
              </a>
              <a href="#" className="text-[var(--color-ivory)]/60 hover:text-[var(--color-gold)] transition-colors">
                <Mail size={20} />
              </a>
            </div>
          </div>
          
          <div>
            <h4 className="text-[var(--color-ivory)] font-serif text-lg mb-6 tracking-wide">Practice Areas</h4>
            <ul className="space-y-3 text-sm text-[var(--color-ivory)]/60">
              <li><Link href="#" className="hover:text-[var(--color-gold)] transition-colors">Corporate Law</Link></li>
              <li><Link href="#" className="hover:text-[var(--color-gold)] transition-colors">Litigation</Link></li>
              <li><Link href="#" className="hover:text-[var(--color-gold)] transition-colors">Intellectual Property</Link></li>
              <li><Link href="#" className="hover:text-[var(--color-gold)] transition-colors">Family Law</Link></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-[var(--color-ivory)] font-serif text-lg mb-6 tracking-wide">Resources</h4>
            <ul className="space-y-3 text-sm text-[var(--color-ivory)]/60">
              <li><Link href="#" className="hover:text-[var(--color-gold)] transition-colors">For Lawyers</Link></li>
              <li><Link href="#" className="hover:text-[var(--color-gold)] transition-colors">For Students</Link></li>
              <li><Link href="#" className="hover:text-[var(--color-gold)] transition-colors">Insights & Journal</Link></li>
              <li><Link href="#" className="hover:text-[var(--color-gold)] transition-colors">Case Studies</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-[var(--color-ivory)] font-serif text-lg mb-6 tracking-wide">Newsletter</h4>
            <p className="text-[var(--color-ivory)]/60 text-sm mb-4">
              Subscribe to receive curated legal insights and platform updates.
            </p>
            <form className="flex flex-col space-y-3">
              <input 
                type="email" 
                placeholder="Email Address" 
                className="bg-white/5 border border-white/10 px-4 py-2 text-sm text-[var(--color-ivory)] focus:outline-none focus:border-[var(--color-gold)]/50 transition-colors"
              />
              <button 
                type="submit" 
                className="bg-[var(--color-ivory)] text-[var(--color-navy)] px-4 py-2 text-sm uppercase tracking-widest font-medium hover:bg-[var(--color-gold)] transition-colors"
              >
                Subscribe
              </button>
            </form>
          </div>
        </div>
        
        <div className="border-t border-white/5 pt-8 flex flex-col md:flex-row justify-between items-center text-xs text-[var(--color-ivory)]/40 uppercase tracking-widest">
          <p>&copy; {new Date().getFullYear()} LexNova. All Rights Reserved.</p>
          <div className="flex space-x-6 mt-4 md:mt-0">
            <Link href="#" className="hover:text-[var(--color-ivory)]/80 transition-colors">Privacy Policy</Link>
            <Link href="#" className="hover:text-[var(--color-ivory)]/80 transition-colors">Terms of Service</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
