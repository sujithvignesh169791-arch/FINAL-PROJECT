"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { Scale, Briefcase, FileText, Users, Building, Shield } from "lucide-react";
import ParallaxBackground from "./ParallaxBackground";

const practices = [
  { title: "Corporate Law", icon: Building, desc: "Mergers, acquisitions, and corporate governance for modern enterprises." },
  { title: "Litigation", icon: Scale, desc: "High-stakes dispute resolution with precision and authority." },
  { title: "Intellectual Property", icon: Shield, desc: "Protecting innovation and creative assets in a digital world." },
  { title: "Family Law", icon: Users, desc: "Navigating complex personal matters with discretion and care." },
  { title: "Tax Law", icon: FileText, desc: "Strategic planning and compliance for global portfolios." },
  { title: "Criminal Defense", icon: Briefcase, desc: "Rigorous representation for white-collar and complex cases." },
];

export default function PracticeAreas() {
  const sectionRef = useRef<HTMLElement>(null);
  const cardsRef = useRef<(HTMLDivElement | null)[]>([]);
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
            },
          }
        );

        gsap.fromTo(
          cardsRef.current,
          { y: 50, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.8,
            stagger: 0.1,
            ease: "power2.out",
            scrollTrigger: {
              trigger: sectionRef.current,
              start: "top 75%",
            },
          }
        );
      }, sectionRef);

      return () => ctx.revert();
    }
  }, []);

  return (
    <section id="practice-areas" ref={sectionRef} className="py-32 relative z-10 section-crossfade">
      
      <ParallaxBackground 
        imageSrc="/images/library_background_1786025856264.png" 
        alt="Law library"
        overlayOpacity={0.85}
        intensity={0.2}
      />

      <div className="container mx-auto px-6 md:px-12 relative z-10">
        <div className="mb-20 text-center md:text-left" ref={headerRef}>
          <h2 className="text-4xl md:text-5xl font-serif text-ivory mb-6">Expertise & Focus</h2>
          <p className="text-ivory/70 max-w-2xl text-lg font-light">
            Our platform provides authoritative insights and tools across core disciplines of modern legal practice.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {practices.map((practice, i) => (
            <div
              key={i}
              ref={(el) => {
                cardsRef.current[i] = el;
              }}
              className="glass p-10 group hover:-translate-y-2 transition-all duration-500 hover:border-gold/50 cursor-pointer"
            >
              <practice.icon className="text-gold/70 w-10 h-10 mb-8 group-hover:text-gold transition-colors duration-500" />
              <h3 className="text-2xl font-serif text-ivory mb-4 group-hover:text-white">{practice.title}</h3>
              <p className="text-ivory/50 leading-relaxed font-light group-hover:text-ivory/70 transition-colors">
                {practice.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
