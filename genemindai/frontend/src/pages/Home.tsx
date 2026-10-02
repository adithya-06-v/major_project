import React, { useState } from 'react';
import { UploadDNA } from '../components/UploadDNA';
import { PredictionCard } from '../components/PredictionCard';
import { ShapViewer } from '../components/ShapViewer';
import { predictSequence, PredictionResponse } from '../services/api';
import { AlertCircle, Loader2, Cpu, CheckCircle2 } from 'lucide-react';

export const Home: React.FC = () => {
  const [sequence, setSequence] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [analyzedLength, setAnalyzedLength] = useState<number>(0);

  const handleAnalyze = async () => {
    const cleanSeq = sequence.replace(/\s+/g, '');
    if (!cleanSeq) {
      setError('Please paste a DNA sequence or upload a FASTA file first.');
      setResult(null);
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await predictSequence(cleanSeq);
      setResult(response);
      setAnalyzedLength(cleanSeq.length);
    } catch (err: any) {
      setError(err.message || 'Failed to complete DNA analysis.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setSequence('');
    setError(null);
    setResult(null);
    setAnalyzedLength(0);
  };

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Intro Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold">
            <Cpu className="w-3.5 h-3.5" />
            Beta Thalassemia Genomic Diagnostic Engine
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
            Precision DNA Mutation & Pathology Classifier
          </h2>
          <p className="text-sm text-slate-400 leading-relaxed">
            Ingest genomic sequences into GeneMindAI to detect single-nucleotide variants in the human *HBB* locus, extract k-mer frequencies, and view SHAP explainability feature attributions.
          </p>
        </div>

        <div className="flex flex-wrap gap-4 text-xs font-mono text-slate-400 border-t md:border-t-0 md:border-l border-slate-800 pt-4 md:pt-0 md:pl-6">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>K-Mer Frequency Encoder</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Random Forest Classifier</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>TreeExplainer XAI</span>
          </div>
        </div>
      </div>

      {/* Input Section */}
      <UploadDNA
        sequence={sequence}
        onChangeSequence={setSequence}
        onAnalyze={handleAnalyze}
        onClear={handleClear}
        isLoading={isLoading}
      />

      {/* Error Alert */}
      {error && (
        <div className="bg-rose-950/60 border border-rose-800/80 rounded-2xl p-5 shadow-lg flex items-start gap-3.5 animate-shake">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-sm font-semibold text-rose-200">Analysis Request Failed</h4>
            <p className="text-xs text-rose-300/90 leading-relaxed">{error}</p>
          </div>
        </div>
      )}

      {/* Loading Spinner */}
      {isLoading && (
        <div className="bg-slate-800/70 border border-slate-700/60 rounded-2xl p-12 text-center shadow-xl backdrop-blur-sm flex flex-col items-center justify-center space-y-4">
          <div className="relative">
            <div className="w-16 h-16 rounded-full border-4 border-cyan-500/20 border-t-cyan-500 animate-spin" />
            <Loader2 className="w-8 h-8 text-cyan-400 animate-pulse absolute inset-0 m-auto" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white tracking-wide">Analyzing DNA...</h3>
            <p className="text-xs text-slate-400 mt-1">
              Extracting k-mer features and running Random Forest inference engine.
            </p>
          </div>
        </div>
      )}

      {/* Results & Prediction Display */}
      {result && !isLoading && (
        <div className="space-y-8 animate-fadeIn">
          <PredictionCard
            prediction={result.prediction}
            confidence={result.confidence}
            sequenceLength={result.sequence_length || analyzedLength}
            gcContent={result.gc_content}
            atContent={result.at_content}
            modelUsed={result.model_used}
            timestamp={result.timestamp}
            clinicalInsight={result.clinical_insight}
          />
          <ShapViewer />
        </div>
      )}
    </main>
  );
};
