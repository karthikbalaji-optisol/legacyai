import React, { useState } from 'react';
import {
  FileCode,
  ShieldCheck,
  Search,
  Filter,
  CheckCircle2,
  Copy,
  ExternalLink,
  Code
} from 'lucide-react';
import { EvidenceRecord } from '../types';

interface SourceEvidenceViewerProps {
  evidenceList: EvidenceRecord[];
  selectedEvidenceId?: string;
  onSelectEvidence?: (id: string) => void;
}

export const SourceEvidenceViewer: React.FC<SourceEvidenceViewerProps> = ({
  evidenceList,
  selectedEvidenceId,
  onSelectEvidence,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const categories = ['all', ...Array.from(new Set(evidenceList.map((e) => e.category)))];

  const filtered = evidenceList.filter((e) => {
    const matchesCategory = filterCategory === 'all' || e.category === filterCategory;
    const matchesSearch =
      e.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.symbol_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.relative_path.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.source_excerpt.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const activeEvidence = selectedEvidenceId
    ? evidenceList.find((e) => e.id === selectedEvidenceId) || evidenceList[0]
    : evidenceList[0];

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-6 py-2">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
            <FileCode className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Source Code Evidence Viewer</h3>
            <span className="text-xs text-slate-500 font-mono">{evidenceList.length} items deterministically anchored to disk</span>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Category filter pills */}
          <div className="flex items-center space-x-1 overflow-x-auto bg-white p-1 rounded-xl border border-slate-200 text-xs shadow-2xs">
            {categories.slice(0, 5).map((cat) => (
              <button
                key={cat}
                onClick={() => setFilterCategory(cat)}
                className={`px-3 py-1 rounded-lg capitalize whitespace-nowrap transition-all font-medium ${
                  filterCategory === cat
                    ? 'bg-slate-900 text-white font-semibold shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                {cat.replace('_', ' ')}
              </button>
            ))}
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search code..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-xs rounded-xl bg-white border border-slate-300 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 w-44 shadow-2xs"
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Evidence List */}
        <div className="lg:col-span-5 space-y-2 max-h-[640px] overflow-y-auto pr-1">
          {filtered.map((ev) => {
            const isSelected = activeEvidence?.id === ev.id;
            return (
              <div
                key={ev.id}
                onClick={() => onSelectEvidence && onSelectEvidence(ev.id)}
                className={`p-3.5 rounded-2xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-emerald-50/70 border-2 border-emerald-500 shadow-md shadow-emerald-500/10'
                    : 'bg-white border-slate-200/90 shadow-2xs hover:shadow-md hover:border-slate-300'
                }`}
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono font-bold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-md border border-emerald-200">
                    {ev.id}
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[10px] uppercase font-bold border border-slate-200">
                    {ev.category.replace('_', ' ')}
                  </span>
                </div>

                <div className="mt-2 text-xs">
                  <p className="font-bold text-slate-900 truncate">{ev.symbol_name}</p>
                  <p className="text-slate-500 font-mono text-[11px] truncate mt-0.5">{ev.relative_path}</p>
                </div>

                <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                  <span className="font-medium">Lines: {ev.start_line} - {ev.end_line}</span>
                  <span className="flex items-center space-x-1 text-emerald-700 font-semibold">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    <span>Verified</span>
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Evidence Code Excerpt Highlight */}
        <div className="lg:col-span-7">
          {activeEvidence ? (
            <div className="rounded-2xl bg-white border border-slate-200/90 p-6 space-y-4 sticky top-28 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-sm font-bold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">
                      {activeEvidence.id}
                    </span>
                    <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
                      Deterministic Match
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 font-mono mt-1">
                    {activeEvidence.relative_path} : Lines {activeEvidence.start_line} - {activeEvidence.end_line}
                  </p>
                </div>

                <button
                  onClick={() => handleCopy(activeEvidence.source_excerpt, activeEvidence.id)}
                  className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-xs text-slate-700 font-medium flex items-center space-x-1.5 transition-colors border border-slate-200 shadow-2xs"
                >
                  <Copy className="w-3.5 h-3.5 text-slate-600" />
                  <span>{copiedId === activeEvidence.id ? 'Copied!' : 'Copy Code'}</span>
                </button>
              </div>

              {/* Exact Code Box - Sleek Contrast */}
              <div className="rounded-xl bg-slate-950 border border-slate-800 p-4 font-mono text-xs overflow-x-auto shadow-inner">
                <div className="flex items-center justify-between text-[11px] text-slate-400 mb-2 border-b border-slate-800 pb-1">
                  <span>C# Source Code Excerpt</span>
                  <span className="text-sky-400">{activeEvidence.extraction_method}</span>
                </div>
                <pre className="text-slate-100 leading-relaxed font-mono whitespace-pre-wrap">
                  {activeEvidence.source_excerpt}
                </pre>
              </div>

              {/* Meta information */}
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-slate-500 block mb-0.5 text-[11px] font-medium">Category</span>
                  <span className="text-slate-900 font-bold uppercase">{activeEvidence.category}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-slate-500 block mb-0.5 text-[11px] font-medium">Validation Rule</span>
                  <span className="text-emerald-700 font-bold">Exact Line & Boundary Match</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full rounded-2xl bg-white border border-slate-200 p-12 text-center text-slate-400 shadow-sm">
              Select an evidence item to view bounded excerpt.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
