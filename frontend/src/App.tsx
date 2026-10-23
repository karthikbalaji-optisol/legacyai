import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { LandingOverview } from './components/LandingOverview';
import { UploadModal } from './components/UploadModal';
import { TimelineProgress } from './components/TimelineProgress';
import { CodeIntelligenceExplorer } from './components/CodeIntelligenceExplorer';
import { BusinessRulesPanel } from './components/BusinessRulesPanel';
import { RequirementsExplorer } from './components/RequirementsExplorer';
import { SourceEvidenceViewer } from './components/SourceEvidenceViewer';
import { ImpactExplorer } from './components/ImpactExplorer';
import { BrdWorkspace } from './components/BrdWorkspace';
import {
  uploadRepository,
  startAnalysis,
  getAnalysisStatus,
  getBRD,
  getEvidence,
  getSymbols,
  getImpactGraph,
  updateRequirement,
  submitHumanReview,
  exportDocx,
  subscribeToAnalysisEvents,
} from './api/client';
import {
  AgentLog,
  AnalysisStatus,
  BRDDocument,
  DiscoveredSymbol,
  EvidenceRecord,
  FunctionalRequirement,
  ImpactGraph,
  ReviewStatus,
} from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('overview');
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isExporting, setIsExporting] = useState<boolean>(false);

  const [activeAnalysisId, setActiveAnalysisId] = useState<string | null>(null);
  const [status, setStatus] = useState<AnalysisStatus | null>(null);
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([]);
  const [brd, setBrd] = useState<BRDDocument | null>(null);
  const [evidenceList, setEvidenceList] = useState<EvidenceRecord[]>([]);
  const [symbols, setSymbols] = useState<DiscoveredSymbol[]>([]);
  const [impactGraph, setImpactGraph] = useState<ImpactGraph | null>(null);

  const [selectedRequirementId, setSelectedRequirementId] = useState<string | undefined>();
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | undefined>();

  // Stream analysis events in real-time with polling fallback
  useEffect(() => {
    if (!activeAnalysisId) return;

    let isMounted = true;

    // Helper to fetch final analysis artifacts
    const fetchAnalysisArtifacts = async () => {
      try {
        const [brdData, evData, symData, graphData] = await Promise.all([
          getBRD(activeAnalysisId),
          getEvidence(activeAnalysisId),
          getSymbols(activeAnalysisId),
          getImpactGraph(activeAnalysisId).catch(() => null),
        ]);
        if (!isMounted) return;
        setBrd(brdData);
        setEvidenceList(evData);
        setSymbols(symData);
        setImpactGraph(graphData);
        if (brdData.functional_requirements.length > 0) {
          setSelectedRequirementId(brdData.functional_requirements[0].id);
        }
        if (evData.length > 0) {
          setSelectedEvidenceId(evData[0].id);
        }
      } catch (err) {
        console.error('Error fetching analysis artifacts:', err);
      }
    };

    // 1. Subscribe to Live SSE EventStream
    const unsubscribe = subscribeToAnalysisEvents(
      activeAnalysisId,
      (event) => {
        if (!isMounted) return;

        setStatus((prev) => ({
          analysis_id: event.analysis_id,
          repository_id: prev?.repository_id || '',
          status: event.status,
          current_node: event.node,
          progress_percentage: event.progress_percentage,
          started_at: prev?.started_at || new Date().toISOString(),
          review_status: prev?.review_status || 'PENDING',
          validation_score: event.details?.validation_score ?? prev?.validation_score,
        }));

        const newLog: AgentLog = {
          id: `${event.node}-${event.step}-${event.timestamp}`,
          timestamp: new Date(event.timestamp).toLocaleTimeString(),
          node: event.node,
          message: event.message,
          badge: event.badge || 'AGENT',
          type: event.type === 'failed' ? 'error' : event.type === 'completed' ? 'success' : 'info',
          step: event.step,
        };

        setAgentLogs((prev) => {
          if (prev.some((l) => l.node === newLog.node && l.message === newLog.message)) {
            return prev;
          }
          return [...prev, newLog];
        });

        if (event.type === 'completed' || event.status === 'awaiting_review') {
          fetchAnalysisArtifacts();
        }
      },
      (err) => {
        console.warn('SSE stream disconnected, falling back to polling:', err);
      }
    );

    // 2. Periodic polling safeguard
    const interval = setInterval(async () => {
      try {
        const s = await getAnalysisStatus(activeAnalysisId);
        if (!isMounted) return;
        setStatus(s);

        if (s.status === 'completed' || s.status === 'awaiting_review') {
          clearInterval(interval);
          fetchAnalysisArtifacts();
        }
      } catch (err) {
        console.error('Error polling status:', err);
      }
    }, 2000);

    return () => {
      isMounted = false;
      unsubscribe();
      clearInterval(interval);
    };
  }, [activeAnalysisId]);

  // Handle ZIP upload
  const handleUploadZip = async (file: File) => {
    setIsLoading(true);
    setAgentLogs([]);
    try {
      const repo = await uploadRepository(file, false);
      const res = await startAnalysis(repo.repository_id);
      setActiveAnalysisId(res.analysis_id);
      setCurrentTab('timeline');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle 1-click LegacyOrders sample
  const handleUseSample = async () => {
    setIsLoading(true);
    setAgentLogs([]);
    try {
      const repo = await uploadRepository(undefined, true);
      const res = await startAnalysis(repo.repository_id);
      setActiveAnalysisId(res.analysis_id);
      setCurrentTab('timeline');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectEvidence = (evId: string) => {
    setSelectedEvidenceId(evId);
    setCurrentTab('evidence');
  };

  const handleUpdateRequirement = async (reqId: string, payload: any) => {
    if (!activeAnalysisId) return;
    const updated = await updateRequirement(activeAnalysisId, reqId, payload);
    setBrd(updated);
  };

  const handleSubmitReview = async (decision: ReviewStatus, reviewerName: string, notes?: string) => {
    if (!activeAnalysisId) return;
    const updated = await submitHumanReview(activeAnalysisId, decision, reviewerName, notes);
    setBrd(updated);
    if (status) {
      setStatus({ ...status, review_status: decision });
    }
  };

  const handleExportDocx = async () => {
    if (!activeAnalysisId) return;
    setIsExporting(true);
    try {
      const res = await exportDocx(activeAnalysisId);
      window.open(res.download_url, '_blank');
    } finally {
      setIsExporting(false);
    }
  };

  const isAnalyzing = status?.status === 'running' || status?.status === 'scanning';

  return (
    <div className="min-h-screen flex flex-col bg-[#f8fafc] text-slate-800 bg-grid-pattern selection:bg-indigo-100 selection:text-indigo-900">
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        hasActiveAnalysis={!!activeAnalysisId}
        onOpenUpload={() => setIsUploadOpen(true)}
        rulesCount={brd?.business_rules.length || evidenceList.filter(e => e.category === 'business_rule').length}
        requirementsCount={brd?.functional_requirements.length}
        isAnalyzing={isAnalyzing}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-4">
        {currentTab === 'overview' && (
          <LandingOverview
            onStartSample={handleUseSample}
            onOpenUpload={() => setIsUploadOpen(true)}
            hasActiveAnalysis={!!activeAnalysisId}
            onViewAnalysis={() => setCurrentTab('timeline')}
          />
        )}

        {currentTab === 'timeline' && (
          <TimelineProgress
            status={status}
            logs={agentLogs}
            onRefresh={() => activeAnalysisId && getAnalysisStatus(activeAnalysisId).then(setStatus)}
          />
        )}

        {currentTab === 'code_intelligence' && (
          <CodeIntelligenceExplorer
            summary={status?.scan_summary || null}
            symbols={symbols}
            onSelectSymbol={(name) => {
              // search evidence for this symbol
              const match = evidenceList.find((e) => e.symbol_name.includes(name));
              if (match) {
                handleSelectEvidence(match.id);
              }
            }}
          />
        )}

        {currentTab === 'rules' && (
          <BusinessRulesPanel
            rules={brd?.business_rules || []}
            onSelectEvidence={handleSelectEvidence}
          />
        )}

        {currentTab === 'requirements' && (
          <RequirementsExplorer
            requirements={brd?.functional_requirements || []}
            selectedRequirementId={selectedRequirementId}
            onSelectRequirement={(req) => setSelectedRequirementId(req.id)}
            onSelectEvidence={handleSelectEvidence}
          />
        )}

        {currentTab === 'evidence' && (
          <SourceEvidenceViewer
            evidenceList={evidenceList}
            selectedEvidenceId={selectedEvidenceId}
            onSelectEvidence={(id) => setSelectedEvidenceId(id)}
          />
        )}

        {currentTab === 'impact' && (
          <ImpactExplorer graph={impactGraph} />
        )}

        {currentTab === 'workspace' && (
          <BrdWorkspace
            brd={brd}
            onUpdateRequirement={handleUpdateRequirement}
            onSubmitReview={handleSubmitReview}
            onExportDocx={handleExportDocx}
            isExporting={isExporting}
          />
        )}
      </main>

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadZip={handleUploadZip}
        onUseSample={handleUseSample}
        isLoading={isLoading}
      />

      {/* Footer */}
      <footer className="border-t border-slate-200/80 bg-white/70 backdrop-blur-sm py-5 text-center text-xs text-slate-500">
        <p className="font-medium text-slate-600">LegacyLens AI — Production-Oriented Agentic Business Analyst for Legacy .NET Reverse Engineering</p>
        <p className="text-[11px] text-slate-400 mt-1">Deterministic Roslyn AST Extraction · Amazon Bedrock Claude 3 · LangGraph Multi-Stage Workflow</p>
      </footer>
    </div>
  );
};
export default App;
