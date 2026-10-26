"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import ParallaxBackground from "./ParallaxBackground";

const testimonials = [
  {
    quote: "LexNova provided the exact insights our firm needed to navigate the changing regulatory landscape. The caliber of the community is unmatched.",
    name: "Eleanor Sterling",
    title: "Managing Partner",
    institution: "Sterling & Vance LLC"
  },
  {
    quote: "As a law student, the mentorship I found here was instrumental in securing my clerkship. The resources are rigorously curated and highly accessible.",
    name: "Jameson Clarke",
    title: "J.D. Candidate",
    institution: "Harvard Law School"
  },
  {
    quote: "The definitive platform for modern legal professionals. It bridges the gap between traditional prestige and cutting-edge digital efficiency.",
    name: "Marcus Wright",
    title: "Chief General Counsel",
    institution: "Aura Tech"
  },
  {
    quote: "An indispensable tool for our litigation team. The case analytics and peer networking have transformed our approach to complex disputes.",
    name: "Sarah Jenkins",
    title: "Senior Litigator",
    institution: "Harrison Group"
  }
];

export default function Testimonials() {
  const scrollRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (!scrollRef.current) return;
    
    const scroller = scrollRef.current;
    
    // Simple infinite scroll effect
    let ctx = gsap.context(() => {
      gsap.to(scroller, {
        x: "-50%",
        ease: "none",
        duration: 30,
        repeat: -1,
      });
    });
    
    return () => ctx.revert();
  }, []);

  const handleMouseEnter = () => {
    gsap.getTweensOf(scrollRef.current).forEach(t => t.pause());
  };

  const handleMouseLeave = () => {
    gsap.getTweensOf(scrollRef.current).forEach(t => t.play());
  };

  return (
    <section id="community" className="py-32 overflow-hidden relative section-crossfade z-10">
      
      <ParallaxBackground 
        imageSrc="/images/courtroom_background_1786026321759.png" 
        alt="Historic courtroom"
        overlayOpacity={0.8}
        intensity={0.25}
      />
      
      <div className="container mx-auto px-6 md:px-12 mb-16 text-center relative z-10">
        <h2 className="text-4xl md:text-5xl font-serif text-[var(--color-ivory)] mb-6">Trusted by the Best.</h2>
        <p className="text-[var(--color-ivory)]/70 text-lg font-light max-w-2xl mx-auto">
          Hear from the practitioners, partners, and future leaders shaping the legal landscape.
        </p>
      </div>

      <div 
        className="w-[200vw] sm:w-[150vw] md:w-[200%] flex gap-8 px-8 relative z-10" 
        ref={scrollRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {/* Render twice for seamless loop */}
        {[...testimonials, ...testimonials].map((t, idx) => (
          <div key={idx} className="w-80 md:w-96 flex-shrink-0 glass-dark p-10 border border-white/5 rounded-sm hover:border-[var(--color-gold)]/30 transition-colors duration-500">
            <p className="text-[var(--color-ivory)]/80 font-light leading-relaxed mb-8 italic">
              "{t.quote}"
            </p>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-[var(--color-charcoal)] border border-white/10 flex items-center justify-center text-[var(--color-gold)] font-serif">
                {t.name.charAt(0)}
              </div>
              <div>
                <h4 className="text-[var(--color-ivory)] text-sm font-medium">{t.name}</h4>
                <p className="text-[var(--color-ivory)]/50 text-xs">{t.title}</p>
                <p className="text-[var(--color-gold)]/70 text-xs mt-1">{t.institution}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
