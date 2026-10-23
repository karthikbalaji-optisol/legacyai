import React from 'react';
import { Scale, CheckCircle2, AlertTriangle, ArrowRight, ShieldCheck, Tag } from 'lucide-react';
import { BusinessRule } from '../types';

interface BusinessRulesPanelProps {
  rules: BusinessRule[];
  onSelectEvidence?: (evidenceId: string) => void;
  onNavigateToRule?: (ruleId: string) => void;
}

export const BusinessRulesPanel: React.FC<BusinessRulesPanelProps> = ({
  rules,
  onSelectEvidence,
  onNavigateToRule,
}) => {
  return (
    <div className="space-y-6 py-2">
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600">
            <Scale className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Discovered Business Rules & Threshold Logic</h3>
            <span className="text-xs text-slate-500 font-mono">{rules.length} verified rules extracted from C# AST</span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs font-semibold px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-2xs">
            100% Code-Anchored
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {rules.map((rule) => (
          <div
            key={rule.id}
            className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-xs hover:shadow-md hover:border-amber-300 transition-all space-y-3 group"
          >
            <div className="flex items-start justify-between">
              <div>
                <span className="text-xs font-mono font-bold text-amber-800 bg-amber-50 px-2.5 py-0.5 rounded-md border border-amber-200">
                  {rule.id}
                </span>
                <h4 className="text-sm font-bold text-slate-900 mt-2 group-hover:text-amber-900 transition-colors">
                  {rule.title}
                </h4>
              </div>

              <div className="flex items-center space-x-1.5">
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                  rule.classification === 'OBSERVED'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-amber-50 text-amber-700 border-amber-200'
                }`}>
                  {rule.classification}
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200">
                  {rule.confidence}
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed font-normal">{rule.description}</p>

            {/* Threshold & Comparison Box */}
            {(rule.threshold_operator || rule.threshold_value) && (
              <div className="flex items-center space-x-2 p-2.5 rounded-xl bg-slate-50 border border-slate-200 font-mono text-xs">
                <span className="text-slate-500 font-sans font-medium text-[11px]">Constraint:</span>
                <span className="text-amber-700 font-bold bg-amber-100/80 px-1.5 py-0.5 rounded">{rule.threshold_operator}</span>
                <span className="text-emerald-700 font-bold bg-emerald-100/80 px-1.5 py-0.5 rounded">{rule.threshold_value}</span>
                {rule.threshold_unit && <span className="text-slate-600">{rule.threshold_unit}</span>}
              </div>
            )}

            {/* Source Reference & Link */}
            <div className="pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs">
              <span className="text-slate-500 font-mono text-[11px] truncate max-w-[240px]">
                {rule.source_file}
              </span>

              <div className="flex items-center space-x-2">
                {rule.supporting_evidence_ids.map((evId) => (
                  <button
                    key={evId}
                    onClick={() => onSelectEvidence && onSelectEvidence(evId)}
                    className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200 hover:bg-sky-100 transition-colors"
                  >
                    {evId}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
