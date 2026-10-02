import { useEffect, useState } from "react";
import { Activity, Dna, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { checkHealth } from "@/services/api";

const links = [
  ["Platform", "platform"],
  ["How It Works", "how-it-works"],
  ["Analysis", "analysis"],
  ["Explainability", "explainability"],
  ["Methodology", "methodology"],
] as const;

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    let active = true;
    const refreshHealth = () => {
      void checkHealth().then((status) => {
        if (active) setOnline(status);
      });
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    refreshHealth();
    const healthInterval = window.setInterval(refreshHealth, 30_000);
    return () => {
      active = false;
      window.clearInterval(healthInterval);
      window.removeEventListener("scroll", onScroll);
    };
  }, []);

  const navigate = (id: string) => {
    setOpen(false);
    scrollTo(id);
  };

  return (
    <header className={`site-nav ${scrolled ? "site-nav-scrolled" : ""}`}>
      <div className="nav-inner">
        <button className="brand" type="button" onClick={() => navigate("top")} aria-label="GeneMindAI home">
          <span className="brand-mark"><Dna /></span>
          <span className="min-w-0">
            <strong>GeneMindAI</strong>
            <small>AI-Driven DNA Computing Platform</small>
          </span>
        </button>

        <nav className="nav-links" aria-label="Main navigation">
          {links.map(([label, id]) => (
            <button type="button" onClick={() => navigate(id)} key={id}>{label}</button>
          ))}
        </nav>

        <div className="nav-actions">
          <span className={`system-status ${online === false ? "status-offline" : ""}`}>
            <Activity /> {online === null ? "Checking System" : online ? "System Online" : "Backend Offline"}
          </span>
          <Button variant="hero" size="lg" onClick={() => navigate("analysis")}>Analyze DNA</Button>
          <Button className="menu-button" variant="ghost" size="icon" onClick={() => setOpen((value) => !value)} aria-label={open ? "Close menu" : "Open menu"}>
            {open ? <X /> : <Menu />}
          </Button>
        </div>
      </div>

      {open && (
        <nav className="mobile-menu" aria-label="Mobile navigation">
          {links.map(([label, id]) => (
            <button type="button" onClick={() => navigate(id)} key={id}>{label}</button>
          ))}
          <div className={`system-status ${online === false ? "status-offline" : ""}`}>
            <Activity /> {online === null ? "Checking System" : online ? "System Online" : "Backend Offline"}
          </div>
          <Button variant="hero" size="lg" onClick={() => navigate("analysis")}>Analyze DNA</Button>
        </nav>
      )}
    </header>
  );
}
