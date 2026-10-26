"use client";

import { useRef, useEffect } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Link from "next/link";
import ParallaxBackground from "./ParallaxBackground";

export default function CallToAction() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);

    if (containerRef.current) {
      const ctx = gsap.context(() => {
        gsap.fromTo(
          ".cta-content",
          { y: 50, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 1.5,
            ease: "power2.out",
            scrollTrigger: {
              trigger: containerRef.current,
              start: "top 75%",
            }
          }
        );
      }, containerRef);
      
      return () => ctx.revert();
    }
  }, []);

  return (
    <section ref={containerRef} className="py-40 relative flex items-center justify-center overflow-hidden section-crossfade">
      
      <ParallaxBackground 
        imageSrc="/images/skyline_background_1786026334741.png" 
        alt="City skyline at dusk"
        overlayOpacity={0.85}
        intensity={0.3}
      />
      
      <div className="cta-content relative z-10 text-center max-w-3xl px-6 mx-auto flex flex-col items-center">
        <h2 className="text-5xl md:text-7xl font-serif text-ivory mb-8 tracking-tight">
          Your Practice. <span className="italic text-gold">Elevated.</span>
        </h2>
        
        <p className="text-ivory/70 text-lg md:text-xl font-light mb-12 max-w-xl mx-auto">
          Join the definitive platform for legal excellence. Gain access to premium insights, elite networking, and powerful practice tools.
        </p>
        
        <Link href="/signup" className="relative inline-block group overflow-hidden px-12 py-5 bg-ivory text-navy font-medium text-sm uppercase tracking-widest shadow-2xl transition-transform hover:-translate-y-1 duration-300 rounded-sm text-center">
          <span className="relative z-10">Join the Platform</span>
          <div className="absolute inset-0 bg-gold translate-y-full group-hover:translate-y-0 transition-transform duration-500 ease-in-out"></div>
          <div className="absolute inset-0 bg-gold mix-blend-overlay opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-md"></div>
        </Link>
      </div>
    </section>
  );
}
