import { useState } from "react";
import {
  ArrowDown,
  Binary,
  BrainCircuit,
  ChevronRight,
  Dna,
  FileSearch,
  GitBranch,
  Network,
  ScanSearch,
  Sparkles,
  Trees,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { GenomicVisual } from "./GenomicVisual";

const scrollTo = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

export function HeroSection() {
  return (
    <section id="top" className="hero-section dark-section">
      <div className="hero-grid page-shell">
        <div className="hero-copy animate-fade-in">
          <p className="eyebrow"><Sparkles /> AI-DRIVEN GENOMIC ANALYSIS</p>
          <h1>Decode DNA.<br /><span>Understand the Signal.</span></h1>
          <p className="hero-lede">GeneMindAI analyzes nucleotide sequences using k-mer frequency encoding, Random Forest classification, and explainable AI to explore patterns in the human HBB locus.</p>
          <div className="hero-actions">
            <Button variant="hero" size="lg" onClick={() => scrollTo("analysis")}>Start DNA Analysis <ChevronRight /></Button>
            <Button variant="heroOutline" size="lg" onClick={() => scrollTo("how-it-works")}>Explore How It Works <ArrowDown /></Button>
          </div>
          <div className="hero-tags" aria-label="Core technologies">
            <span><Binary /> k = 3 encoding</span>
            <span><Trees /> Random Forest</span>
            <span><Network /> SHAP explainability</span>
          </div>
        </div>
        <GenomicVisual />
      </div>
      <div className="hero-footnote page-shell"><span>HBB / BETA-GLOBIN</span><span>SEQUENCE → MODEL → EXPLANATION</span></div>
    </section>
  );
}

const overview = [
  { number: "01", icon: Dna, title: "Sequence Analysis", copy: "Process nucleotide sequences and prepare them for analysis." },
  { number: "02", icon: BrainCircuit, title: "Machine Learning", copy: "Use k-mer frequency encoding with a Random Forest classifier." },
  { number: "03", icon: ScanSearch, title: "Explainable AI", copy: "Use SHAP-based visualizations to inspect model feature importance." },
];

export function PlatformOverview() {
  return (
    <section id="platform" className="light-section section-pad">
      <div className="page-shell">
        <div className="section-intro split-intro">
          <div><p className="eyebrow light-eyebrow">THE PLATFORM</p><h2>From Sequence<br />to Insight</h2></div>
          <p>GeneMindAI combines nucleotide sequence processing, machine learning classification, and explainable AI into a single genomic analysis workflow.</p>
        </div>
        <div className="overview-grid">
          {overview.map(({ number, icon: Icon, title, copy }) => (
            <article className="overview-card" key={number}>
              <div className="card-top"><span>{number}</span><Icon /></div>
              <h3>{title}</h3><p>{copy}</p>
              <div className="sequence-rule">A&nbsp;&nbsp;T&nbsp;&nbsp;C&nbsp;&nbsp;G</div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

const workflow = [
  ["01", "DNA Sequence", "ATCG"], ["02", "Preprocessing", "CLEAN"], ["03", "k-mer Encoding", "k = 3"],
  ["04", "Random Forest", "MODEL"], ["05", "Prediction", "OUTPUT"], ["06", "SHAP Explainability", "WHY"],
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="workflow-section section-pad">
      <div className="page-shell">
        <div className="section-intro centered-intro"><p className="eyebrow light-eyebrow">THE COMPUTATIONAL PATH</p><h2>How the Analysis Works</h2><p>One continuous path turns a nucleotide sequence into an interpretable model output.</p></div>
        <div className="workflow-track">
          {workflow.map(([number, title, detail], index) => (
            <article className="workflow-step" key={number}>
              <div className="workflow-node"><span>{number}</span><i /></div>
              <div><small>{detail}</small><h3>{title}</h3></div>
              {index < workflow.length - 1 && <ChevronRight className="workflow-arrow" />}
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

const tech = [
  { label: "K-MER ENCODING", title: "Sequence becomes structure.", body: "Frequency-based sequence representation using k = 3.", icon: Binary, wide: true },
  { label: "RANDOM FOREST", title: "Classification through an ensemble.", body: "Machine-learning classification used by the existing backend.", icon: Trees },
  { label: "TREEEXPLAINER / SHAP", title: "Model importance, made visible.", body: "Explainability visualization for model feature importance.", icon: GitBranch },
  { label: "HBB LOCUS", title: "A defined genomic focus.", body: "Analysis focused on the human HBB / beta-globin locus.", icon: FileSearch, wide: true },
];

export function TechnologySection() {
  return (
    <section className="technology-section dark-section section-pad">
      <div className="page-shell">
        <div className="section-intro split-intro dark-intro"><div><p className="eyebrow">CAPABILITIES</p><h2>Built for Interpretable<br />Genomic Analysis</h2></div><p>A focused technical stack brings sequence representation, classification, and model explanation into one coherent workflow.</p></div>
        <div className="technology-grid">
          {tech.map(({ label, title, body, icon: Icon, wide }) => (
            <article className={`technology-card ${wide ? "technology-wide" : ""}`} key={label}>
              <div className="tech-icon"><Icon /></div><small>{label}</small><h3>{title}</h3><p>{body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export function MethodologySection() {
  const stages = [
    { title: "DNA sequence", description: "Paste a sequence or upload a FASTA or text file. FASTA headers are removed, and the app analyzes the sequence as supplied; it does not extract the HBB gene from a larger reference file." },
    { title: "Preprocessing", description: "Whitespace is removed and lowercase letters are converted to uppercase. The sequence must contain only A, T, C, G, or N. N contributes to sequence length but is excluded from GC and AT percentages." },
    { title: "k-mer frequency encoding", description: "The sequence is divided into overlapping groups of three bases. For example, ATCG produces ATC and TCG. The model receives each stored feature's relative frequency across the sequence." },
    { title: "Random Forest classification", description: "The saved Random Forest model compares the encoded frequencies with patterns learned during training. It assigns one of two labels: Healthy or Beta Thalassemia; it does not identify a specific variant." },
    { title: "Prediction", description: "The response includes the predicted label, the model's confidence score, sequence length, GC and AT percentages, and a timestamp. Confidence is a model output, not a clinical certainty." },
    { title: "SHAP / TreeExplainer", description: "The SHAP images summarize feature influence for the model overall. They are pre-generated reports, not recalculated for the uploaded sequence, and feature influence does not prove biological cause." },
  ];
  const [expandedStage, setExpandedStage] = useState<string | null>(null);

  return (
    <section id="methodology" className="methodology-section light-section section-pad">
      <div className="page-shell methodology-grid">
        <div className="methodology-copy"><p className="eyebrow light-eyebrow">METHODOLOGY</p><h2>The Methodology Behind GeneMindAI</h2><p>GeneMindAI focuses on the human HBB / beta-globin locus. The sequence is normalized, represented as k-mer frequencies at k = 3, classified with the existing Random Forest model, and examined through SHAP / TreeExplainer.</p><p className="method-note">The platform supports research and educational exploration. It does not describe biological mechanisms or act as a diagnostic device.</p></div>
        <div className="methodology-flow">
          {stages.map(({ title, description }, index) => {
            const isExpanded = expandedStage === title;
            return (
              <div className="method-stage" key={title}>
                <button
                  type="button"
                  className="method-stage-toggle"
                  aria-expanded={isExpanded}
                  aria-controls={`method-stage-panel-${index}`}
                  onClick={() => setExpandedStage((current) => current === title ? null : title)}
                >
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <strong>{title}</strong>
                  <ArrowDown aria-hidden="true" />
                </button>
                <div
                  id={`method-stage-panel-${index}`}
                  className={`method-stage-panel ${isExpanded ? "is-open" : ""}`}
                  aria-hidden={!isExpanded}
                >
                  <div className="method-stage-panel-inner"><p>{description}</p></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export function FinalCTA() {
  return (
    <section className="final-cta dark-section">
      <div className="final-dna" aria-hidden="true">ATG&nbsp;&nbsp;GTG&nbsp;&nbsp;CAT&nbsp;&nbsp;CTG&nbsp;&nbsp;ACT&nbsp;&nbsp;CCT&nbsp;&nbsp;GAG</div>
      <div className="page-shell final-cta-inner"><p className="eyebrow">BEGIN AN ANALYSIS</p><h2>Explore the Signal<br />Within the Sequence.</h2><p>Analyze a nucleotide sequence with GeneMindAI.</p><Button variant="hero" size="lg" onClick={() => scrollTo("analysis")}>Analyze DNA <ChevronRight /></Button></div>
    </section>
  );
}

export function Footer() {
  const links = [["Platform", "platform"], ["How It Works", "how-it-works"], ["Analysis", "analysis"], ["Explainability", "explainability"], ["Methodology", "methodology"]] as const;
  return <footer className="site-footer"><div className="page-shell footer-grid"><div><strong>GeneMindAI</strong><p>AI-Driven DNA Computing Platform</p></div><nav>{links.map(([label, id]) => <button type="button" onClick={() => scrollTo(id)} key={id}>{label}</button>)}</nav></div><div className="page-shell footer-bottom"><span>GeneMindAI — Research and educational use. Not a diagnostic device.</span><span>Sequence → Insight</span></div></footer>;
}
