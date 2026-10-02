import React from 'react';
import { Navbar } from './components/Navbar';
import { Home } from './pages/Home';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-white">
      <Navbar />
      <div className="flex-1">
        <Home />
      </div>
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500 bg-slate-900/40">
        <div className="max-w-7xl mx-auto px-4">
          <p>© {new Date().getFullYear()} GeneMindAI. AI-Driven Genomic Analysis Platform for Beta Thalassemia.</p>
        </div>
      </footer>
    </div>
  );
};

export default App;
