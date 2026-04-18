import React, { useState, useCallback, useMemo } from 'react';
import ReactFlow, { 
  addEdge, 
  Background, 
  Controls, 
  applyEdgeChanges, 
  applyNodeChanges,
  MarkerType,
  Handle,
  Position
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Search, Database, BarChart3, Edit3, CheckCircle, Loader2 } from 'lucide-react';

// Custom Node Component for Premium Feel
const ResearchNode = ({ data, selected }) => {
    const isExecuting = data.status === 'executing';
    const isSuccess = data.status === 'success';

    return (
        <div className={`node-container ${selected ? 'node-active' : ''} ${isSuccess ? 'node-success' : ''}`}>
            <Handle type="target" position={Position.Left} className="handle-custom" />
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div className="glass-card" style={{ padding: '0.5rem', display: 'flex' }}>
                    {data.icon}
                </div>
                <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{data.label}</div>
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{data.description}</div>
                </div>
                {isExecuting && <Loader2 size={16} className="anim-pulse" color="var(--accent)" />}
                {isSuccess && <CheckCircle size={16} color="var(--success)" />}
            </div>

            <Handle type="source" position={Position.Right} className="handle-custom" />
        </div>
    );
};

const nodeTypes = {
    research: ResearchNode,
};

const FlowCanvas = ({ onNodeFocus, nodeStatus }) => {
  const initialNodes = useMemo(() => [
    {
      id: 'node-1',
      type: 'research',
      data: { 
          label: 'Scopus Collector', 
          description: 'API Data Harvesting', 
          icon: <Search size={18} color="var(--primary)" />,
          status: nodeStatus['node-1']
      },
      position: { x: 50, y: 150 },
    },
    {
      id: 'node-2',
      type: 'research',
      data: { 
          label: 'Analysis Engine', 
          description: 'R Bibliometrics', 
          icon: <Database size={18} color="var(--secondary)" />,
          status: nodeStatus['node-2']
      },
      position: { x: 350, y: 150 },
    },
    {
      id: 'node-3',
      type: 'research',
      data: { 
          label: 'Paper Ranker', 
          description: 'Citation Scoring', 
          icon: <BarChart3 size={18} color="var(--accent)" />,
          status: nodeStatus['node-3']
      },
      position: { x: 650, y: 150 },
    },
    {
      id: 'node-4',
      type: 'research',
      data: { 
          label: 'Review Drafter', 
          description: 'LaTeX Synthesis', 
          icon: <Edit3 size={18} color="var(--success)" />,
          status: nodeStatus['node-4']
      },
      position: { x: 950, y: 150 },
    },
  ], [nodeStatus]);

  const [nodes, setNodes] = useState(initialNodes);
  const [edges, setEdges] = useState([
    { id: 'e1-2', source: 'node-1', target: 'node-2', animated: nodeStatus['node-1'] === 'executing', markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1' } },
    { id: 'e2-3', source: 'node-2', target: 'node-3', animated: nodeStatus['node-2'] === 'executing', markerEnd: { type: MarkerType.ArrowClosed, color: '#a855f7' } },
    { id: 'e3-4', source: 'node-3', target: 'node-4', animated: nodeStatus['node-3'] === 'executing', markerEnd: { type: MarkerType.ArrowClosed, color: '#10b981' } },
  ]);

  // Sync nodes when status changes
  React.useEffect(() => {
      setNodes(initialNodes);
      setEdges(prev => prev.map(edge => ({
          ...edge,
          animated: nodeStatus[edge.source] === 'executing'
      })));
  }, [nodeStatus, initialNodes]);

  const onNodesChange = useCallback((changes) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);
  const onConnect = useCallback((connection) => setEdges((eds) => addEdge(connection, eds)), []);

  return (
    <div style={{ height: '100%', width: '100%', background: '#050507' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={(e, n) => onNodeFocus(n)}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background variant="dots" gap={25} size={1} color="#222" />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
};

export default FlowCanvas;
