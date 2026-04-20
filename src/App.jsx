import React, { useState, useCallback } from 'react';
import FlowCanvas from './FlowCanvas';
import axios from 'axios';
import { Settings, Play, Terminal, Database, FileText, Search, Activity, CheckCircle, RefreshCcw } from 'lucide-react';

const API_BASE = "http://localhost:8000/api";

const App = () => {
  const [activeNode, setActiveNode] = useState(null);
  const [nodeStatus, setNodeStatus] = useState({}); // { 'node-1': 'success', 'node-2': 'executing' }
  const [logs, setLogs] = useState(["[System] Orchestrator ready."]);
  const [config, setConfig] = useState({ theme_description: "", project_title: "", review_word_count: 3000 });

  React.useEffect(() => {
    axios.get(`${API_BASE}/config`)
      .then(res => { if(res.data) setConfig(c => ({...c, ...res.data})); })
      .catch(err => addLog(`Config init error: ${err.message}`));
  }, []);

  const addLog = (msg) => setLogs(prev => [...prev.slice(-10), `[${new Date().toLocaleTimeString()}] ${msg}`]);

  const saveConfig = async () => {
    try {
        await axios.post(`${API_BASE}/update_config`, config);
        addLog(`Config saved for: ${config.project_title}`);
    } catch(err) {
        addLog(`Failed to save config: ${err.message}`);
    }
  };

  const runNode = async (nodeId) => {
    setNodeStatus(prev => ({ ...prev, [nodeId]: 'executing' }));
    addLog(`Starting execution for ${nodeId}...`);
    
    try {
      const resp = await axios.post(`${API_BASE}/run`, { node_id: nodeId });
      if (resp.data.status === 'started') {
        // We simulate a completion for the UI demo, but in real it would poll /status
        setTimeout(() => {
          setNodeStatus(prev => ({ ...prev, [nodeId]: 'success' }));
          addLog(`Node ${nodeId} execution complete.`);
        }, 5000);
      }
    } catch (err) {
      setNodeStatus(prev => ({ ...prev, [nodeId]: 'error' }));
      addLog(`Error triggering ${nodeId}: ${err.message}`);
    }
  };

  const startFullWorkflow = async () => {
    addLog("Initiating sequential search-to-draft pipeline...");
    // Sequence: 1 -> 2 -> 3 -> 4
    for (let i = 1; i <= 4; i++) {
        const id = `node-${i}`;
        await runNode(id);
        await new Promise(r => setTimeout(r, 6000)); // Wait for simulated step
    }
    addLog("Mission Finished. main.pdf is ready.");
  };

  return (
    <div className="app-container" style={{ display: 'flex', height: '100vh', width: '100vw', backgroundColor: 'var(--bg-dark)' }}>
      {/* Sidebar */}
      <aside className="glass-card" style={{ width: '320px', borderRight: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
          <h1 style={{ fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem', fontWeight: 700 }}>
            <Activity color="var(--accent)" className="anim-pulse" />
            ARA WORKFLOW
          </h1>
        </div>

        <div style={{ flex: 1, padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.05em' }}>CONFIGURATIONS</span>
            <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div className="glass-card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <div>
                        <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Project Title</label>
                        <input value={config.project_title || ''} onChange={e => setConfig({...config, project_title: e.target.value})} style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', color: 'white', borderRadius: '4px' }} />
                    </div>
                    <div>
                        <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Theme Context</label>
                        <textarea value={config.theme_description || ''} onChange={e => setConfig({...config, theme_description: e.target.value})} style={{ width: '100%', minHeight: '60px', padding: '0.5rem', marginTop: '0.25rem', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', color: 'white', borderRadius: '4px', resize: 'vertical' }} />
                    </div>
                    <div>
                        <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Target Words</label>
                        <input type="number" value={config.review_word_count || 3000} onChange={e => setConfig({...config, review_word_count: parseInt(e.target.value)})} style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-color)', color: 'white', borderRadius: '4px' }} />
                    </div>
                    <button onClick={saveConfig} style={{ background: 'rgba(255,255,255,0.1)', color: 'white', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', cursor: 'pointer', marginTop: '0.5rem', fontSize: '0.8rem' }}>
                        Save Config
                    </button>
                </div>
                <button onClick={startFullWorkflow} className="glow-primary" style={{ background: 'var(--primary)', color: 'white', padding: '1rem', borderRadius: '10px', border: 'none', cursor: 'pointer', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem' }}>
                    <Play size={20} fill="white" /> Launch Sequence
                </button>
            </div>
          </div>

          <div style={{ flex: 1 }}>
             <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.05em' }}>EVENT LOGS</span>
             <div style={{ marginTop: '1rem', fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--accent)', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {logs.map((log, i) => <div key={i}>{log}</div>)}
             </div>
          </div>
        </div>

        <div style={{ padding: '1rem', borderTop: '1px solid var(--border-color)', fontSize: '0.75rem', textAlign: 'center' }}>
          Expertise v1.0 • <span style={{ color: 'var(--primary)' }}>Deepmind Antigravity</span>
        </div>
      </aside>

      {/* Canvas */}
      <main style={{ flex: 1, position: 'relative' }}>
        <FlowCanvas onNodeFocus={setActiveNode} nodeStatus={nodeStatus} />
      </main>

      {/* Inspector Panel */}
      {activeNode && (
        <aside className="glass-card anim-slide-in" style={{ width: '400px', borderLeft: '1px solid var(--border-color)', padding: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
             <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Node Inspector</h2>
             <button onClick={() => setActiveNode(null)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>✕</button>
          </div>

          <div className="glass-card" style={{ padding: '1.5rem', border: '1px solid var(--primary)', background: 'linear-gradient(145deg, rgba(99,102,241,0.05) 0%, rgba(0,0,0,0) 100%)' }}>
             <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                <Search color="var(--primary)" size={32} />
                <div>
                    <h3 style={{ fontSize: '1rem' }}>{activeNode.data.label}</h3>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ID: {activeNode.id}</span>
                </div>
             </div>
             
             <div style={{ marginTop: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>STATUS</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem', color: nodeStatus[activeNode.id] === 'success' ? 'var(--success)' : 'var(--accent)' }}>
                        {nodeStatus[activeNode.id] === 'success' ? <CheckCircle size={16} /> : <RefreshCcw size={16} className="anim-pulse" />}
                        {nodeStatus[activeNode.id] || 'Idle'}
                    </div>
                </div>

                <button 
                    onClick={() => runNode(activeNode.id)}
                    style={{ background: 'rgba(255,255,255,0.05)', color: 'white', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)', cursor: 'pointer' }}
                >
                    Run This Node Individually
                </button>
             </div>
          </div>
        </aside>
      )}
    </div>
  );
};

export default App;
