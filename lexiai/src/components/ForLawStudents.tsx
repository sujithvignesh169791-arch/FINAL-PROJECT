"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { BookOpen, Users, Trophy, Target } from "lucide-react";
import Link from "next/link";
import ParallaxBackground from "./ParallaxBackground";

export default function ForLawStudents() {
  const sectionRef = useRef<HTMLElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    
    if (sectionRef.current) {
      const items = gsap.utils.toArray(".student-feature");
      
      const ctx = gsap.context(() => {
        gsap.fromTo(
          contentRef.current,
          { y: 30, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 1,
            ease: "power2.out",
            scrollTrigger: {
              trigger: sectionRef.current,
              start: "top 75%",
            }
          }
        );

        gsap.fromTo(
          items,
          { y: 40, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.8,
            stagger: 0.15,
            ease: "power2.out",
            scrollTrigger: {
              trigger: sectionRef.current,
              start: "top 65%",
            }
          }
        );
      }, sectionRef);

      return () => ctx.revert();
    }
  }, []);

  const features = [
    { icon: BookOpen, title: "Study Resources & Briefs", desc: "Access a vast library of annotated case briefs and authoritative study materials." },
    { icon: Users, title: "Mentorship Matching", desc: "Connect with practicing attorneys for guidance, resume review, and career strategy." },
    { icon: Target, title: "Clerkship Opportunities", desc: "Exclusive listings for internships and clerkships at top-tier firms." },
    { icon: Trophy, title: "Moot Court Updates", desc: "Stay informed on national competitions and access preparation strategies." }
  ];

  return (
    <section id="for-students" ref={sectionRef} className="py-32 relative section-crossfade">
      
      <ParallaxBackground 
        imageSrc="/images/study_background_1786026291914.png" 
        alt="Law students study area"
        overlayOpacity={0.8}
        intensity={0.2}
      />
      
      {/* Warm ambient glow overlay on top of the image to keep the approachable feel */}
      <div className="absolute top-0 right-0 w-160 h-160 bg-amber-900/20 rounded-full mix-blend-screen filter blur-[100px] pointer-events-none z-10"></div>

      <div className="container mx-auto px-6 md:px-12 relative z-10">
        <div className="flex flex-col md:flex-row gap-16">
          
          <div className="md:w-1/3" ref={contentRef}>
            <h2 className="text-4xl md:text-5xl font-serif text-ivory mb-6">The Future of Law.</h2>
            <p className="text-ivory/70 text-lg font-light mb-8 leading-relaxed">
              A dedicated hub designed to foster the next generation of legal excellence. Find the mentorship and resources you need to transition from student to practitioner.
            </p>
            <Link href="/signup" className="inline-flex text-gold font-medium text-sm uppercase tracking-widest hover:text-ivory transition-colors duration-300 items-center group">
              Explore Student Hub 
              <span className="ml-2 transform group-hover:translate-x-1 transition-transform">→</span>
            </Link>
          </div>

          <div className="md:w-2/3 grid grid-cols-1 sm:grid-cols-2 gap-6">
            {features.map((feature, idx) => (
              <div key={idx} className="student-feature glass p-8 border border-white/5 hover:border-gold/30 transition-colors duration-300">
                <div className="w-12 h-12 bg-white/5 flex items-center justify-center rounded-sm mb-6">
                  <feature.icon className="text-ivory w-6 h-6" />
                </div>
                <h3 className="text-xl font-serif text-ivory mb-3">{feature.title}</h3>
                <p className="text-ivory/60 font-light leading-relaxed text-sm">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>

        </div>
      </div>
    </section>
  );
}
