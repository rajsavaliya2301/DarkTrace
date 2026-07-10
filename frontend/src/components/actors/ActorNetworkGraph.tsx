import { useEffect, useRef } from 'react';
import cytoscape, { type Core } from 'cytoscape';
import type { NetworkGraph } from '../../types';
import { SEVERITY_COLORS } from '../../utils/constants';

interface ActorNetworkGraphProps {
  graph: NetworkGraph;
}

const nodeColors: Record<string, string> = {
  actor: '#a855f7',
  site: '#3b82f6',
  address: '#f59e0b',
  email: '#10b981',
};

export default function ActorNetworkGraph({
  graph,
}: ActorNetworkGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  useEffect(() => {
    if (!containerRef.current || !graph) return;

    const elements = [
      ...graph.nodes.map((node) => ({
        data: {
          id: node.id,
          label: node.label,
          type: node.type,
          riskScore: node.risk_score,
        },
      })),
      ...graph.edges.map((edge, idx) => ({
        data: {
          id: `edge-${idx}`,
          source: edge.source,
          target: edge.target,
          label: edge.label,
          count: edge.count,
        },
      })),
    ];

    if (cyRef.current) {
      cyRef.current.destroy();
    }

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': (ele: cytoscape.NodeSingular) =>
              nodeColors[ele.data('type')] || '#6b7280',
            label: 'data(label)',
            color: '#e5e7eb',
            'font-size': '11px',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            width: (ele: cytoscape.NodeSingular) =>
              ele.data('type') === 'actor' ? 40 : 30,
            height: (ele: cytoscape.NodeSingular) =>
              ele.data('type') === 'actor' ? 40 : 30,
            'border-width': 2,
            'border-color': (ele: cytoscape.NodeSingular) => {
              if (ele.data('type') === 'actor' && ele.data('riskScore')) {
                const score = ele.data('riskScore');
                if (score >= 700) return '#ef4444';
                if (score >= 500) return '#f59e0b';
                return '#6b7280';
              }
              return 'transparent';
            },
            'border-opacity': 0.8,
          },
        },
        {
          selector: 'edge',
          style: {
            'line-color': '#374151',
            'target-arrow-color': '#374151',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            width: 1.5,
            label: (ele: cytoscape.EdgeSingular) => {
              const count = ele.data('count');
              const label = ele.data('label');
              return count ? `${label} (${count})` : label;
            },
            'font-size': '9px',
            color: '#6b7280',
            'text-rotation': 'autorotate',
            'text-margin-x': 4,
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-color': '#3b82f6',
            'border-width': 3,
          },
        },
      ],
      layout: {
        name: 'cose',
        fit: true,
        padding: 30,
        nodeRepulsion: () => 8000,
        idealEdgeLength: () => 120,
        gravity: 0.25,
      },
      userZoomingEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: false,
      minZoom: 0.5,
      maxZoom: 3,
    });

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [graph]);

  if (!graph || !graph.nodes || graph.nodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-gray-500">
        No network data available
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="h-full w-full rounded-lg bg-dark-surface"
      role="img"
      aria-label="Actor relationship network graph"
    />
  );
}
