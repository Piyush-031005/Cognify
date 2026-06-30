import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Brain, LogOut, Sun, Moon } from "lucide-react";
import { clearSession, getCurrentUser } from "@/lib/storage";
import { Button } from "@/components/ui/button";

export default function Navbar({ variant = "outside" }: { variant?: "outside" | "inside" }) {
  const navigate = useNavigate();
  const location = useLocation();
  const user = getCurrentUser();
  const inside = variant === "inside";

  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "dark");

  useEffect(() => {
    const isLanding = location.pathname === "/";
    if (isLanding) {
      if (theme === "light") {
        document.documentElement.classList.remove("theme-inside", "theme-light-pop");
      } else {
        document.documentElement.classList.remove("theme-light-pop");
        document.documentElement.classList.add("theme-inside");
      }
    } else {
      if (theme === "light") {
        document.documentElement.classList.remove("theme-inside");
        document.documentElement.classList.add("theme-light-pop");
      } else {
        document.documentElement.classList.remove("theme-light-pop");
        document.documentElement.classList.add("theme-inside");
      }
    }
  }, [theme, location.pathname]);

  const toggleTheme = () => {
    const nextTheme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    localStorage.setItem("theme", nextTheme);
  };

  const onLogout = () => { clearSession(); navigate("/"); };

  return (
    <header className={`sticky top-0 z-40 w-full border-b ${inside ? "border-mint/15 bg-cyan-deep/70" : "border-border bg-background/70"} backdrop-blur-xl`}>
      <div className="container flex h-16 items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group">
          <div className={`grid h-9 w-9 place-items-center rounded-xl ${inside ? "bg-mint text-cyan-deep shadow-mint" : "bg-primary text-primary-foreground shadow-lime"} transition-transform group-hover:scale-110`}>
            <Brain className="h-5 w-5" />
          </div>
          <span className="font-display text-xl font-bold tracking-tight">Cognify</span>
        </Link>

        <nav className="flex items-center gap-2">
          {/* Theme Switcher Button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            aria-label="Toggle Theme"
            className="transition-all hover:bg-white/10"
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4 text-yellow-400" />
            ) : (
              <Moon className="h-4 w-4 text-black" />
            )}
          </Button>

          {!user && location.pathname !== "/auth" && (
            <Button asChild variant="ghost" className="font-medium">
              <Link to="/auth">Sign in</Link>
            </Button>
          )}
          {!user && (
            <Button asChild className={inside ? "bg-mint text-cyan-deep hover:bg-mint-glow shadow-mint" : "bg-primary text-primary-foreground hover:bg-primary-glow shadow-lime"}>
              <Link to="/auth">Get started</Link>
            </Button>
          )}
          {user && (
            <>
              <Button asChild variant="ghost"><Link to="/dashboard">Dashboard</Link></Button>
              <Button variant="ghost" size="icon" onClick={onLogout} aria-label="Log out">
                <LogOut className="h-4 w-4" />
              </Button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
