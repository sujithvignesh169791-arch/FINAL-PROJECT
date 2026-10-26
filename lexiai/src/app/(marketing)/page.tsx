import Hero from "@/components/Hero";
import PracticeAreas from "@/components/PracticeAreas";
import ForLawyers from "@/components/ForLawyers";
import ForLawStudents from "@/components/ForLawStudents";
import InsightsJournal from "@/components/InsightsJournal";
import CaseStudies from "@/components/CaseStudies";
import Testimonials from "@/components/Testimonials";
import CallToAction from "@/components/CallToAction";

export default function Home() {
  return (
    <>
      <Hero />
      <PracticeAreas />
      <ForLawyers />
      <ForLawStudents />
      <InsightsJournal />
      <CaseStudies />
      <Testimonials />
      <CallToAction />
    </>
  );
}
