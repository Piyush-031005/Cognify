import { useEffect } from "react";
import Navbar from "./Navbar";

export default function InsideLayout({ children, showNav = true }: { children: React.ReactNode; showNav?: boolean }) {
  useEffect(() => {
    const currentTheme = localStorage.getItem("theme") || "light";
    const themeClass = currentTheme === "light" ? "theme-light-pop" : "theme-inside";
    document.documentElement.classList.add(themeClass);
    return () => {
      document.documentElement.classList.remove("theme-inside", "theme-light-pop", "theme-light-report");
    };
  }, []);
  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      {showNav && <Navbar variant="inside" />}
      {showNav ? (
        <main className="container py-8 relative z-10">
          {children}
        </main>
      ) : (
        <main className="relative z-10 min-h-screen w-full">
          {children}
        </main>
      )}
    </div>
  );
}
