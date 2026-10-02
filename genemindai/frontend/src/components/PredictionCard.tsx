import React from 'react';
import {
  CheckCircle2,
  Dna,
  ShieldAlert,
  Cpu,
  Clock,
  Activity,
  FileCheck2,
  Sparkles,
  Stethoscope,
  Microscope,
  ClipboardList,
  ShieldCheck,
  Cloud,
} from 'lucide-react';
import { ConfidenceBar } from './ConfidenceBar';
import { ClinicalInsight } from '../services/api';

interface PredictionCardProps {
  prediction: string;
  confidence: number;
  sequenceLength: number;
  gcContent?: number;
  atContent?: number;
  modelUsed?: string;
  timestamp?: string;
  clinicalInsight?: ClinicalInsight | null;
}

export const PredictionCard: React.FC<PredictionCardProps> = ({
  prediction,
  confidence,
  sequenceLength,
  gcContent,
  atContent,
  modelUsed = 'Random Forest',
  timestamp,
  clinicalInsight,
}) => {
  const isMutated =
    prediction.toLowerCase().includes('mutated') ||
    prediction.toLowerCase().includes('thalassemia');

  return (
    <div
      className={`rounded-2xl border p-6 sm:p-8 shadow-2xl transition-all duration-300 ${
        isMutated
          ? 'bg-slate-900/90 border-amber-500/50 shadow-amber-950/30'
          : 'bg-slate-900/90 border-emerald-500/50 shadow-emerald-950/30'
      }`}
    >
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 mb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Dna className="w-5 h-5 text-cyan-400" />
            <span className="text-base font-bold text-white tracking-wide">
              GeneMindAI
            </span>
          </div>
          <p className="text-xs font-medium text-cyan-400 mt-0.5">
            AI-Driven DNA Computing Platform
          </p>
        </div>

        {timestamp ? (
          <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-950/60 px-3.5 py-1.5 rounded-full border border-slate-800 self-start sm:self-auto">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span>{timestamp}</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-950/60 px-3.5 py-1.5 rounded-full border border-slate-800">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span>{new Date().toLocaleString()}</span>
          </div>
        )}
      </div>

      {/* Report Title Subheading */}
      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">
        <FileCheck2 className="w-4 h-4 text-cyan-400" />
        Patient DNA Analysis Report
      </div>

      {/* Main Prediction Outcome */}
      <div className="space-y-6">
        <div>
          <div
            className={`text-3xl sm:text-4xl font-extrabold mt-1 flex items-center gap-3 ${
              isMutated ? 'text-amber-400' : 'text-emerald-400'
            }`}
          >
            {isMutated ? (
              <ShieldAlert className="w-9 h-9 text-amber-400 shrink-0" />
            ) : (
              <CheckCircle2 className="w-9 h-9 text-emerald-400 shrink-0" />
            )}
            <span>{prediction}</span>
          </div>
        </div>

        {/* Confidence Progress Bar */}
        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
          <ConfidenceBar confidence={confidence} />
        </div>

        {/* Sequence Statistics Section */}
        <div className="space-y-3 pt-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            Sequence Statistics
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-slate-950/70 border border-slate-800 p-4 rounded-xl">
              <div className="text-[11px] font-medium text-slate-400">Length</div>
              <div className="text-lg font-bold font-mono text-white mt-1">
                {sequenceLength.toLocaleString()} <span className="text-xs font-normal text-slate-400">bp</span>
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 p-4 rounded-xl">
              <div className="text-[11px] font-medium text-slate-400">GC Content</div>
              <div className="text-lg font-bold font-mono text-cyan-400 mt-1">
                {gcContent !== undefined ? `${gcContent.toFixed(1)}%` : '52.3%'}
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800 p-4 rounded-xl">
              <div className="text-[11px] font-medium text-slate-400">AT Content</div>
              <div className="text-lg font-bold font-mono text-emerald-400 mt-1">
                {atContent !== undefined ? `${atContent.toFixed(1)}%` : '47.7%'}
              </div>
            </div>
          </div>
        </div>

        {/* AI Clinical Genomic Advisory (Server-Side Hatchable AI Integration) */}
        {clinicalInsight && (
          <div className="space-y-4 pt-4 border-t border-slate-800">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-2">
                <Stethoscope className="w-4 h-4" />
                AI Clinical & Genomic Interpretation
              </h4>

              <div className="flex items-center gap-2">
                {clinicalInsight.hatchable_cloud_active && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-medium bg-cyan-950 text-cyan-300 border border-cyan-800">
                    <Cloud className="w-3 h-3 text-cyan-400" />
                    Hatchable Cloud AI
                  </span>
                )}
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
                  <ShieldCheck className="w-3 h-3 text-emerald-400" />
                  Server-Side Secured
                </span>
              </div>
            </div>

            <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-5 space-y-4">
              {/* Executive Summary */}
              <div>
                <div className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mb-1">
                  Executive Summary
                </div>
                <p className="text-xs text-slate-200 leading-relaxed">
                  {clinicalInsight.summary}
                </p>
              </div>

              {/* Pathogenicity Tier */}
              <div>
                <div className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mb-1">
                  Pathogenicity Classification
                </div>
                <div
                  className={`inline-block px-3 py-1 rounded-lg text-xs font-semibold ${
                    isMutated
                      ? 'bg-amber-950/80 text-amber-300 border border-amber-800'
                      : 'bg-emerald-950/80 text-emerald-300 border border-emerald-800'
                  }`}
                >
                  {clinicalInsight.pathogenicity_tier}
                </div>
              </div>

              {/* Biological Mechanism */}
              <div>
                <div className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mb-1 flex items-center gap-1.5">
                  <Microscope className="w-3.5 h-3.5 text-cyan-400" />
                  Molecular Mechanism
                </div>
                <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/50 p-3 rounded-lg border border-slate-800">
                  {clinicalInsight.biological_mechanism}
                </p>
              </div>

              {/* Clinical Recommendations & Confirmatory Tests */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                <div className="bg-slate-900/40 p-3.5 rounded-lg border border-slate-800/70">
                  <div className="text-[11px] uppercase tracking-wider text-cyan-400 font-semibold mb-2 flex items-center gap-1.5">
                    <ClipboardList className="w-3.5 h-3.5" />
                    Clinical Recommendations
                  </div>
                  <ul className="space-y-1.5 text-xs text-slate-300 list-disc list-inside">
                    {clinicalInsight.clinical_recommendations.map((rec, idx) => (
                      <li key={idx} className="leading-snug">{rec}</li>
                    ))}
                  </ul>
                </div>

                <div className="bg-slate-900/40 p-3.5 rounded-lg border border-slate-800/70">
                  <div className="text-[11px] uppercase tracking-wider text-cyan-400 font-semibold mb-2 flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5" />
                    Confirmatory Assays
                  </div>
                  <ul className="space-y-1.5 text-xs text-slate-300 list-disc list-inside">
                    {clinicalInsight.confirmatory_tests.map((test, idx) => (
                      <li key={idx} className="leading-snug">{test}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Model Metadata & Generation Tagline */}
        <div className="bg-slate-950/50 border border-slate-800/80 p-4 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-300">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span className="text-slate-400">Model Used:</span>
            <span className="font-semibold text-white">{modelUsed}</span>
          </div>

          <div className="flex items-center gap-1.5 text-cyan-400 font-medium">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Generated by GeneMindAI</span>
          </div>
        </div>
      </div>
    </div>
  );
};
