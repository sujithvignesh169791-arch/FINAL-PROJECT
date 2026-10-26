import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import SmoothScrollProvider from "@/components/SmoothScrollProvider";
import ScrollProgress from "@/components/ScrollProgress";

export default function MarketingLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <SmoothScrollProvider>
      <ScrollProgress />
      <Navbar />
      <main className="min-h-screen">
        {children}
      </main>
      <Footer />
    </SmoothScrollProvider>
  );
}
