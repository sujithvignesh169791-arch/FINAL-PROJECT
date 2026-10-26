"use client";

import { useRef, useEffect } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Link from "next/link";
import ParallaxBackground from "./ParallaxBackground";

export default function Hero() {
  const containerRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLDivElement>(null);
  const headlineRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    
    if (!containerRef.current || !textRef.current) return;

    const ctx = gsap.context(() => {
      // Pinning the hero section
      ScrollTrigger.create({
        trigger: containerRef.current,
        start: "top top",
        end: "+=150%",
        pin: true,
        scrub: 1,
      });
      
      // Text reveal and scale
      gsap.fromTo(
        textRef.current,
        { y: 50, opacity: 0, scale: 0.95 },
        {
          y: 0,
          opacity: 1,
          scale: 1,
          duration: 1.5,
          ease: "power2.out",
          delay: 0.2,
        }
      );

      // Subtle light sweep
      const sweep = gsap.to(".light-sweep", {
        x: "200%",
        duration: 2.5,
        ease: "power2.inOut",
        paused: true,
      });
      
      setTimeout(() => sweep.play(), 1000);
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <div className="hero-pin-wrapper">
      <section ref={containerRef} className="relative h-screen w-full flex items-center justify-center overflow-hidden bg-charcoal section-crossfade">
      
      <ParallaxBackground 
        imageSrc="/images/hero_background_1786025803963.png" 
        alt="Legal objects on marble surface"
        overlayOpacity={0.65}
        kenBurns={true}
      />

      <div className="container relative z-10 px-6 mx-auto flex flex-col items-center text-center" ref={textRef}>
        <div className="overflow-hidden relative mb-4">
          <h1 ref={headlineRef} className="text-6xl md:text-8xl lg:text-9xl font-serif text-ivory tracking-tight relative">
            Justice, <span className="italic text-ivory/90">Elevated.</span>
          </h1>
          <div className="light-sweep absolute top-0 -left-full w-1/2 h-full bg-linear-to-r from-transparent via-white/10 to-transparent skew-x-[-20deg] mix-blend-overlay"></div>
        </div>
        
        <p className="mt-6 text-lg md:text-xl text-ivory/70 max-w-2xl font-light tracking-wide uppercase">
          Where Legal Excellence Meets Modern Practice.
        </p>

        <div className="mt-12 flex flex-col sm:flex-row gap-6">
          <Link href="/login" className="px-8 py-4 bg-gold text-navy font-medium text-sm uppercase tracking-widest hover:bg-white transition-colors duration-500 text-center">
            Sign In
          </Link>
          <Link href="/signup" className="px-8 py-4 border border-gold/30 text-ivory font-medium text-sm uppercase tracking-widest hover:border-gold transition-colors duration-500 relative overflow-hidden group glass text-center flex items-center justify-center">
            <span className="relative z-10">Get Started</span>
            <div className="absolute inset-0 bg-gold/10 translate-y-full group-hover:translate-y-0 transition-transform duration-500"></div>
          </Link>
        </div>
      </div>
      </section>
    </div>
  );
}

