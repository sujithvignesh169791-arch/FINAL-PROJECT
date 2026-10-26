"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

export default function CaseStudies() {
  const sectionRef = useRef<HTMLElement>(null);
  
  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    
    const ctx = gsap.context(() => {
      // Animate counters
      const counters = gsap.utils.toArray(".stat-counter");
      
      counters.forEach((counter: any) => {
        const target = parseInt(counter.getAttribute("data-target") || "0", 10);
        
        gsap.to(counter, {
          innerHTML: target,
          duration: 2,
          ease: "power2.out",
          snap: { innerHTML: 1 },
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 60%",
          }
        });
      });
    }, sectionRef);

    return () => ctx.revert();

  }, []);

  return (
    <section id="case-studies" ref={sectionRef} className="py-32 relative section-crossfade z-10 border-t border-white/5">
      <div className="absolute inset-0 bg-charcoal"></div>
      <div className="container mx-auto px-6 md:px-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-24">
          <div className="md:col-span-1">
            <h2 className="text-4xl font-serif text-ivory mb-6">Proven Track Record.</h2>
            <p className="text-ivory/60 text-lg font-light mb-8">
              Numbers that reflect our commitment to excellence and decisive outcomes.
            </p>
          </div>
          
          <div className="md:col-span-3 grid grid-cols-1 sm:grid-cols-3 gap-8 border-t border-white/5 pt-8 md:border-0 md:pt-0">
            <div>
              <div className="flex items-baseline mb-2">
                <span className="text-6xl font-serif text-gold stat-counter" data-target="250">0</span>
                <span className="text-4xl text-gold">+</span>
              </div>
              <div className="text-ivory/70 text-sm uppercase tracking-widest font-medium">Cases Won</div>
            </div>
            <div>
              <div className="flex items-baseline mb-2">
                <span className="text-6xl font-serif text-gold stat-counter" data-target="15">0</span>
                <span className="text-4xl text-gold">B+</span>
              </div>
              <div className="text-ivory/70 text-sm uppercase tracking-widest font-medium">In Settlements</div>
            </div>
            <div>
              <div className="flex items-baseline mb-2">
                <span className="text-6xl font-serif text-gold stat-counter" data-target="40">0</span>
                <span className="text-4xl text-gold">Yr</span>
              </div>
              <div className="text-ivory/70 text-sm uppercase tracking-widest font-medium">Combined Experience</div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="glass-dark p-12 border border-white/5 hover:border-gold/30 transition-colors duration-500">
            <span className="text-gold text-xs uppercase tracking-widest font-medium mb-4 block">Corporate M&A</span>
            <h3 className="text-2xl font-serif text-ivory mb-6">Navigating a $4B Transatlantic Merger.</h3>
            <p className="text-ivory/60 font-light leading-relaxed mb-8">
              How our team structured the acquisition of a leading European fintech firm by a US conglomerate, navigating complex regulatory landscapes across five jurisdictions.
            </p>
            <button className="text-ivory text-sm uppercase tracking-widest border-b border-gold/50 pb-1 hover:text-gold transition-colors">
              Read Case Study
            </button>
          </div>
          
          <div className="glass-dark p-12 border border-white/5 hover:border-gold/30 transition-colors duration-500">
            <span className="text-gold text-xs uppercase tracking-widest font-medium mb-4 block">Intellectual Property</span>
            <h3 className="text-2xl font-serif text-ivory mb-6">Defending Core Patents in Tech.</h3>
            <p className="text-ivory/60 font-light leading-relaxed mb-8">
              A landmark victory defending a major semiconductor manufacturer against a coordinated patent infringement lawsuit, setting a new industry precedent.
            </p>
            <button className="text-ivory text-sm uppercase tracking-widest border-b border-gold/50 pb-1 hover:text-gold transition-colors">
              Read Case Study
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
