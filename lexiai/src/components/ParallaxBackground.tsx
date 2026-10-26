"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Image from "next/image";

interface ParallaxBackgroundProps {
  imageSrc: string;
  alt: string;
  intensity?: number; // 0.1 to 1 for parallax strength
  overlayOpacity?: number; // 0 to 1 for darkening overlay
  kenBurns?: boolean; // Slow zoom effect
}

export default function ParallaxBackground({
  imageSrc,
  alt,
  intensity = 0.3,
  overlayOpacity = 0.75,
  kenBurns = false
}: ParallaxBackgroundProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);

    const isReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (isReducedMotion || !containerRef.current || !imageRef.current) return;

    const ctx = gsap.context(() => {
      // The parallax effect: move the image slightly slower than the scroll
      // giving the illusion of depth. Y translation depends on intensity.
      const yVal = window.innerHeight * intensity;

      gsap.fromTo(
        imageRef.current,
        { y: -yVal / 2 },
        {
          y: yVal / 2,
          ease: "none",
          scrollTrigger: {
            trigger: containerRef.current,
            start: "top bottom",
            end: "bottom top",
            scrub: true,
          }
        }
      );

      // Optional Ken Burns slow scale effect
      if (kenBurns) {
        gsap.to(imageRef.current, {
          scale: 1.1,
          ease: "none",
          scrollTrigger: {
            trigger: containerRef.current,
            start: "top bottom",
            end: "bottom top",
            scrub: true,
          }
        });
      }
    }, containerRef);

    return () => ctx.revert();
  }, [intensity, kenBurns]);

  return (
    <div ref={containerRef} className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
      <div className="absolute inset-0 z-10 bg-navy transition-opacity" style={{ opacity: overlayOpacity, mixBlendMode: 'multiply' }}></div>
      <div className="absolute inset-0 z-10 bg-linear-to-b from-charcoal/80 via-transparent to-charcoal/90"></div>
      
      <Image
        ref={imageRef}
        src={imageSrc}
        alt={alt}
        fill
        sizes="100vw"
        priority
        className="object-cover object-center scale-[1.1] blur-[2px]"
        quality={80}
      />
    </div>
  );
}

