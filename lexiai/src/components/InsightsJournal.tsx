"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import ParallaxBackground from "./ParallaxBackground";

export default function InsightsJournal() {
  const sectionRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    
    if (sectionRef.current) {
      const ctx = gsap.context(() => {
        gsap.fromTo(
          headerRef.current,
          { y: 30, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 1,
            ease: "power2.out",
            scrollTrigger: {
              trigger: sectionRef.current,
              start: "top 80%",
            }
          }
        );

        gsap.fromTo(
          ".article-card",
          { y: 40, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.8,
            stagger: 0.2,
            ease: "power2.out",
            scrollTrigger: {
              trigger: sectionRef.current,
              start: "top 70%",
            }
          }
        );
      }, sectionRef);

      return () => ctx.revert();
    }
  }, []);

  return (
    <section id="insights" ref={sectionRef} className="py-32 relative section-crossfade">
      
      <ParallaxBackground 
        imageSrc="/images/journal_background_1786026306732.png" 
        alt="Antique law journal"
        overlayOpacity={0.85}
        intensity={0.2}
      />

      <div className="container mx-auto px-6 md:px-12 relative z-10">
        <div className="flex justify-between items-end mb-16" ref={headerRef}>
          <div>
            <h2 className="text-4xl md:text-5xl font-serif text-ivory mb-4">Insights & Journal</h2>
            <p className="text-ivory/70 text-lg font-light">The latest analysis from our editorial board.</p>
          </div>
          <div className="hidden md:flex space-x-6 text-sm uppercase tracking-widest text-ivory/50">
            <button className="text-gold">All</button>
            <button className="hover:text-ivory transition-colors">Litigation</button>
            <button className="hover:text-ivory transition-colors">Corporate</button>
            <button className="hover:text-ivory transition-colors">Technology</button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Featured Article */}
          <div className="article-card lg:col-span-8 group cursor-pointer relative overflow-hidden glass border border-white/10 rounded-sm">
            <div className="absolute inset-0 bg-black/40 group-hover:bg-black/20 transition-colors duration-700 z-10"></div>
            <div className="w-full h-125 relative overflow-hidden bg-gray-900">
               {/* Decorative background representing the article image */}
               <div className="absolute inset-0 bg-linear-to-tr from-charcoal to-navy transform group-hover:scale-105 transition-transform duration-1000 opacity-50"></div>
            </div>
            <div className="absolute bottom-0 left-0 p-10 z-20 w-full bg-linear-to-t from-charcoal to-transparent">
              <span className="text-gold text-xs uppercase tracking-widest font-medium mb-4 block">Technology & Law</span>
              <h3 className="text-3xl md:text-4xl font-serif text-ivory mb-4 group-hover:text-white transition-colors">
                The Regulatory Landscape of Artificial Intelligence in 2026.
              </h3>
              <p className="text-ivory/80 font-light mb-6 line-clamp-2 max-w-2xl">
                An in-depth analysis of emerging compliance frameworks and what they mean for enterprise data strategy and intellectual property.
              </p>
              <div className="text-ivory/50 text-sm flex items-center space-x-4">
                <span>By Dr. Aris Thorne</span>
                <span>•</span>
                <span>12 Min Read</span>
              </div>
            </div>
          </div>

          {/* Secondary Articles */}
          <div className="lg:col-span-4 flex flex-col gap-8">
            {[
              { category: "Corporate", title: "M&A Trends in the Renewable Energy Sector.", author: "Elena Rostova", time: "8 Min Read" },
              { category: "Litigation", title: "Precedent Shifts in Cross-Border Jurisdictional Disputes.", author: "Marcus Vance", time: "15 Min Read" },
              { category: "Policy", title: "Decoding the New Antitrust Guidelines for Tech Conglomerates.", author: "Sarah Jenkins", time: "10 Min Read" }
            ].map((article, idx) => (
              <div key={idx} className="article-card group cursor-pointer flex flex-col justify-center glass p-6 border border-white/5 h-full hover:border-gold/30 transition-colors rounded-sm">
                <span className="text-gold text-xs uppercase tracking-widest font-medium mb-3 block">{article.category}</span>
                <h4 className="text-xl font-serif text-ivory mb-3 group-hover:text-white transition-colors">
                  {article.title}
                </h4>
                <div className="text-ivory/50 text-sm flex items-center space-x-4 mt-auto">
                  <span>{article.author}</span>
                  <span>•</span>
                  <span>{article.time}</span>
                </div>
              </div>
            ))}
          </div>

        </div>
      </div>
    </section>
  );
}

