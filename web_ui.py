# -*- coding: utf-8 -*-
"""
Ghost Agent Web UI - Port 26602
Ghost & Jake
"""
import json, re, sys
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent))
from ghost_v21 import GhostAgent

_agent = None

def get_agent():
    global _agent
    if _agent is None:
        _agent = GhostAgent()
    return _agent

PAGE = '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Ghost Agent</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui,sans-serif;background:#0a0a0f;color:#e0e0e0;min-height:100vh}.header{background:linear-gradient(135deg,#1a1a2e,#16213e);padding:16px 24px;border-bottom:1px solid #2a2a4a;display:flex;align-items:center;gap:12px}.header h1{font-size:20px;color:#00d4ff}.status{margin-left:auto;font-size:12px;color:#666}.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#00ff88;margin-right:6px;animation:pulse 2s infinite}@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}.main{max-width:900px;margin:0 auto;padding:24px}.chat{background:#111118;border-radius:12px;border:1px solid #2a2a4a;overflow:hidden}.messages{height:60vh;min-height:400px;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:16px}.message{display:flex;gap:12px;animation:fadeIn .3s ease}@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}.avatar{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0}.avatar.u{background:#2a2a4a}.avatar.g{background:linear-gradient(135deg,#00d4ff,#0088ff)}.bubble{background:#1a1a2e;border-radius:12px;padding:12px 16px;max-width:80%;line-height:1.6;font-size:14px;border:1px solid #2a2a4a}.bubble.u{background:#1e1e3a;margin-left:auto}.bubble pre{background:#0a0a0f;border-radius:8px;padding:12px;overflow-x:auto;font-size:13px;margin:8px 0;border:1px solid #2a2a4a}.s{color:#00ff88}.e{color:#ff4444}.i{color:#00d4ff}.input-area{padding:16px 20px;border-top:1px solid #2a2a4a;display:flex;gap:12px;background:#0e0e16}.input-area input{flex:1;background:#1a1a2e;border:1px solid #2a2a4a;border-radius:8px;padding:12px 16px;color:#e0e0e0;font-size:14px;outline:none}.input-area input:focus{border-color:#00d4ff}.input-area input::placeholder{color:#555}.input-area button{background:linear-gradient(135deg,#00d4ff,#0088ff);border:none;border-radius:8px;padding:12px 24px;color:#fff;font-size:14px;font-weight:600;cursor:pointer}.input-area button:hover{opacity:.85}.input-area button:disabled{opacity:.4;cursor:not-allowed}.footer{text-align:center;padding:16px;font-size:12px;color:#444}.footer a{color:#00d4ff;text-decoration:none}.qa{display:flex;gap:8px;flex-wrap:wrap;padding:12px 20px;border-top:1px solid #2a2a4a}.qa button{background:#1a1a2e;border:1px solid #2a2a4a;border-radius:6px;padding:6px 14px;color:#888;font-size:12px;cursor:pointer}.qa button:hover{border-color:#00d4ff;color:#00d4ff}</style></head><body><div class="header"><span style="font-size:24px">&#128123;</span><h1>Ghost Agent</h1><div class="status"><span class="dot"></span>Online | Port 26602</div></div><div class="main"><div class="chat"><div class="messages" id="m"><div class="message"><div class="avatar g">&#128123;</div><div class="bubble g"><span class="i">Ghost Agent v2.1</span><br>&#20320;&#22909;&#65292;&#25105;&#26159; Ghost Agent &#128123;<br>&#21487;&#20197;&#24110;&#20320;&#20889;&#20195;&#30721;&#12289;&#35843;&#35797;&#12289;&#33258;&#21160;&#20462;&#22797;&#12290;</div></div></div><div class="qa"><button onclick="sq(&#39;write a data analysis script&#39;)">&#128202; Data Analysis</button><button onclick="sq(&#39;write a math calculator&#39;)">&#128437; Calculator</button><button onclick="sq(&#39;write a web API server&#39;)">&#128295; API Server</button><button onclick="sq(&#39;write a file organizer&#39;)">&#128193; File Organizer</button><button onclick="sq(&#39;status&#39;)">&#128269; Status</button></div><div class="input-area"><input type="text" id="i" placeholder="Enter requirement..." onkeydown="if(event.key===\'Enter\')send()"><button id="b" onclick="send()">Send</button></div></div></div><div class="footer">Ghost Agent v2.1 &copy; 2026 <a href="https://gitee.com/Jake26602/Ghost-Agent">Gitee</a> | MIT License</div><script>function sq(t){document.getElementById("i").value=t;send()}function send(){var i=document.getElementById("i");var t=i.value.trim();if(!t)return;i.value="";add("u",t);document.getElementById("b").disabled=true;fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:t})}).then(function(r){return r.json()}).then(function(d){document.getElementById("b").disabled=false;var c="";if(d.success){c=\'<span class="s">&#10003; Done!</span>\';if(d.output)c+="<pre>"+esc(d.output)+"</pre>"}else{c=\'<span class="e">&#10007; Failed</span>\';if(d.error)c+="<pre>"+esc(d.error)+"</pre>"}add("g",c)}).catch(function(e){document.getElementById("b").disabled=false;add("g",\'<span class="e">Error: \'+esc(String(e))+"</span>")})}function add(t,c){var m=document.getElementById("m");var d=document.createElement("div");d.className="message";var av=t==="u"?"&#128100;":"&#128123;";d.innerHTML=\'<div class="avatar \'+\'u\'+\'">\'+av+\'</div><div class="bubble \'+\'u\'+\'">\'+c+"</div>";m.appendChild(d);m.scrollTop=m.scrollHeight}function esc(t){var d=document.createElement("div");d.textContent=t;return d.innerHTML}</script></body></html>'


class Handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        p = urlparse(self.path)
        if p.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(PAGE.encode("utf-8"))
        elif p.path == "/api/status":
            a = get_agent()
            self.send_json({"status": "ok", "version": "2.1", "tasks": len(a.history)})
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        p = urlparse(self.path)
        if p.path == "/api/chat":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            msg = body.get("message", "").strip()
            
            if not msg:
                self.send_json({"success": False, "error": "Empty message"})
                return
            
            if msg.lower() == "status":
                a = get_agent()
                info = "Ghost Agent v2.1\nBackend: " + a.ai.__class__.__name__ + "\nTasks: " + str(len(a.history))
                self.send_json({"success": True, "output": info})
                return
            
            try:
                a = get_agent()
                result = a.do(msg)
                self.send_json({
                    "success": result["success"],
                    "output": (result.get("output") or "")[:1000],
                    "error": (result.get("error") or "")[:500] if not result["success"] else None,
                })
            except Exception as e:
                self.send_json({"success": False, "error": str(e)[:500]})
        else:
            self.send_response(404)
            self.end_headers()
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    
    def log_message(self, *a):
        pass


def main():
    port = 26602
    server = HTTPServer(("0.0.0.0", port), Handler)
    print("Ghost Agent Web UI")
    print("URL: http://localhost:" + str(port))
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")


if __name__ == "__main__":
    main()
