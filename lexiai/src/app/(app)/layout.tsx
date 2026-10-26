import AppHeader from "@/components/app/AppHeader";
import Sidebar from "@/components/app/Sidebar";

export default function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="flex h-screen w-full bg-charcoal overflow-hidden text-foreground">
      <Sidebar />
      <div className="flex-1 flex flex-col h-screen overflow-hidden relative">
        {/* Stitch Background */}
        <div 
          className="absolute inset-0 z-0 opacity-5"
          style={{
            backgroundImage: "url('/images/skyline_background_1786026334741.png')",
            backgroundSize: "cover",
            backgroundPosition: "center fixed"
          }}
        />
        <AppHeader />
        <main className="flex-1 overflow-y-auto p-6 relative">
          <div className="absolute top-0 right-0 w-[50%] h-[50%] bg-gold/5 rounded-full blur-[120px] pointer-events-none" />
          <div className="relative z-10 max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
