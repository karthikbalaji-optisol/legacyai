import React from 'react';
import {
  Cpu,
  Sparkles,
  Activity,
  FileCode2,
  Scale,
  FileText,
  Search,
  Network,
  CheckCircle2,
  ShieldCheck,
  UploadCloud,
  Layers,
} from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  hasActiveAnalysis: boolean;
  onOpenUpload: () => void;
  rulesCount?: number;
  requirementsCount?: number;
  isAnalyzing?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  hasActiveAnalysis,
  onOpenUpload,
  rulesCount,
  requirementsCount,
  isAnalyzing,
}) => {
  const navItems = [
    {
      id: 'overview',
      label: 'Overview',
      icon: Sparkles,
      tag: null,
    },
    {
      id: 'timeline',
      label: 'Agent Pipeline',
      icon: Activity,
      isLive: isAnalyzing,
      tag: isAnalyzing ? 'LIVE' : null,
    },
    {
      id: 'code_intelligence',
      label: 'Code Intelligence',
      icon: FileCode2,
      tag: null,
    },
    {
      id: 'rules',
      label: 'Business Rules',
      icon: Scale,
      count: rulesCount,
      tag: null,
    },
    {
      id: 'requirements',
      label: 'Requirements (BRD)',
      icon: FileText,
      count: requirementsCount,
      tag: null,
    },
    {
      id: 'evidence',
      label: 'Source Evidence',
      icon: Search,
      tag: null,
    },
    {
      id: 'impact',
      label: 'Impact Explorer',
      icon: Network,
      tag: 'GRAPH',
    },
    {
      id: 'workspace',
      label: 'Review & Sign-Off',
      icon: CheckCircle2,
      tag: null,
    },
  ];

  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-white/80 border-b border-slate-200/80 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2.5">
        {/* Top Identity & Status Ribbon */}
        <div className="flex items-center justify-between h-13 mb-2">
          {/* Brand Logo & Tagline */}
          <div
            className="flex items-center space-x-3 cursor-pointer group"
            onClick={() => setCurrentTab('overview')}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-sky-600 to-blue-600 flex items-center justify-center shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform">
              <Cpu className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg tracking-tight text-slate-900">
                  LegacyLens<span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-600 to-indigo-600">.AI</span>
                </span>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                  Agentic BA
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block font-medium">
                Legacy .NET Reverse Engineering to Verified BRD
              </p>
            </div>
          </div>

          {/* Model Status & Zero-Hallucination Badges */}
          <div className="hidden lg:flex items-center space-x-3">
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-50 border border-slate-200/90 text-xs shadow-2xs">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-slate-500 font-medium">Inference:</span>
              <span className="text-slate-800 font-semibold">Amazon Bedrock</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-sky-100 text-sky-700 font-mono font-semibold">Claude 3</span>
            </div>

            <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200/80 text-xs text-emerald-800 font-medium shadow-2xs">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Zero-Hallucination Verified</span>
            </div>
          </div>

          {/* Action CTAs */}
          <div className="flex items-center space-x-2.5">
            <button
              onClick={onOpenUpload}
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-900 hover:bg-slate-800 text-white shadow-sm shadow-slate-900/15 hover:shadow-md transition-all flex items-center space-x-2 active:scale-95"
            >
              <UploadCloud className="w-4 h-4 text-sky-400" />
              <span>Analyze Repo</span>
            </button>
          </div>
        </div>

        {/* Unique Floating Segmented Navigation Dock */}
        <div className="pt-0.5 pb-1">
          <nav className="flex items-center space-x-1 overflow-x-auto p-1 rounded-2xl bg-slate-100/80 border border-slate-200/80 shadow-inner scrollbar-none text-xs">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentTab(item.id)}
                  className={`px-3.5 py-2 rounded-xl font-medium whitespace-nowrap transition-all duration-200 flex items-center space-x-2 relative ${
                    isActive
                      ? 'bg-white text-slate-900 shadow-sm font-semibold border border-slate-200/80'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
                  }`}
                >
                  <Icon
                    className={`w-3.5 h-3.5 transition-colors ${
                      isActive ? 'text-indigo-600' : 'text-slate-500'
                    }`}
                  />
                  <span>{item.label}</span>

                  {item.count !== undefined && item.count > 0 && (
                    <span
                      className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold ${
                        isActive
                          ? 'bg-slate-900 text-white'
                          : 'bg-slate-200 text-slate-700'
                      }`}
                    >
                      {item.count}
                    </span>
                  )}

                  {item.tag && (
                    <span
                      className={`text-[9px] px-1.5 py-0.2 rounded font-mono font-bold uppercase ${
                        item.tag === 'LIVE'
                          ? 'bg-emerald-100 text-emerald-700 border border-emerald-300 animate-pulse'
                          : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                      }`}
                    >
                      {item.tag}
                    </span>
                  )}

                  {item.isLive && (
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping absolute -top-0.5 -right-0.5" />
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
};
