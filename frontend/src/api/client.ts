import {
  AnalysisStatus,
  AnalysisStreamEvent,
  BRDDocument,
  DiscoveredSymbol,
  EvidenceRecord,
  ImpactGraph,
  ReviewStatus,
} from '../types';

const API_BASE = '/api/v1';

export async function uploadRepository(file?: File, useSample: boolean = false): Promise<{ repository_id: string; name: string }> {
  const formData = new FormData();
  if (file) {
    formData.append('file', file);
  }
  formData.append('use_sample', String(useSample));

  const res = await fetch(`${API_BASE}/repositories`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function startAnalysis(repositoryId: string): Promise<{ analysis_id: string; status: string }> {
  const res = await fetch(`${API_BASE}/analyses/repositories/${repositoryId}/analyze`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Analysis failed to start' }));
    throw new Error(err.detail || 'Analysis start error');
  }
  return res.json();
}

export async function getAnalysisStatus(analysisId: string): Promise<AnalysisStatus> {
  const res = await fetch(`${API_BASE}/analyses/${analysisId}`);
  if (!res.ok) throw new Error('Failed to fetch analysis status');
  return res.json();
}

export async function getBRD(analysisId: string): Promise<BRDDocument> {
  const res = await fetch(`${API_BASE}/analyses/${analysisId}/brd`);
  if (!res.ok) throw new Error('Failed to fetch BRD');
  return res.json();
}

export async function getEvidence(analysisId: string, category?: string): Promise<EvidenceRecord[]> {
  const url = category ? `${API_BASE}/analyses/${analysisId}/evidence?category=${category}` : `${API_BASE}/analyses/${analysisId}/evidence`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch evidence');
  return res.json();
}

export async function getSymbols(analysisId: string): Promise<DiscoveredSymbol[]> {
  const res = await fetch(`${API_BASE}/analyses/${analysisId}/symbols`);
  if (!res.ok) throw new Error('Failed to fetch symbols');
  return res.json();
}

export async function getImpactGraph(analysisId: string): Promise<ImpactGraph> {
  const res = await fetch(`${API_BASE}/analyses/${analysisId}/impact-graph`);
  if (!res.ok) throw new Error('Failed to fetch impact graph');
  return res.json();
}

export async function updateRequirement(
  analysisId: string,
  reqId: string,
  payload: { title?: string; description?: string; review_status?: ReviewStatus; reviewer_notes?: string }
): Promise<BRDDocument> {
  const res = await fetch(`${API_BASE}/analyses/${analysisId}/requirements/${reqId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update requirement');
  return res.json();
}

export async function submitHumanReview(
  analysisId: string,
  decision: ReviewStatus,
  reviewerName: string,
  notes?: string
): Promise<BRDDocument> {
  const res = await fetch(`${API_BASE}/analyses/${analysisId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, reviewer_name: reviewerName, notes }),
  });
  if (!res.ok) throw new Error('Failed to submit review');
  return res.json();
}

export async function exportDocx(analysisId: string): Promise<{ export_id: string; download_url: string; filename: string }> {
  const res = await fetch(`${API_BASE}/analyses/${analysisId}/export`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to export DOCX');
  return res.json();
}

export function subscribeToAnalysisEvents(
  analysisId: string,
  onEvent: (event: AnalysisStreamEvent) => void,
  onError?: (err: any) => void
): () => void {
  const eventSource = new EventSource(`${API_BASE}/analyses/${analysisId}/events`);
  eventSource.onmessage = (e) => {
    try {
      const data: AnalysisStreamEvent = JSON.parse(e.data);
      onEvent(data);
    } catch (err) {
      console.error('Error parsing SSE event data:', err);
    }
  };
  eventSource.onerror = (err) => {
    if (onError) onError(err);
  };
  return () => {
    eventSource.close();
  };
}
