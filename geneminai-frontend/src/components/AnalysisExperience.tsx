import { useCallback, useEffect, useRef, useState, type ChangeEvent, type DragEvent } from "react";
import {
  AlertCircle,
  BarChart3,
  CheckCircle2,
  FileCode2,
  FlaskConical,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { API_BASE_URL, analyzeSequence, getApiErrorMessage, getTestSample, type AnalysisResponse } from "@/services/api";

const ALLOWED_FILE_TYPES = [".fasta", ".fa", ".txt"];

function normalizeSequence(value: string) {
  return value.replace(/\s/g, "").toUpperCase();
}

function parseFasta(value: string) {
  return normalizeSequence(value.split(/\r?\n/).filter((line) => !line.trimStart().startsWith(">")).join(""));
}

interface FileUploadProps { onSequence: (value: string) => void; setError: (value: string | null) => void }

function FileUpload({ onSequence, setError }: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const readFile = useCallback((file?: File) => {
    if (!file) return;
    const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!ALLOWED_FILE_TYPES.includes(extension)) {
      setError("Choose a .fasta, .fa, or .txt sequence file.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result !== "string") {
        setError("This sequence file could not be read.");
        return;
      }
      onSequence(parseFasta(reader.result));
      setError(null);
    };
    reader.onerror = () => setError("This sequence file could not be read.");
    reader.readAsText(file);
  }, [onSequence, setError]);

  const drop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    readFile(event.dataTransfer.files[0]);
  };

  const select = (event: ChangeEvent<HTMLInputElement>) => readFile(event.target.files?.[0]);

  return (
    <div className={`file-drop ${dragging ? "file-drop-active" : ""}`} onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={drop}>
      <UploadCloud />
      <div><strong>Drop a FASTA sequence</strong><span>.fasta, .fa, or .txt</span></div>
      <Button type="button" variant="heroOutline" onClick={() => inputRef.current?.click()}>Browse file</Button>
      <input ref={inputRef} type="file" accept=".fasta,.fa,.txt,text/plain" onChange={select} className="sr-only" aria-label="Upload a DNA sequence file" />
    </div>
  );
}

export function AnalysisLoading() {
  return <div className="analysis-loading" role="status"><div className="scanner"><span>ATGGTGCATCTGACTCCTGAGGAG</span><i /></div><div><strong>Analyzing DNA Sequence</strong><p>Extracting k-mer features and running Random Forest inference...</p></div></div>;
}

function valueOrDash(value: number | null, suffix = "") {
  return typeof value === "number" && Number.isFinite(value) ? `${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}${suffix}` : "—";
}

function apiTimestampOrFallback(value: string | null) {
  const timestamp = value?.trim();
  return timestamp || "Not provided";
}

const RESULT_INFORMATION: Record<string, { title: string; summary: string }> = {
  "Beta Thalassemia": {
    title: "About Beta Thalassemia",
    summary: "Variants in HBB can reduce or prevent beta-globin production. The resulting condition and its severity depend on the specific variants and the person's overall genotype.",
  },
  "Sickle Cell Disease": {
    title: "About Sickle Cell Disease",
    summary: "Sickle cell disease is a group of inherited hemoglobin disorders involving hemoglobin S, usually together with another disease-causing HBB variant. The specific genotype affects the condition.",
  },
  "Hemoglobin E Disease": {
    title: "About Hemoglobin E",
    summary: "Hemoglobin E is caused by an HBB variant. Having two HbE copies often causes a mild blood condition, while HbE inherited with a beta-thalassemia variant can have a more variable and sometimes more severe effect.",
  },
  "Hemoglobin C Disease": {
    title: "About Hemoglobin C",
    summary: "Hemoglobin C is caused by an HBB variant. Two HbC copies are often associated with a mild hemolytic anemia; inheriting HbC with HbS is a distinct condition with different clinical implications.",
  },
  Healthy: {
    title: "About the Healthy Classification",
    summary: "Healthy means the model returned its Healthy class. It does not rule out other genetic conditions, carrier status, or health concerns.",
  },
};

