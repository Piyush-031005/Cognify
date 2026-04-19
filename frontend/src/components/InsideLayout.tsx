import { useEffect } from "react";
import Navbar from "./Navbar";

export default function InsideLayout({ children, showNav = true }: { children: React.ReactNode; showNav?: boolean }) {
  useEffect(() => {
    document.documentElement.classList.add("theme-inside");
    return () => document.documentElement.classList.remove("theme-inside");
  }, []);
  return (
    <div className="min-h-screen bg-gradient-cyan grid-bg-mint">
      {showNav && <Navbar variant="inside" />}
      {children}
    </div>
  );
}
