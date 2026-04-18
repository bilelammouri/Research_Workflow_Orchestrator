# ARA Research Orchestrator

A premium, node-based visual workflow for autonomous scientific research. This orchestrator transforms abstract research themes into structured academic literature reviews (PDF) using a multi-agent pipeline.

## 🌟 Visual Workflow
- **Canvas-Based Interface**: Drag & drop research nodes (Collector, Analyzer, Ranker, Drafter).
- **Dynamic Connections**: Animated Bezier curves showing real-time data flow.
- **Real-Time Configuration**: Adjust research themes and word counts directly from the sidebar.

## 📂 Project Structure
```text
Research_Workflow_Orchestrator/
├── index.html         # High-fidelity visual dashboard (Frontend)
├── server.py           # Zero-dependency Orchestration Server (Backend)
├── logo.png           # UI Identity asset
├── agent_config.json  # Live synchronized parameters
├── requirements.txt    # Python dependencies
└── core/              # Autonomous Research Agents
    ├── scopus_collector.py
    ├── analysis_engine.R
    ├── paper_ranker.py
    └── review_drafter.py
```

## 🚀 Getting Started

### 1. Installation
Ensure you have Python 3.10+ and R installed.
```bash
pip install -r requirements.txt
```

### 2. Configuration
The orchestrator automatically manages your parameters. Make sure your Scopus API Key is present in `agent_config.json`.

### 3. Launch
1. **Start the Backend**:
   ```bash
   python server.py
   ```
2. **Open the Dashboard**:
   Open `index.html` in any modern web browser (Chrome, Edge, Safari).
3. **Deploy**:
   Type your theme in the sidebar, adjust word counts, and click **"Launch Deployment"**.

## 🛠 Technology Stack
- **Frontend**: Vanilla JS, Tailwind CSS, Lucide Icons, SVG Bezier Engine.
- **Backend**: Python multi-threaded HTTP server (Zero-dependency).
- **Agents**: Python (Scopus API), R (Bibliometrix).
