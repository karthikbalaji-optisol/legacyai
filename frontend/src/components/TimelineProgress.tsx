import React, { useEffect, useRef } from 'react';
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  Cpu,
  ShieldCheck,
  Terminal,
  Activity,
  Radio,
  FileCode2,
  Sparkles,
} from 'lucide-react';
import { AgentLog, AnalysisStatus } from '../types';

interface TimelineProgressProps {
  status: AnalysisStatus | null;
  logs?: AgentLog[];
  onRefresh: () => void;
}

export const TimelineProgress: React.FC<TimelineProgressProps> = ({ status, logs = [], onRefresh }) => {
  const terminalEndRef = useRef<HTMLDivElement>(null);

  const steps = [
    { id: 'validate_repository', label: '1. Validate Repository', desc: 'Verify archive sandbox, paths, and security limits' },
    { id: 'scan_source_code', label: '2. Scan Source Code', desc: 'Deterministic C# AST & syntax scanner' },
    { id: 'build_evidence_index', label: '3. Build Evidence Index', desc: 'Generate stable IDs & bounded line excerpts' },
    { id: 'extract_business_capabilities', label: '4. Extract Capabilities', desc: 'Synthesize high-level business functions' },
    { id: 'extract_business_rules', label: '5. Extract Business Rules', desc: 'Extract thresholds, operators & validations' },
    { id: 'generate_functional_requirements', label: '6. Generate Requirements', desc: 'Formulate FRs with acceptance criteria' },
    { id: 'validate_evidence', label: '7. Validate Evidence', desc: 'Deterministic zero-hallucination verification' },
    { id: 'identify_gaps_and_questions', label: '8. Identify Gaps', desc: 'Flag ungrounded claims & open questions' },
    { id: 'generate_brd', label: '9. Generate BRD', desc: 'Bedrock model synthesis & schema validation' },
    { id: 'await_human_review', label: '10. Await Human Review', desc: 'Analyst approval checkpoint (no self-approval)' },
    { id: 'export_approved_document', label: '11. Export Document', desc: 'Publish verified enterprise DOCX document' },
  ];

  // Auto-scroll terminal when new logs arrive
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs.length]);

  if (!status) {
    return (
      <div className="rounded-2xl bg-white border border-slate-200/90 p-10 text-center space-y-3 shadow-sm">
        <Clock className="w-10 h-10 text-slate-400 mx-auto" />
        <h3 className="text-base font-semibold text-slate-800">No active analysis pipeline</h3>
        <p className="text-xs text-slate-500">Upload a .NET repository or select the LegacyOrders sample to start.</p>
      </div>
    );
  }

  const currentStepIndex = status.current_node
    ? steps.findIndex(s => s.id === status.current_node)
    : -1;

  const isCompleted = status.status === 'completed' || status.status === 'awaiting_review';
  const isFailed = status.status === 'failed';
  const isRunning = !isCompleted && !isFailed;

  const getBadgeStyle = (badge: string) => {
    switch (badge.toUpperCase()) {
      case 'SECURITY':
      case 'INIT':
        return 'text-purple-400 bg-purple-950/60 border-purple-800/60';
      case 'SCANNER':
        return 'text-cyan-400 bg-cyan-950/60 border-cyan-800/60';
      case 'EVIDENCE':
        return 'text-blue-400 bg-blue-950/60 border-blue-800/60';
      case 'DOMAIN':
        return 'text-indigo-400 bg-indigo-950/60 border-indigo-800/60';
      case 'RULES':
        return 'text-amber-400 bg-amber-950/60 border-amber-800/60';
      case 'SPEC':
        return 'text-pink-400 bg-pink-950/60 border-pink-800/60';
      case 'VALIDATOR':
        return 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60';
      case 'BEDROCK':
        return 'text-sky-300 bg-sky-950/60 border-sky-800/60';
      case 'COMPLETE':
        return 'text-emerald-300 bg-emerald-950 border-emerald-500';
      case 'ERROR':
        return 'text-red-400 bg-red-950 border-red-800';
      default:
        return 'text-slate-400 bg-slate-800 border-slate-700';
    }
  };

  return (
    <div className="space-y-6 py-2">
      {/* Top Status Bar with Live Indicator */}
      <div className="rounded-2xl bg-white border border-slate-200/90 p-6 flex flex-wrap items-center justify-between gap-4 shadow-sm">
        <div className="space-y-1.5">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono uppercase text-slate-400 font-medium">Analysis ID:</span>
            <span className="text-xs font-mono text-indigo-600 font-semibold">{status.analysis_id}</span>
          </div>

          <div className="flex items-center space-x-3 text-sm">
            <span className="text-slate-700 font-medium">Status:</span>
            <span className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold uppercase ${
              isCompleted ? 'bg-emerald-50 text-emerald-700 border border-emerald-300' :
              isFailed ? 'bg-red-50 text-red-700 border border-red-300' :
              'bg-sky-50 text-sky-700 border border-sky-300'
            }`}>
              {isCompleted ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> :
               isFailed ? <AlertCircle className="w-3.5 h-3.5 text-red-600" /> :
               <Clock className="w-3.5 h-3.5 animate-spin text-sky-600" />}
              <span>{status.status.replace('_', ' ')}</span>
            </span>

            {isRunning && (
              <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono text-emerald-700 bg-emerald-50 border border-emerald-300 animate-pulse font-semibold">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping inline-block" />
                <span>LIVE STREAMING</span>
              </span>
            )}
          </div>
        </div>

        {/* Live Metrics Cards */}
        <div className="flex items-center space-x-6 border-l border-slate-200 pl-6">
          <div>
            <p className="text-xs text-slate-500 font-medium">Pipeline Progress</p>
            <div className="flex items-center space-x-2 mt-0.5">
              <span className="text-2xl font-bold text-slate-900 font-mono">{status.progress_percentage}%</span>
              <div className="w-24 bg-slate-100 h-2 rounded-full overflow-hidden border border-slate-200">
                <div
                  className="bg-indigo-600 h-full transition-all duration-500 rounded-full"
                  style={{ width: `${status.progress_percentage}%` }}
                />
              </div>
            </div>
          </div>

          {status.validation_score !== undefined && (
            <div className="border-l border-slate-200 pl-6">
              <p className="text-xs text-slate-500 font-medium">Citation Score</p>
              <div className="flex items-center space-x-2 mt-0.5">
                <p className="text-2xl font-bold text-emerald-600 font-mono">{status.validation_score.toFixed(1)}%</p>
                <div className="w-8 h-8 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
                  <ShieldCheck className="w-4 h-4" />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Live Agent Execution Terminal & Thought Stream */}
      <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden shadow-xl">
        <div className="px-5 py-3.5 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <Terminal className="w-4 h-4 text-emerald-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
              Live Agent Execution Stream
            </h3>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
              SSE EventSource
            </span>
          </div>

          <div className="flex items-center space-x-3 text-xs font-mono">
            {isRunning ? (
              <span className="flex items-center space-x-1.5 text-emerald-400">
                <Radio className="w-3.5 h-3.5 animate-pulse" />
                <span>Loop Active: Stage {Math.max(1, currentStepIndex + 1)}/11</span>
              </span>
            ) : isCompleted ? (
              <span className="flex items-center space-x-1.5 text-emerald-400">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Pipeline Complete</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1.5 text-red-400">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>Pipeline Stopped</span>
              </span>
            )}
          </div>
        </div>

        {/* Terminal Log Console */}
        <div className="p-4 bg-slate-950/90 font-mono text-xs max-h-72 overflow-y-auto space-y-2 select-text">
          {logs.length === 0 ? (
            <div className="text-slate-500 italic py-4 text-center">
              Connecting to live LangGraph agent execution stream...
            </div>
          ) : (
            logs.map((log) => (
              <div key={log.id} className="flex items-start space-x-2.5 leading-relaxed hover:bg-slate-900/40 p-1 rounded transition-colors">
                <span className="text-slate-500 shrink-0 text-[11px]">{log.timestamp}</span>
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider shrink-0 border ${getBadgeStyle(log.badge)}`}>
                  {log.badge}
                </span>
                <span className={`${
                  log.type === 'error' ? 'text-red-300' :
                  log.type === 'success' ? 'text-emerald-300' :
                  'text-slate-300'
                }`}>
                  {log.message}
                </span>
              </div>
            ))
          )}

          {/* Active running pulse line */}
          {isRunning && (
            <div className="flex items-center space-x-2 text-sky-400 pt-1 border-t border-slate-900 mt-2">
              <span className="animate-spin text-xs">⠋</span>
              <span className="text-slate-400">Agent executing:</span>
              <span className="font-semibold text-sky-300">
                {steps[currentStepIndex]?.label || status.current_node || 'Orchestrating'}...
              </span>
              <span className="w-1.5 h-3.5 bg-sky-400 animate-pulse inline-block" />
            </div>
          )}

          <div ref={terminalEndRef} />
        </div>
      </div>

      {/* 11-Node LangGraph Dynamic Timeline */}
      <div className="rounded-2xl bg-white border border-slate-200/90 p-6 space-y-4 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200/80 pb-3">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-indigo-600" />
            <span>LangGraph Deterministic Orchestration Pipeline</span>
          </h3>
          <span className="text-xs text-slate-500 font-mono font-medium">11 Explicit Stages</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-1">
          {steps.map((s, idx) => {
            const isPassed = isCompleted || (currentStepIndex > -1 && idx < currentStepIndex);
            const isCurrent = isRunning && (idx === currentStepIndex || (currentStepIndex === -1 && idx === 0));

            return (
              <div
                key={s.id}
                className={`p-3.5 rounded-xl border transition-all ${
                  isPassed
                    ? 'bg-emerald-50/40 border-emerald-200/90 text-slate-800 shadow-2xs'
                    : isCurrent
                    ? 'bg-sky-50 border-2 border-sky-500 text-slate-900 shadow-md shadow-sky-500/10 ring-2 ring-sky-100 scale-[1.01]'
                    : 'bg-slate-50/60 border-slate-200/80 text-slate-400 opacity-75'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-xs font-bold ${
                    isPassed ? 'text-emerald-700' : isCurrent ? 'text-sky-700' : 'text-slate-500'
                  }`}>
                    {s.label}
                  </span>
                  {isPassed ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  ) : isCurrent ? (
                    <Clock className="w-4 h-4 text-sky-600 animate-spin shrink-0" />
                  ) : (
                    <div className="w-3 h-3 rounded-full border border-slate-300 shrink-0" />
                  )}
                </div>
                <p className={`text-[11px] leading-normal ${isPassed ? 'text-slate-600' : isCurrent ? 'text-slate-700' : 'text-slate-400'}`}>
                  {s.desc}
                </p>

                {isCurrent && (
                  <div className="mt-2 pt-2 border-t border-sky-200 flex items-center space-x-1.5 text-[10px] text-sky-700 font-mono font-semibold">
                    <Activity className="w-3 h-3 animate-pulse text-sky-600" />
                    <span>Processing live in LangGraph loop...</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
