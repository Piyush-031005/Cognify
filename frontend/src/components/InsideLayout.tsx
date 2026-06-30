import { useEffect } from "react";
import Navbar from "./Navbar";

export default function InsideLayout({ children, showNav = true }: { children: React.ReactNode; showNav?: boolean }) {
  useEffect(() => {
    const currentTheme = localStorage.getItem("theme") || "dark";
    const themeClass = currentTheme === "light" ? "theme-light-pop" : "theme-inside";
    document.documentElement.classList.add(themeClass);
    return () => {
      document.documentElement.classList.remove("theme-inside", "theme-light-pop");
    };
  }, []);
  return (
    <div className="min-h-screen bg-background grid-bg-subtle relative overflow-hidden">
      {showNav && <Navbar variant="inside" />}
      {children}
    </div>
  );
}