export function AnalysisResults({ result }: { result: AnalysisResponse }) {
  const isHealthy = result.prediction === "Healthy";
  const resultInformation = result.prediction
    ? RESULT_INFORMATION[result.prediction]
    : undefined;
  const isFixtureMatch = result.model_used === "Synthetic test fixture label lookup";
  const confidence = typeof result.confidence === "number" ? Math.max(0, Math.min(100, result.confidence * 100)) : null;
  const confidenceTone = confidence === null ? "confidence-neutral" : confidence >= 80 ? "confidence-high" : confidence >= 50 ? "confidence-medium" : "confidence-low";
  const displayTimestamp = apiTimestampOrFallback(result.timestamp);

  return (
    <section id="results" className="results-section light-section section-pad" aria-live="polite" tabIndex={-1}>
      <div className="page-shell">
        <div className="report-heading"><div><p className="eyebrow light-eyebrow">ANALYSIS COMPLETE</p><h2>DNA Analysis Report</h2></div><p>API timestamp<br /><strong>{displayTimestamp}</strong></p></div>
        <div className="result-focus">
          <div className={`prediction-panel ${isHealthy ? "prediction-healthy" : "prediction-warning"}`}>
            <div className="prediction-icon">{isHealthy ? <CheckCircle2 /> : <ShieldAlert />}</div>
            <div><small>PREDICTION</small><h3>{result.prediction}</h3><p>Classification returned by the GeneMindAI backend.</p></div>
          </div>
          <div className={`confidence-panel ${confidenceTone}`}>
            <div className="confidence-top"><span>{isFixtureMatch ? "TEST FIXTURE LABEL MATCH" : "MODEL CONFIDENCE"}</span><strong>{confidence === null ? "—" : `${confidence.toFixed(1)}%`}</strong></div>
            <div className="confidence-track"><i style={{ width: `${confidence ?? 0}%` }} /></div>
            <p>{isFixtureMatch ? "Exact match to the assigned label in a synthetic test dataset; this is not a model confidence or clinical result." : "Confidence value returned by the model."}</p>
          </div>
        </div>
        <div className="result-metrics">
          <div><span>Sequence Length</span><strong>{valueOrDash(result.sequence_length)}</strong><small>nucleotides</small></div>
          <div><span>GC Content</span><strong>{valueOrDash(result.gc_content, "%")}</strong><small>sequence composition</small></div>
          <div><span>AT Content</span><strong>{valueOrDash(result.at_content, "%")}</strong><small>sequence composition</small></div>
        </div>
        <div className="report-meta"><p><span>Model Used</span><strong>{result.model_used || "Not provided"}</strong></p><p><span>Target Locus</span><strong>HBB (Beta-Globin)</strong></p><p><span>Report</span><strong>Generated by GeneMindAI</strong></p></div>
        {result.training_data_notice && (
          <p className="plot-note" role="note">{result.training_data_notice}</p>
        )}
        {resultInformation && (
          <aside className="disease-context" aria-label={resultInformation.title}>
            <p className="eyebrow light-eyebrow">{resultInformation.title}</p>
            <h3>{result.prediction}</h3>
            <p>{resultInformation.summary}</p>
            <p>This is general educational information. A sequence classification does not establish a diagnosis; clinical interpretation requires validated testing and the person’s full genotype and context.</p>
          </aside>
        )}
      </div>
    </section>
  );
}

