import React, { useState, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  Position,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Network, Scale, Code, Layers, FileText, CheckCircle2, AlertCircle, Info, TestTube } from 'lucide-react';
import { ImpactGraph, ImpactNode } from '../types';

interface ImpactExplorerProps {
  graph: ImpactGraph | null;
}

export const ImpactExplorer: React.FC<ImpactExplorerProps> = ({ graph }) => {
  const [selectedNode, setSelectedNode] = useState<ImpactNode | null>(null);

  // Transform backend graph nodes and edges into React Flow format
  const { nodes, edges } = useMemo(() => {
    if (!graph) return { nodes: [], edges: [] };

    const flowNodes: Node[] = [];
    const flowEdges: Edge[] = [];

    // Group nodes by type to compute pleasant layered x,y coordinates
    const rules = graph.nodes.filter((n) => n.node_type === 'rule');
    const methods = graph.nodes.filter((n) => n.node_type === 'method');
    const requirements = graph.nodes.filter((n) => n.node_type === 'requirement');
    const acceptance = graph.nodes.filter((n) => n.node_type === 'acceptance_criteria');

    const columnX = {
      rule: 50,
      method: 380,
      requirement: 720,
      acceptance_criteria: 1080,
    };

    const nodeColors: Record<string, { bg: string; border: string; text: string }> = {
      rule: { bg: '#fffbeb', border: '#f59e0b', text: '#92400e' },
      method: { bg: '#faf5ff', border: '#a855f7', text: '#6b21a8' },
      requirement: { bg: '#eff6ff', border: '#3b82f6', text: '#1e40af' },
      acceptance_criteria: { bg: '#ecfdf5', border: '#10b981', text: '#065f46' },
    };

    const placeNodes = (items: ImpactNode[], colKey: 'rule' | 'method' | 'requirement' | 'acceptance_criteria') => {
      items.forEach((item, idx) => {
        const c = nodeColors[colKey];
        flowNodes.push({
          id: item.id,
          data: { label: item.label, raw: item },
          position: { x: columnX[colKey], y: 60 + idx * 110 },
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
          style: {
            background: c.bg,
            border: `1.5px solid ${c.border}`,
            color: c.text,
            borderRadius: '10px',
            padding: '12px 14px',
            fontSize: '11px',
            fontWeight: 600,
            width: 250,
            boxShadow: '0 2px 8px rgba(15, 23, 42, 0.06)',
          },
        });
      });
    };

    placeNodes(rules, 'rule');
    placeNodes(methods, 'method');
    placeNodes(requirements, 'requirement');
    placeNodes(acceptance, 'acceptance_criteria');

    graph.edges.forEach((e) => {
      flowEdges.push({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#6366f1', strokeWidth: 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1' },
        labelStyle: { fill: '#64748b', fontSize: 10, fontWeight: 600 },
      });
    });

    return { nodes: flowNodes, edges: flowEdges };
  }, [graph]);

  const handleNodeClick = (_: any, node: Node) => {
    const raw = (node.data as any).raw as ImpactNode;
    setSelectedNode(raw);
  };

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="rounded-2xl bg-white border border-slate-200/90 p-12 text-center text-slate-500 shadow-sm">
        <Network className="w-10 h-10 mx-auto mb-3 text-slate-400" />
        <h4 className="text-sm font-semibold text-slate-800 mb-1">No Impact Graph Available</h4>
        <p className="text-xs text-slate-500">Run an analysis to generate the interactive Business Rule Impact trace.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 py-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200/80 pb-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <Network className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-bold text-slate-900">Business Rule Impact Explorer</h3>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 uppercase tracking-wide">
              Traceability Graph
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Interactive trace: <span className="text-amber-700 font-mono font-medium">Business Rule</span> → <span className="text-purple-700 font-mono font-medium">Source Method</span> → <span className="text-blue-700 font-mono font-medium">Requirement</span> → <span className="text-emerald-700 font-mono font-medium">Acceptance Criteria</span>
          </p>
        </div>

        <div className="flex items-center space-x-3 text-[11px] font-medium">
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block shadow-sm"></span><span className="text-slate-600">Rules</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-purple-500 inline-block shadow-sm"></span><span className="text-slate-600">Methods</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block shadow-sm"></span><span className="text-slate-600">Requirements</span></span>
          <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block shadow-sm"></span><span className="text-slate-600">Acceptance</span></span>
        </div>
      </div>

      {/* Main Flow Canvas & Side Inspection Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 h-[600px] rounded-2xl bg-white border border-slate-200/90 overflow-hidden relative shadow-sm">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodeClick={handleNodeClick}
            fitView
          >
            <Background color="#cbd5e1" gap={18} size={1.5} />
            <Controls className="bg-white border border-slate-200 text-slate-700 shadow-sm rounded-xl overflow-hidden" />
            <MiniMap
              nodeStrokeColor="#6366f1"
              nodeColor="#f1f5f9"
              className="bg-white border border-slate-200 rounded-xl shadow-sm"
            />
          </ReactFlow>
        </div>

        {/* Impact Inspector Side Panel */}
        <div className="lg:col-span-4 rounded-2xl bg-white border border-slate-200/90 p-5 space-y-4 shadow-sm">
          <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
            <Info className="w-4 h-4 text-indigo-600" />
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              {selectedNode ? 'Relationship Inspection' : 'Select Node to Inspect'}
            </h4>
          </div>

          {selectedNode ? (
            <div className="space-y-4 text-xs">
              <div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded uppercase font-bold bg-slate-100 text-slate-700 border border-slate-200">
                  {selectedNode.node_type}
                </span>
                <h5 className="text-sm font-bold text-slate-900 mt-2">{selectedNode.label}</h5>
              </div>

              {selectedNode.details.description && (
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
                  <span className="text-slate-500 block mb-1 font-semibold text-[11px] uppercase tracking-wide">Description</span>
                  <p className="text-slate-700 leading-relaxed">{selectedNode.details.description}</p>
                </div>
              )}

              {selectedNode.details.threshold && (
                <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200/80">
                  <span className="text-amber-800 block mb-1 font-semibold text-[11px] uppercase tracking-wide">Enforced Rule Condition</span>
                  <p className="text-amber-900 font-mono font-bold text-xs">{selectedNode.details.threshold}</p>
                </div>
              )}

              {selectedNode.details.scenario && (
                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5 font-mono text-[11px] text-slate-200 shadow-sm">
                  <span className="text-slate-400 block mb-1 font-semibold font-sans text-xs">Validation Test Scenario</span>
                  <p className="text-white font-bold">{selectedNode.details.scenario}</p>
                  <p className="text-sky-300">Given: {selectedNode.details.given}</p>
                  <p className="text-amber-300">When: {selectedNode.details.when}</p>
                  <p className="text-emerald-300">Then: {selectedNode.details.then}</p>
                </div>
              )}

              {selectedNode.details.source_file && (
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-[11px] font-mono text-slate-600 truncate">
                  <span className="font-semibold text-slate-500 font-sans">File: </span>{selectedNode.details.source_file}
                </div>
              )}

              <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-500 space-y-1">
                <p className="flex items-center space-x-1.5 text-emerald-700 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>Relationship confirmed via deterministic code scanner.</span>
                </p>
              </div>
            </div>
          ) : (
            <div className="py-16 text-center text-slate-400 space-y-2">
              <Network className="w-8 h-8 mx-auto text-slate-300" />
              <p className="text-xs text-slate-500">
                Click any node in the interactive graph above to view its ripple effect, connected services, and Gherkin test scenarios.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
