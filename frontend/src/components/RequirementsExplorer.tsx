import React, { useState } from 'react';
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  ExternalLink,
  ShieldCheck,
  Edit3,
  HelpCircle,
  Code
} from 'lucide-react';
import { FunctionalRequirement, ReviewStatus } from '../types';

interface RequirementsExplorerProps {
  requirements: FunctionalRequirement[];
  onSelectRequirement: (req: FunctionalRequirement) => void;
  selectedRequirementId?: string;
  onSelectEvidence: (evidenceId: string) => void;
}

export const RequirementsExplorer: React.FC<RequirementsExplorerProps> = ({
  requirements,
  onSelectRequirement,
  selectedRequirementId,
  onSelectEvidence,
}) => {
  const [filterCategory, setFilterCategory] = useState<string>('all');

  const categories = ['all', ...Array.from(new Set(requirements.map((r) => r.category)))];

  const filtered = requirements.filter(
    (r) => filterCategory === 'all' || r.category === filterCategory
  );

  return (
    <div className="space-y-6 py-2">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Functional Requirements Explorer</h3>
            <span className="text-xs text-slate-500 font-mono">{requirements.length} specifications extracted with acceptance criteria</span>
          </div>
        </div>

        {/* Unique Floating Segmented Filter Bar */}
        <div className="flex items-center space-x-1 overflow-x-auto bg-white p-1 rounded-xl border border-slate-200 shadow-2xs text-xs">
          {categories.map((c) => (
            <button
              key={c}
              onClick={() => setFilterCategory(c)}
              className={`px-3 py-1 rounded-lg capitalize whitespace-nowrap transition-all font-medium ${
                filterCategory === c
                  ? 'bg-slate-900 text-white font-semibold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Requirement Cards List */}
        <div className="lg:col-span-5 space-y-3">
          {filtered.map((req) => {
            const isSelected = selectedRequirementId === req.id;
            return (
              <div
                key={req.id}
                onClick={() => onSelectRequirement(req)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-sky-50/70 border-2 border-sky-500 shadow-md shadow-sky-500/10'
                    : 'bg-white border-slate-200/90 shadow-2xs hover:shadow-md hover:border-slate-300'
                }`}
              >
                <div className="flex items-start justify-between">
                  <span className="text-xs font-mono font-bold text-sky-800 bg-sky-50 px-2.5 py-0.5 rounded-md border border-sky-200">
                    {req.id}
                  </span>
                  <div className="flex items-center space-x-1.5">
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                      req.classification === 'OBSERVED'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : 'bg-amber-50 text-amber-700 border-amber-200'
                    }`}>
                      {req.classification}
                    </span>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase border ${
                      req.review_status === 'APPROVED' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                      req.review_status === 'REJECTED' ? 'bg-red-50 text-red-700 border-red-200' :
                      'bg-slate-100 text-slate-700 border-slate-200'
                    }`}>
                      {req.review_status}
                    </span>
                  </div>
                </div>

                <h4 className="text-sm font-bold text-slate-900 mt-2 leading-snug">{req.title}</h4>
                <p className="text-xs text-slate-600 line-clamp-2 mt-1 leading-relaxed">{req.description}</p>

                <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500 font-medium text-[11px]">{req.category}</span>
                  <span className="text-[11px] text-sky-700 font-mono font-semibold flex items-center space-x-1">
                    <span>{req.supporting_evidence_ids.length} citations</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Requirement Detail View */}
        <div className="lg:col-span-7">
          {selectedRequirementId ? (
            (() => {
              const active = requirements.find((r) => r.id === selectedRequirementId);
              if (!active) return null;

              return (
                <div className="rounded-2xl bg-white border border-slate-200/90 p-6 space-y-6 sticky top-28 shadow-sm">
                  {/* Header */}
                  <div className="border-b border-slate-200 pb-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-mono font-bold text-sky-800 bg-sky-50 px-2.5 py-0.5 rounded border border-sky-200">
                        {active.id}
                      </span>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                          {active.confidence} Confidence
                        </span>
                        <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200">
                          {active.classification}
                        </span>
                      </div>
                    </div>
                    <h3 className="text-lg font-bold text-slate-900">{active.title}</h3>
                    <p className="text-xs text-slate-600 leading-relaxed">{active.description}</p>
                  </div>

                  {/* Supporting Code Evidence Anchors */}
                  <div className="space-y-2.5">
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-1.5">
                      <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      <span>Verifiable Code Citations ({active.supporting_evidence_ids.length})</span>
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {active.supporting_evidence_ids.map((evId) => (
                        <button
                          key={evId}
                          onClick={() => onSelectEvidence(evId)}
                          className="px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-xs font-mono font-semibold text-slate-800 flex items-center space-x-2 transition-colors shadow-2xs"
                        >
                          <Code className="w-3.5 h-3.5 text-indigo-600" />
                          <span>{evId}</span>
                          <ExternalLink className="w-3 h-3 text-slate-400" />
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Acceptance Criteria Scenarios */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                      Acceptance Criteria (Gherkin Scenarios)
                    </h4>
                    <div className="space-y-2.5">
                      {active.acceptance_criteria.map((ac) => (
                        <div key={ac.id} className="p-3.5 rounded-xl bg-slate-50/80 border border-slate-200 text-xs space-y-1.5 shadow-2xs">
                          <p className="font-bold text-slate-900">[{ac.id}] {ac.scenario}</p>
                          <div className="text-slate-600 space-y-1 font-mono text-[11px] pl-2.5 border-l-2 border-indigo-500">
                            <p><span className="text-indigo-600 font-bold">Given:</span> {ac.given}</p>
                            <p><span className="text-amber-600 font-bold">When:</span> {ac.when}</p>
                            <p><span className="text-emerald-600 font-bold">Then:</span> {ac.then}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Implementing Symbols */}
                  {active.implemented_by_symbols.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                        Discovered Implementing Methods
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {active.implemented_by_symbols.map((sym) => (
                          <span key={sym} className="px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-[11px] font-mono text-indigo-700 font-medium">
                            {sym}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })()
          ) : (
            <div className="h-full rounded-2xl bg-white border border-slate-200 p-12 text-center flex flex-col items-center justify-center space-y-2 text-slate-400 shadow-sm">
              <FileText className="w-8 h-8 text-slate-300" />
              <p className="text-sm text-slate-500">Select a functional requirement from the left to view code citations & acceptance criteria.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
