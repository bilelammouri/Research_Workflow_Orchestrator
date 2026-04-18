import http.server
import socketserver
import json
import subprocess
import os
from urllib.parse import urlparse, parse_qs
import threading

PORT = 8000
CONFIG_PATH = "agent_config.json"

class OrchestratorHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        if self.path == '/api/update_config':
            print(f"[Backend] Updating configuration: {data}")
            try:
                # Merge existing config with new values
                current_conf = {}
                if os.path.exists(CONFIG_PATH):
                    with open(CONFIG_PATH, 'r') as f:
                        current_conf = json.load(f)
                
                current_conf.update(data)
                with open(CONFIG_PATH, 'w') as f:
                    json.dump(current_conf, f, indent=4)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "updated"}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())

        elif self.path == '/api/run':
            node_id = data.get('node_id')
            script_map = {
                'node-1': 'core/scopus_collector.py',
                'node-2': 'core/analysis_engine.R',
                'node-3': 'core/paper_ranker.py',
                'node-4': 'core/review_drafter.py'
            }
            script = script_map.get(node_id)
            if script:
                threading.Thread(target=self.execute_script, args=(script, node_id)).start()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"status": "started"}).encode())

    def execute_script(self, script_path, node_id):
        try:
            cmd = ["python", script_path]
            if script_path.endswith('.R'):
                # Ensure R detects its binary
                cmd = ["Rscript", script_path]
            print(f"[Exec] {script_path}...")
            subprocess.run(cmd, check=True)
        except Exception as e:
            print(f"[Error] {node_id}: {e}")

print(f"[Backend] Orchestrator Server running on port {PORT}...")
with socketserver.ThreadingTCPServer(("", PORT), OrchestratorHandler) as httpd:
    httpd.serve_forever()
