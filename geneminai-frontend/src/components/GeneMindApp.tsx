import { useEffect, useRef, useState } from "react";
import type { AnalysisResponse } from "@/services/api";
import { Navbar } from "./Navbar";
import { DNAAnalysisLab, AnalysisResults, ExplainabilitySection } from "./AnalysisExperience";
import { FinalCTA, Footer, HeroSection, HowItWorks, MethodologySection, PlatformOverview, TechnologySection } from "./Sections";

export function GeneMindApp() {
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const shouldScroll = useRef(false);

  useEffect(() => {
    if (!result || !shouldScroll.current) return;
    shouldScroll.current = false;
    requestAnimationFrame(() => {
      const report = document.getElementById("results");
      report?.scrollIntoView({ behavior: "smooth", block: "start" });
      report?.focus({ preventScroll: true });
    });
  }, [result]);

  const onResult = (next: AnalysisResponse) => {
    shouldScroll.current = true;
    setResult(next);
  };

  return <div className="site-frame"><Navbar /><main><HeroSection /><PlatformOverview /><HowItWorks /><TechnologySection /><DNAAnalysisLab onResult={onResult} onClear={() => setResult(null)} />{result && <AnalysisResults result={result} />}<ExplainabilitySection /><MethodologySection /><FinalCTA /></main><Footer /></div>;
}
