import { useState, useEffect } from 'react';
import { Database } from 'lucide-react';
import { GraphView } from './components/GraphView';
import { QueryPanel } from './components/QueryPanel';
import { FilterPanel } from './components/FilterPanel';
import { DetailsPanel } from './components/DetailsPanel';
import { UploadPanel } from './components/UploadPanel';
import { GraphData, GraphNode, SparqlResponse, ProcessResponse } from './types';
import { sparqlToGraphData } from './utils/graphTransform';

export default function App() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [filteredGraphData, setFilteredGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedType, setSelectedType] = useState<string>('all');

  useEffect(() => {
    if (selectedType === 'all') {
      setFilteredGraphData(graphData);
    } else {
      const filteredNodes = graphData.nodes.filter((node) => node.type === selectedType);
      const nodeIds = new Set(filteredNodes.map((n) => n.id));
      const filteredLinks = graphData.links.filter(
        (link) => {
          const sourceId = typeof link.source === 'object' ? (link.source as any).id : link.source;
          const targetId = typeof link.target === 'object' ? (link.target as any).id : link.target;
          return nodeIds.has(sourceId) && nodeIds.has(targetId);
        }
      );
      setFilteredGraphData({ nodes: filteredNodes, links: filteredLinks });
    }
  }, [graphData, selectedType]);

  const handleQueryResult = (data: SparqlResponse) => {
    const graphData = sparqlToGraphData(data.results);
    setGraphData(graphData);
    setSelectedNode(null);
  };

  const handleProcessComplete = (data: ProcessResponse) => {
    const nodes: GraphNode[] = data.entities.map((entity) => ({
      id: entity.uri_name,
      label: entity.label,
      type: entity.entity_type,
    }));

    const links = data.relations.map((relation) => ({
      source: relation.subject,
      target: relation.object,
      label: relation.predicate,
    }));

    const newGraphData = { nodes, links };
    setGraphData(newGraphData);
    setSelectedNode(null);
  };

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node);
  };

  const handleCloseDetails = () => {
    setSelectedNode(null);
  };

  return (
    <div className="size-full bg-gradient-to-br from-slate-50 to-slate-100 overflow-auto">
      <div className="min-h-full p-6 flex flex-col gap-6">
        <header className="flex items-center gap-3 pb-4 border-b border-slate-200 flex-shrink-0">
          <Database className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-slate-800">GraphDB Knowledge Graph Visualizer</h1>
            <p className="text-sm text-slate-600">Smart Home NLP to RDF Pipeline</p>
          </div>
        </header>

        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-8 space-y-6">
            <div className="h-[600px]">
              <GraphView
                data={filteredGraphData}
                onNodeClick={handleNodeClick}
                selectedNodeId={selectedNode?.id}
              />
            </div>
            <div>
              <UploadPanel onProcessComplete={handleProcessComplete} />
            </div>
          </div>

          <div className="col-span-4 space-y-6">
            <div>
              <FilterPanel selectedType={selectedType} onTypeChange={setSelectedType} />
            </div>
            <div>
              <DetailsPanel
                node={selectedNode}
                graphData={graphData}
                onClose={handleCloseDetails}
              />
            </div>
            <div>
              <QueryPanel onQueryResult={handleQueryResult} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}