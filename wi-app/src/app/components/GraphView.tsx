import { useRef, useCallback, useEffect, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { GraphData, GraphNode } from '../types';
import { nodeColors } from '../utils/graphTransform';

interface GraphViewProps {
  data: GraphData;
  onNodeClick?: (node: GraphNode) => void;
  selectedNodeId?: string;
}

export function GraphView({ data, onNodeClick, selectedNodeId }: GraphViewProps) {
  const graphRef = useRef<any>();
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  const handleNodeClick = useCallback(
    (node: any) => {
      if (onNodeClick) {
        onNodeClick(node as GraphNode);
      }
    },
    [onNodeClick]
  );

  const nodeCanvasObject = useCallback(
    (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const label = node.label;
      const fontSize = 12 / globalScale;
      ctx.font = `${fontSize}px Inter, system-ui, sans-serif`;

      const isSelected = node.id === selectedNodeId;
      const nodeColor = nodeColors[node.type] || nodeColors.Entity;

      ctx.fillStyle = isSelected ? '#1e293b' : nodeColor;
      ctx.beginPath();
      ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI);
      ctx.fill();

      if (isSelected) {
        ctx.strokeStyle = nodeColor;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(node.x, node.y, 7, 0, 2 * Math.PI);
        ctx.stroke();
      }

      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = isSelected ? nodeColor : '#1e293b';
      ctx.fillText(label, node.x, node.y + 10);
    },
    [selectedNodeId]
  );

  return (
    <div ref={containerRef} className="w-full h-full bg-slate-50 rounded-lg border border-slate-200 overflow-hidden">
      {data.nodes.length > 0 ? (
        <ForceGraph2D
          ref={graphRef}
          graphData={data}
          width={dimensions.width}
          height={dimensions.height}
          nodeLabel="label"
          nodeCanvasObject={nodeCanvasObject}
          linkLabel="label"
          linkColor={() => '#cbd5e1'}
          linkWidth={1.5}
          linkDirectionalArrowLength={3.5}
          linkDirectionalArrowRelPos={1}
          onNodeClick={handleNodeClick}
          backgroundColor="#f8fafc"
          cooldownTime={3000}
          d3VelocityDecay={0.3}
        />
      ) : (
        <div className="flex items-center justify-center h-full text-slate-500">
          <div className="text-center">
            <p className="text-lg font-medium">No graph data available</p>
            <p className="text-sm mt-1">Upload a file or run a SPARQL query to visualize the graph</p>
          </div>
        </div>
      )}
    </div>
  );
}
