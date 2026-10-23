import React, { useState } from 'react';
import {
  Code2,
  FolderTree,
  FileCode,
  Tag,
  Shield,
  Layers,
  Search,
  Filter
} from 'lucide-react';
import { DiscoveredSymbol, ScanSummary } from '../types';

interface CodeIntelligenceExplorerProps {
  summary: ScanSummary | null;
  symbols: DiscoveredSymbol[];
  onSelectSymbol?: (symbolName: string) => void;
}

export const CodeIntelligenceExplorer: React.FC<CodeIntelligenceExplorerProps> = ({
  summary,
  symbols,
  onSelectSymbol,
}) => {
  const [filterKind, setFilterKind] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const filteredSymbols = symbols.filter((s) => {
    const matchesKind = filterKind === 'all' || s.kind === filterKind;
    const matchesSearch =
      s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.relative_path.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesKind && matchesSearch;
  });

  return (
    <div className="space-y-6 py-2">
      {/* Metric Cards */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
          <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-xs">
            <span className="text-xs text-slate-500 font-medium">Total C# Files</span>
            <p className="text-2xl font-bold text-slate-900 font-mono mt-1">{summary.csharp_files}</p>
          </div>
          <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-xs">
            <span className="text-xs text-slate-500 font-medium">Lines of Code</span>
            <p className="text-2xl font-bold text-indigo-600 font-mono mt-1">{summary.total_lines_of_code}</p>
          </div>
          <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-xs">
            <span className="text-xs text-slate-500 font-medium">Controllers</span>
            <p className="text-2xl font-bold text-emerald-600 font-mono mt-1">{summary.controllers_count}</p>
          </div>
          <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-xs">
            <span className="text-xs text-slate-500 font-medium">Services</span>
            <p className="text-2xl font-bold text-purple-600 font-mono mt-1">{summary.services_count}</p>
          </div>
          <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-xs">
            <span className="text-xs text-slate-500 font-medium">Entities & DTOs</span>
            <p className="text-2xl font-bold text-amber-600 font-mono mt-1">{summary.models_count}</p>
          </div>
          <div className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-xs">
            <span className="text-xs text-slate-500 font-medium">Business Rules</span>
            <p className="text-2xl font-bold text-rose-600 font-mono mt-1">{summary.business_rules_count}</p>
          </div>
        </div>
      )}

      {/* Symbol Table & Filtering */}
      <div className="rounded-2xl bg-white border border-slate-200/90 p-6 space-y-4 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-4">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600">
              <Code2 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Discovered Symbols & Structural Index</h3>
              <span className="text-xs text-slate-500 font-mono">{filteredSymbols.length} indexed classes and methods</span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {/* Unique Segmented Filter Pill Menu */}
            <div className="flex items-center space-x-1 bg-slate-100 rounded-xl p-1 border border-slate-200 text-xs shadow-2xs">
              {['all', 'controller', 'class', 'method', 'model', 'enum'].map((k) => (
                <button
                  key={k}
                  onClick={() => setFilterKind(k)}
                  className={`px-2.5 py-1 rounded-lg capitalize transition-all font-medium ${
                    filterKind === k ? 'bg-white text-slate-900 font-semibold shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {k}
                </button>
              ))}
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search symbol..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8 pr-3 py-1.5 text-xs rounded-xl bg-white border border-slate-300 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 w-48 shadow-2xs"
              />
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 uppercase font-mono border-b border-slate-200 text-[11px]">
              <tr>
                <th className="py-2.5 px-3">Symbol</th>
                <th className="py-2.5 px-3">Kind</th>
                <th className="py-2.5 px-3">File Location</th>
                <th className="py-2.5 px-3">Lines</th>
                <th className="py-2.5 px-3">Roles / Route</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {filteredSymbols.map((sym) => (
                <tr
                  key={`${sym.relative_path}-${sym.name}`}
                  onClick={() => onSelectSymbol && onSelectSymbol(sym.name)}
                  className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                >
                  <td className="py-2.5 px-3 text-slate-900 font-semibold group-hover:text-indigo-600 transition-colors">
                    {sym.name}
                  </td>
                  <td className="py-2.5 px-3">
                    <span className={`text-[10px] px-2 py-0.5 rounded-full uppercase font-bold border ${
                      sym.kind === 'controller' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                      sym.kind === 'method' ? 'bg-indigo-50 text-indigo-700 border-indigo-200' :
                      sym.kind === 'model' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                      'bg-slate-100 text-slate-700 border-slate-200'
                    }`}>
                      {sym.kind}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-slate-600 truncate max-w-[200px]">{sym.relative_path}</td>
                  <td className="py-2.5 px-3 text-slate-500">{sym.start_line} - {sym.end_line}</td>
                  <td className="py-2.5 px-3">
                    {sym.route ? (
                      <span className="text-[11px] text-sky-700 font-bold bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                        {sym.route}
                      </span>
                    ) : sym.roles.length > 0 ? (
                      <span className="text-[11px] text-purple-700 font-bold bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                        {sym.roles.join(', ')}
                      </span>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