export function DNAAnalysisLab({ onResult, onClear }: { onResult: (result: AnalysisResponse) => void; onClear: () => void }) {
  const [sequence, setSequence] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingSample, setLoadingSample] = useState<"healthy" | "disease" | null>(null);
  const [loadedSample, setLoadedSample] = useState<string | null>(null);
  const [sampleNotice, setSampleNotice] = useState<string | null>(null);
  const normalizedLength = normalizeSequence(sequence).length;

  const updateSequence = (value: string) => {
    setSequence(value);
    setLoadedSample(null);
    setSampleNotice(null);
  };

  const loadTestSample = async (kind: "healthy" | "disease") => {
    setLoadingSample(kind);
    setError(null);
    try {
      const sampleData = await getTestSample(kind);
      const sampleSequence = parseFasta(sampleData.sequence);
      if (!sampleSequence || !/^[ATCGN]+$/.test(sampleSequence)) {
        throw new Error("Sample file contains an invalid DNA sequence.");
      }
      setSequence(sampleSequence);
      setLoadedSample(sampleData.label);
      setSampleNotice(sampleData.source_notice);
    } catch {
      setError("The reference sample could not be loaded. Please try again.");
    } finally {
      setLoadingSample(null);
    }
  };

  const submit = async () => {
    const normalized = normalizeSequence(sequence);
    if (!normalized) { setError("Enter or upload a DNA sequence before analysis."); return; }
    if (!/^[ATCGN]+$/.test(normalized)) { setError("DNA sequences may contain only A, T, C, G, and N."); return; }
    setError(null);
    setLoading(true);
    try {
      const data = await analyzeSequence(normalized);
      if (!data.prediction) {
        setError("The backend returned an unsupported prediction value.");
        return;
      }
      onResult(data);
    } catch (reason) {
      setError(getApiErrorMessage(reason));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="analysis" className="analysis-section dark-section section-pad">
      <div className="page-shell">
        <div className="section-intro split-intro dark-intro"><div><p className="eyebrow"><FlaskConical /> GENEMINDAI ANALYSIS LAB</p><h2>Analyze a DNA<br />Sequence</h2></div><p>Submit a nucleotide sequence to the existing GeneMindAI backend for classification and analysis.</p></div>
        <div className="lab-workspace">
          <div className="sequence-editor">
            <div className="editor-toolbar"><span><FileCode2 /> SEQUENCE INPUT</span><span>{normalizedLength.toLocaleString()} bases</span></div>
            <textarea value={sequence} onChange={(event) => { updateSequence(event.target.value.toUpperCase()); setError(null); }} spellCheck={false} placeholder="ATGGTGCATCTGACTCCTGAGGAG..." aria-label="DNA sequence" disabled={loading || loadingSample !== null} />
            <div className="editor-footer"><span>ALLOWED BASES</span>{["A", "T", "C", "G", "N"].map((base) => <kbd key={base}>{base}</kbd>)}</div>
          </div>
          <aside className="lab-controls">
            <FileUpload onSequence={updateSequence} setError={setError} />
            <div className="sample-group"><div><strong>Test samples</strong><span>Load a prepared synthetic input sequence</span></div><Button type="button" variant="heroOutline" onClick={() => void loadTestSample("healthy")} disabled={loading || loadingSample !== null}>{loadingSample === "healthy" ? "Loading..." : "Load Healthy Sample"}</Button><Button type="button" variant="heroOutline" onClick={() => void loadTestSample("disease")} disabled={loading || loadingSample !== null}>{loadingSample === "disease" ? "Loading..." : "Load Random Disease Sample"}</Button>{loadedSample && <p>Loaded class: <strong>{loadedSample}</strong></p>}{sampleNotice && <p>{sampleNotice}</p>}<p>Randomly selects from beta-thalassemia, sickle cell disease, hemoglobin E, and hemoglobin C test folders.</p></div>
            {error && <div className="lab-error" role="alert"><AlertCircle /><span>{error}</span></div>}
            <div className="lab-actions"><Button variant="laboratory" size="lg" onClick={submit} disabled={loading || loadingSample !== null}>{loading ? "Analyzing..." : "Analyze DNA"}<Sparkles /></Button><Button variant="heroOutline" size="lg" onClick={() => { setSequence(""); setError(null); setLoadedSample(null); setSampleNotice(null); onClear(); }} disabled={loading || loadingSample !== null}><RotateCcw /> Clear</Button></div>
          </aside>
        </div>
        {loading && <AnalysisLoading />}
      </div>
    </section>
  );
}

function ExplainabilityPlot({ title, src }: { title: string; src: string }) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [src]);
  return <article className="plot-card"><div className="plot-title"><BarChart3 /><span>{title}</span></div><div className="plot-frame">{failed ? <div className="plot-fallback"><AlertCircle /><p>No explainability plot available</p></div> : <img src={src} alt={title} onError={() => setFailed(true)} />}</div></article>;
}

export function ExplainabilitySection() {
  return (
    <section id="explainability" className="explainability-section dark-section section-pad">
      <div className="page-shell">
        <div className="section-intro split-intro dark-intro"><div><p className="eyebrow">EXPLAINABLE AI WITH SHAP</p><h2>See What the<br />Model Sees</h2></div><p>GeneMindAI uses SHAP-based visualizations to inspect feature importance from the existing model.</p></div>
        <div className="plot-grid"><ExplainabilityPlot title="SHAP Summary Plot" src={`${API_BASE_URL}/reports/shap_summary.png`} /><ExplainabilityPlot title="SHAP Bar Chart" src={`${API_BASE_URL}/reports/shap_bar.png`} /></div>
        <p className="plot-note">Visualizations are presented as generated by the existing backend. GeneMindAI does not infer additional biological interpretations from these plots.</p>
      </div>
    </section>
  );
}
