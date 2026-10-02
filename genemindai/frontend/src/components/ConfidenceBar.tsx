import React from 'react';

interface ConfidenceBarProps {
  confidence: number; // float between 0 and 1
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({ confidence }) => {
  const percentage = Math.min(Math.max(Math.round(confidence * 100), 0), 100);

  // Color mapping based on confidence tier
  let barColor = 'bg-cyan-500';
  let textColor = 'text-cyan-400';

  if (percentage >= 80) {
    barColor = 'bg-emerald-500';
    textColor = 'text-emerald-400';
  } else if (percentage >= 50) {
    barColor = 'bg-amber-500';
    textColor = 'text-amber-400';
  } else {
    barColor = 'bg-rose-500';
    textColor = 'text-rose-400';
  }

  return (
    <div className="w-full space-y-2">
      <div className="flex justify-between items-center text-xs">
        <span className="text-slate-400 font-medium uppercase tracking-wider">
          Prediction Confidence
        </span>
        <span className={`font-bold font-mono text-sm ${textColor}`}>
          {percentage}% ({confidence.toFixed(4)})
        </span>
      </div>

      <div className="w-full bg-slate-900/90 rounded-full h-3 p-0.5 border border-slate-700/60 shadow-inner">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out shadow-sm ${barColor}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
