import React, { useState } from 'react';
import {
  FileText,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Download,
  Edit2,
  Save,
  UserCheck,
  HelpCircle,
  Workflow as WorkflowIcon,
  ShieldAlert
} from 'lucide-react';
import { BRDDocument, ReviewStatus } from '../types';

interface BrdWorkspaceProps {
  brd: BRDDocument | null;
  onUpdateRequirement: (reqId: string, payload: any) => Promise<void>;
  onSubmitReview: (decision: ReviewStatus, reviewerName: string, notes?: string) => Promise<void>;
  onExportDocx: () => Promise<void>;
  isExporting: boolean;
}

export const BrdWorkspace: React.FC<BrdWorkspaceProps> = ({
  brd,
  onUpdateRequirement,
  onSubmitReview,
  onExportDocx,
  isExporting,
}) => {
  const [editingReqId, setEditingReqId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [reviewerName, setReviewerName] = useState('Senior Business Analyst');
  const [reviewNotes, setReviewNotes] = useState('');

  if (!brd) {
    return (
      <div className="rounded-2xl bg-white border border-slate-200/90 p-12 text-center text-slate-500 shadow-sm">
        <FileText className="w-10 h-10 mx-auto mb-3 text-slate-400" />
        <h4 className="text-sm font-semibold text-slate-800 mb-1">No BRD Document Generated</h4>
        <p className="text-xs text-slate-500">Run an analysis pipeline to synthesize the formal Business Requirements Document.</p>
      </div>
    );
  }

  const handleStartEdit = (req: any) => {
    setEditingReqId(req.id);
    setEditTitle(req.title);
    setEditDesc(req.description);
  };

  const handleSaveEdit = async (reqId: string) => {
    await onUpdateRequirement(reqId, {
      title: editTitle,
      description: editDesc,
    });
    setEditingReqId(null);
  };

  return (
    <div className="space-y-6 py-4">
      {/* Top Banner & Export Actions */}
      <div className="rounded-2xl bg-white border border-slate-200/90 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div>
          <div className="flex items-center space-x-2.5">
            <h2 className="text-xl font-bold text-slate-900">{brd.project_title}</h2>
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
              v{brd.version}.0
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Target: <span className="font-medium text-slate-700">{brd.target_framework}</span> | Generated: {new Date(brd.generated_at).toLocaleString()}
          </p>
          <p className="text-xs text-slate-500">
            Inference Engine: <span className="text-emerald-700 font-semibold">{brd.model_provider_used}</span>
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={onExportDocx}
            disabled={isExporting}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center space-x-2 shadow-sm disabled:opacity-50 transition-all"
          >
            <Download className="w-4 h-4" />
            <span>{isExporting ? 'Generating DOCX...' : 'Export Corporate DOCX'}</span>
          </button>
        </div>
      </div>

      {/* Human Review & Governance Sign-off Block */}
      <div className="rounded-2xl bg-white border border-slate-200/90 p-6 space-y-4 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2">
            <UserCheck className="w-5 h-5 text-indigo-600" />
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              Human Stakeholder Governance & Review Sign-Off
            </h3>
          </div>
          <span className={`text-xs font-bold px-3 py-1 rounded-full uppercase border ${
            brd.review_status === 'APPROVED' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
            brd.review_status === 'REJECTED' ? 'bg-red-50 text-red-700 border-red-200' :
            'bg-amber-50 text-amber-700 border-amber-200'
          }`}>
            Current Status: {brd.review_status}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-slate-600 font-medium block mb-1">Reviewer Name & Role</label>
            <input
              type="text"
              value={reviewerName}
              onChange={(e) => setReviewerName(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 border border-slate-200 text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-indigo-500 transition-colors"
            />
          </div>
          <div>
            <label className="text-xs text-slate-600 font-medium block mb-1">Audit Notes / Revision Comments</label>
            <input
              type="text"
              placeholder="e.g. Verified against core finance policies..."
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 border border-slate-200 text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-indigo-500 transition-colors"
            />
          </div>
        </div>

        <div className="flex items-center justify-end space-x-3 pt-2">
          <button
            onClick={() => onSubmitReview('NEEDS_REVISION', reviewerName, reviewNotes)}
            className="px-4 py-2 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 font-semibold text-xs flex items-center space-x-1.5 transition-colors"
          >
            <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
            <span>Request Revision</span>
          </button>
          <button
            onClick={() => onSubmitReview('REJECTED', reviewerName, reviewNotes)}
            className="px-4 py-2 rounded-xl bg-red-50 hover:bg-red-100 text-red-800 border border-red-200 font-semibold text-xs flex items-center space-x-1.5 transition-colors"
          >
            <XCircle className="w-3.5 h-3.5 text-red-600" />
            <span>Reject Document</span>
          </button>
          <button
            onClick={() => onSubmitReview('APPROVED', reviewerName, reviewNotes)}
            className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center space-x-1.5 shadow-sm transition-all"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Approve & Sign Off</span>
          </button>
        </div>
      </div>

      {/* Section 1: Executive Summary */}
      <div className="rounded-2xl bg-white border border-slate-200/90 p-6 space-y-3 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">1. Executive Summary</h3>
        <p className="text-xs text-slate-600 leading-relaxed">{brd.executive_summary}</p>
      </div>

      {/* Section 2: Business Objectives */}
      <div className="rounded-2xl bg-white border border-slate-200/90 p-6 space-y-3 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">2. Business Objectives</h3>
        <ul className="list-disc list-inside space-y-1.5 text-xs text-slate-600">
          {brd.business_objectives.map((obj, i) => (
            <li key={i}>{obj}</li>
          ))}
        </ul>
      </div>

      {/* Section 3: Functional Requirements with Inline Editing */}
      <div className="rounded-2xl bg-white border border-slate-200/90 p-6 space-y-4 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
          3. Functional Requirements Specifications
        </h3>

        <div className="space-y-4">
          {brd.functional_requirements.map((req) => (
            <div key={req.id} className="p-4 rounded-xl bg-slate-50/70 border border-slate-200/80 space-y-3 hover:bg-slate-50 transition-colors">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs font-mono font-bold text-indigo-600">{req.id}</span>
                  {editingReqId === req.id ? (
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      className="mt-1 block w-full px-2.5 py-1 text-sm rounded-lg bg-white border border-slate-300 text-slate-900 focus:outline-none focus:border-indigo-500"
                    />
                  ) : (
                    <h4 className="text-sm font-bold text-slate-900 mt-1">{req.title}</h4>
                  )}
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-[10px] font-semibold px-2.5 py-0.5 rounded-full bg-slate-200/60 text-slate-700 border border-slate-300/50">
                    {req.category}
                  </span>
                  {editingReqId === req.id ? (
                    <button
                      onClick={() => handleSaveEdit(req.id)}
                      className="p-1 text-emerald-600 hover:text-emerald-700"
                    >
                      <Save className="w-4 h-4" />
                    </button>
                  ) : (
                    <button
                      onClick={() => handleStartEdit(req)}
                      className="p-1 text-slate-400 hover:text-slate-600"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>

              {editingReqId === req.id ? (
                <textarea
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  rows={3}
                  className="w-full px-2.5 py-1.5 text-xs rounded-lg bg-white border border-slate-300 text-slate-800 focus:outline-none focus:border-indigo-500"
                />
              ) : (
                <p className="text-xs text-slate-600 leading-relaxed">{req.description}</p>
              )}

              {/* Citations */}
              <div className="flex items-center space-x-2 text-[11px] font-mono text-slate-500">
                <span>Supporting Citations:</span>
                <span className="text-indigo-600 font-semibold">{req.supporting_evidence_ids.join(', ')}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section 4: Stakeholder Open Questions */}
      <div className="rounded-2xl bg-white border border-slate-200/90 p-6 space-y-4 shadow-sm">
        <div className="flex items-center space-x-2">
          <HelpCircle className="w-5 h-5 text-amber-600" />
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            4. Unresolved Business Questions & Stakeholder Action Items
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {brd.open_questions.map((oq) => (
            <div key={oq.id} className="p-4 rounded-xl bg-slate-50/70 border border-slate-200/80 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-mono text-amber-800 font-bold">{oq.id}: {oq.topic}</span>
                <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 text-[10px] font-semibold border border-amber-200">
                  {oq.urgency} Priority
                </span>
              </div>
              <p className="text-slate-700 leading-relaxed font-medium">{oq.question}</p>
              <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-[11px] text-slate-500">
                <span>Target: <strong className="text-slate-800 font-semibold">{oq.stakeholder_target}</strong></span>
                <span className="font-mono text-slate-400">{oq.context_code_reference}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
