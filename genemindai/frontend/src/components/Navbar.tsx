import React from 'react';
import { Dna, Activity } from 'lucide-react';

export const Navbar: React.FC = () => {
  return (
    <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          <div className="flex items-center space-x-4">
            <div className="p-2.5 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl shadow-lg shadow-cyan-500/20">
              <Dna className="w-7 h-7 text-white animate-pulse" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-white via-slate-100 to-cyan-400 bg-clip-text text-transparent">
                GeneMindAI
              </h1>
              <p className="text-xs font-medium text-cyan-400 tracking-wide uppercase">
                AI-Driven DNA Computing Platform
              </p>
            </div>
          </div>

          <div className="hidden sm:flex items-center space-x-3 bg-slate-800/60 px-3.5 py-1.5 rounded-full border border-slate-700/50">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping" />
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 -ml-5" />
            <span className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-emerald-400" />
              System Online
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
