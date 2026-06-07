import { X, Info } from 'lucide-react';
import { GraphNode, GraphData } from '../types';
import { nodeColors } from '../utils/graphTransform';

interface DetailsPanelProps {
  node: GraphNode | null;
  graphData: GraphData;
  onClose: () => void;
}

export function DetailsPanel({ node, graphData, onClose }: DetailsPanelProps) {
  if (!node) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <div className="flex items-center gap-2 text-slate-400">
          <Info className="w-5 h-5" />
          <p>Click on a node to view details</p>
        </div>
      </div>
    );
  }

  const nodeColor = nodeColors[node.type] || nodeColors.Entity;

  const outgoingLinks = graphData.links.filter((link) => link.source === node.id || (typeof link.source === 'object' && (link.source as any).id === node.id));
  const incomingLinks = graphData.links.filter((link) => link.target === node.id || (typeof link.target === 'object' && (link.target as any).id === node.id));

  return (
    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
        <h3 className="font-semibold text-slate-800">Node Details</h3>
        <button
          onClick={onClose}
          className="p-1 hover:bg-slate-200 rounded transition-colors"
        >
          <X className="w-4 h-4 text-slate-600" />
        </button>
      </div>

      <div className="p-4 space-y-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span
              className="w-4 h-4 rounded-full"
              style={{ backgroundColor: nodeColor }}
            />
            <span className="font-semibold text-lg text-slate-800">{node.label}</span>
          </div>
          <div className="text-sm text-slate-500">
            <span className="font-medium">Type:</span> {node.type}
          </div>
        </div>

        <div className="border-t border-slate-200 pt-4">
          <div className="text-sm font-medium text-slate-700 mb-2">URI</div>
          <div className="text-xs text-slate-600 bg-slate-50 p-2 rounded border border-slate-200 break-all font-mono">
            {node.id}
          </div>
        </div>

        {outgoingLinks.length > 0 && (
          <div className="border-t border-slate-200 pt-4">
            <div className="text-sm font-medium text-slate-700 mb-2">
              Outgoing Relations ({outgoingLinks.length})
            </div>
            <div className="space-y-2">
              {outgoingLinks.map((link, idx) => {
                const targetId = typeof link.target === 'object' ? (link.target as any).id : link.target;
                const targetNode = graphData.nodes.find((n) => n.id === targetId);
                return (
                  <div key={idx} className="text-xs bg-slate-50 p-2 rounded border border-slate-200">
                    <div className="font-medium text-slate-700">{link.label}</div>
                    <div className="text-slate-500 mt-1">→ {targetNode?.label || targetId}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {incomingLinks.length > 0 && (
          <div className="border-t border-slate-200 pt-4">
            <div className="text-sm font-medium text-slate-700 mb-2">
              Incoming Relations ({incomingLinks.length})
            </div>
            <div className="space-y-2">
              {incomingLinks.map((link, idx) => {
                const sourceId = typeof link.source === 'object' ? (link.source as any).id : link.source;
                const sourceNode = graphData.nodes.find((n) => n.id === sourceId);
                return (
                  <div key={idx} className="text-xs bg-slate-50 p-2 rounded border border-slate-200">
                    <div className="font-medium text-slate-700">{link.label}</div>
                    <div className="text-slate-500 mt-1">← {sourceNode?.label || sourceId}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
