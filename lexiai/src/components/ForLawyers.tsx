"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { CheckCircle2 } from "lucide-react";
import Link from "next/link";
import ParallaxBackground from "./ParallaxBackground";

export default function ForLawyers() {
  const sectionRef = useRef<HTMLElement>(null);
  const textRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    
    if (!sectionRef.current || !textRef.current || !imageRef.current) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        textRef.current,
        { y: 40, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 1,
          ease: "power2.out",
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 70%",
          }
        }
      );

      gsap.fromTo(
        imageRef.current,
        { y: 60, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 1,
          ease: "power2.out",
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 60%",
          }
        }
      );
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section id="for-lawyers" ref={sectionRef} className="py-32 relative section-crossfade">
      
      <ParallaxBackground 
        imageSrc="/images/office_background_1786025871411.png" 
        alt="Law office boardroom"
        overlayOpacity={0.8}
        intensity={0.25}
      />

      <div className="container mx-auto px-6 md:px-12 flex flex-col lg:flex-row items-center gap-16 relative z-10">
        
        <div className="lg:w-1/2" ref={textRef}>
          <p className="text-gold uppercase tracking-widest text-sm mb-4 font-medium">For Practitioners</p>
          <h2 className="text-4xl md:text-5xl font-serif text-ivory mb-6 leading-tight">
            Elevate Your Practice with Strategic Intelligence.
          </h2>
          <p className="text-ivory/70 text-lg font-light mb-10 leading-relaxed">
            Access a curated suite of tools designed for practicing attorneys. From case management insights to a verified credibility network, empower your firm to operate at the highest echelon.
          </p>
          
          <ul className="space-y-6 mb-12">
            {[
              "Proprietary case management insights & analytics",
              "Exclusive professional networking with verified peers",
              "Premium Continuing Legal Education (CLE) resources",
              "Verified credibility badge system for your public profile"
            ].map((item, i) => (
              <li key={i} className="flex items-start">
                <CheckCircle2 className="text-gold w-6 h-6 mr-4 shrink-0 mt-0.5" />
                <span className="text-ivory/80 text-lg">{item}</span>
              </li>
            ))}
          </ul>
          
          <Link href="/signup" className="inline-block px-8 py-3 border border-ivory/20 text-ivory hover:bg-ivory hover:text-charcoal transition-colors duration-300 text-sm uppercase tracking-widest text-center">
            Join the Network
          </Link>
        </div>

        <div className="lg:w-1/2 w-full h-150 relative" ref={imageRef}>
          <div className="absolute inset-0 bg-navy/80 backdrop-blur-md rounded-sm overflow-hidden border border-white/10 shadow-2xl">
            {/* Abstract mockup representation */}
            <div className="w-full h-12 bg-white/5 border-b border-white/5 flex items-center px-4 space-x-2">
              <div className="w-3 h-3 rounded-full bg-white/20"></div>
              <div className="w-3 h-3 rounded-full bg-white/20"></div>
              <div className="w-3 h-3 rounded-full bg-white/20"></div>
            </div>
            <div className="p-8 h-full flex flex-col gap-6">
              <div className="w-1/3 h-6 bg-white/10 rounded"></div>
              <div className="w-full h-px bg-white/5 my-4"></div>
              <div className="flex gap-6 h-1/3">
                <div className="w-2/3 h-full bg-white/5 rounded p-4 flex flex-col gap-4">
                  <div className="w-1/2 h-4 bg-white/10 rounded"></div>
                  <div className="w-full h-2 bg-white/10 rounded"></div>
                  <div className="w-3/4 h-2 bg-white/10 rounded"></div>
                  <div className="w-full h-2 bg-white/10 rounded"></div>
                </div>
                <div className="w-1/3 h-full bg-gold/10 rounded border border-gold/20 p-4 flex flex-col gap-4 items-center justify-center">
                   <div className="w-16 h-16 rounded-full border-4 border-gold/50 border-t-gold animate-spin-slow"></div>
                   <div className="w-1/2 h-3 bg-gold/30 rounded mt-4"></div>
                </div>
              </div>
              <div className="w-full grow bg-white/5 rounded mt-auto flex items-end p-6">
                <div className="w-full h-1/2 bg-linear-to-t from-white/10 to-transparent"></div>
              </div>
            </div>
          </div>
          
          {/* Floating element */}
          <div className="absolute -bottom-10 -left-10 glass p-6 rounded-sm w-64 shadow-2xl border border-gold/20 animate-float">
            <div className="text-gold text-sm font-serif mb-2">Verified Profile</div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-white/10 rounded-full"></div>
              <div>
                <div className="w-24 h-3 bg-white/20 rounded mb-2"></div>
                <div className="w-16 h-2 bg-white/10 rounded"></div>
              </div>
            </div>
            <div className="w-full h-1 bg-gold/30 rounded overflow-hidden">
               <div className="w-3/4 h-full bg-gold"></div>
            </div>
          </div>
        </div>
        
      </div>
    </section>
  );
}

