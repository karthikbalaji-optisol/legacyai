import React from 'react';
import {
  ShieldAlert,
  FileCheck2,
  GitBranch,
  SearchCode,
  Network,
  CheckCircle2,
  ArrowRight,
  Code2,
  Layers,
  Sparkles,
  ShieldCheck,
  Check,
} from 'lucide-react';

interface LandingOverviewProps {
  onStartSample: () => void;
  onOpenUpload: () => void;
  hasActiveAnalysis: boolean;
  onViewAnalysis: () => void;
}

export const LandingOverview: React.FC<LandingOverviewProps> = ({
  onStartSample,
  onOpenUpload,
  hasActiveAnalysis,
  onViewAnalysis,
}) => {
  return (
    <div className="space-y-10 py-4">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-white border border-slate-200/90 p-8 sm:p-12 shadow-sm">
        <div className="absolute top-0 right-0 -mt-16 -mr-16 w-96 h-96 bg-gradient-to-br from-sky-100 to-indigo-100 rounded-full blur-3xl pointer-events-none opacity-70" />
        <div className="absolute bottom-0 left-1/3 -mb-20 w-80 h-80 bg-emerald-50 rounded-full blur-2xl pointer-events-none opacity-60" />

        <div className="relative z-10 max-w-3xl space-y-5">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-200/80 text-indigo-700 text-xs font-semibold shadow-2xs">
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>Autonomous Business Analyst for Legacy Systems</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight">
            Turn Legacy <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 via-sky-600 to-blue-600">.NET Code</span> into Verified Business Requirements.
          </h1>

          <p className="text-base sm:text-lg text-slate-600 leading-relaxed font-normal">
            LegacyLens AI reverse-engineers undocumented enterprise ASP.NET repositories, extracts deterministic code evidence,
            orchestrates an 11-stage LangGraph workflow powered by Amazon Bedrock, and produces an evidence-grounded BRD with zero hallucinated rules.
          </p>

          <div className="flex flex-wrap items-center gap-3.5 pt-2">
            <button
              onClick={onStartSample}
              className="px-6 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold shadow-md shadow-slate-900/15 flex items-center space-x-2 transition-all transform hover:-translate-y-0.5 active:translate-y-0"
            >
              <span>Analyze LegacyOrders Sample</span>
              <ArrowRight className="w-4 h-4 text-sky-400" />
            </button>

            <button
              onClick={onOpenUpload}
              className="px-6 py-3 rounded-xl bg-white hover:bg-slate-50 text-slate-800 font-semibold border border-slate-300 shadow-xs hover:border-slate-400 transition-all"
            >
              Upload Custom ZIP
            </button>

            {hasActiveAnalysis && (
              <button
                onClick={onViewAnalysis}
                className="px-5 py-3 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-semibold flex items-center space-x-2 transition-all shadow-xs"
              >
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>View Live Pipeline</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 3 Core Architectural Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="rounded-2xl bg-white border border-slate-200/90 p-6 space-y-3.5 shadow-xs hover:shadow-md hover:border-sky-300 transition-all group">
          <div className="w-11 h-11 rounded-xl bg-sky-50 border border-sky-200/80 flex items-center justify-center text-sky-600 shadow-2xs group-hover:scale-105 transition-transform">
            <SearchCode className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-slate-900">Deterministic C# Scanner & MCP</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Compiler-aware AST extraction discovers controllers, validation operators, thresholds, role gates,
            and status transitions deterministically before LLM inference.
          </p>
        </div>

        <div className="rounded-2xl bg-white border border-slate-200/90 p-6 space-y-3.5 shadow-xs hover:shadow-md hover:border-emerald-300 transition-all group">
          <div className="w-11 h-11 rounded-xl bg-emerald-50 border border-emerald-200/80 flex items-center justify-center text-emerald-600 shadow-2xs group-hover:scale-105 transition-transform">
            <FileCheck2 className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-slate-900">Zero-Hallucination Policy</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Every business rule is validated in Python against real source line ranges.
            Observed code behavior is strictly distinguished from inferred business intent.
          </p>
        </div>

        <div className="rounded-2xl bg-white border border-slate-200/90 p-6 space-y-3.5 shadow-xs hover:shadow-md hover:border-purple-300 transition-all group">
          <div className="w-11 h-11 rounded-xl bg-purple-50 border border-purple-200/80 flex items-center justify-center text-purple-600 shadow-2xs group-hover:scale-105 transition-transform">
            <Network className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-slate-900">Interactive Impact Explorer</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Visual graph mapping rule ripple effects:
            <span className="block mt-1 font-mono text-[11px] text-purple-700 font-medium">
              Rule → Method → Service → Requirement → Acceptance Criteria
            </span>
          </p>
        </div>
      </div>

      {/* The Central BA Journey Walkthrough */}
      <div className="rounded-2xl bg-white border border-slate-200/90 p-8 space-y-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200/80 pb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">The Verified Business Analyst Journey</h2>
            <p className="text-xs text-slate-500">From raw legacy C# classes to an approved corporate Word document</p>
          </div>
          <span className="text-xs font-mono font-semibold px-3 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200 self-start sm:self-auto">
            10-Stage Lifecycle
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {[
            { step: '01', title: 'Safe Ingestion', desc: 'Path traversal protection, zip bomb rejection, symlink sandbox' },
            { step: '02', title: 'Code Intelligence', desc: 'Extracts 43+ symbols, ASP.NET routes, thresholds, dependencies' },
            { step: '03', title: 'LangGraph & Bedrock', desc: '11-stage graph synthesizes capabilities, rules & requirements' },
            { step: '04', title: 'Deterministic Gate', desc: 'Verifies exact line ranges, flags unsupported claims' },
            { step: '05', title: 'Traceability Explorer', desc: 'Click any requirement to see the exact C# excerpt' },
            { step: '06', title: 'Impact Graph', desc: 'Visualizes ripple effects across services & test scenarios' },
            { step: '07', title: 'Human Review', desc: 'Analyst edits, accepts, or requests rule revision' },
            { step: '08', title: 'Corporate DOCX', desc: 'One-click export with cover page, tables & audit trail' },
          ].map((item) => (
            <div
              key={item.step}
              className="p-4 rounded-xl bg-slate-50/70 border border-slate-200/80 hover:bg-white hover:shadow-xs hover:border-slate-300 transition-all space-y-1.5"
            >
              <span className="text-xs font-mono text-indigo-600 font-bold">{item.step}</span>
              <h4 className="text-xs font-bold text-slate-900">{item.title}</h4>
              <p className="text-[11px] text-slate-500 leading-normal">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
