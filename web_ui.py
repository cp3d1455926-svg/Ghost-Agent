# -*- coding: utf-8 -*-
"""
Ghost Agent Web UI v3.0 - Awwwards 2026 Style
Port 26602
Design: Glassmorphism + Aurora + Micro-animations + Bento Grid
Ghost & Jake
"""
import json, re, sys
from pathlib import Path
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

PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Ghost Agent - 智能代码助手</title>
<style>
:root {
  --bg: #08080c;
  --bg-card: rgba(255,255,255,0.03);
  --bg-glass: rgba(255,255,255,0.06);
  --border: rgba(255,255,255,0.08);
  --border-hover: rgba(255,255,255,0.15);
  --text: #e8e8f0;
  --text-dim: #8888a0;
  --text-muted: #555570;
  --accent: #7c5cfc;
  --accent2: #06d6a0;
  --accent3: #ff6b9d;
  --gradient: linear-gradient(135deg, #7c5cfc, #06d6a0, #ff6b9d);
  --gradient-text: linear-gradient(135deg, #a78bfa, #34d399);
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: var(--bg);
  color: var(--text);
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Aurora background */
body::before {
  content: '';
  position: fixed;
  top: -50%; left: -50%;
  width: 200%; height: 200%;
  background: radial-gradient(ellipse at 20% 50%, rgba(124,92,252,0.08) 0%, transparent 50%),
              radial-gradient(ellipse at 80% 20%, rgba(6,214,160,0.06) 0%, transparent 50%),
              radial-gradient(ellipse at 50% 80%, rgba(255,107,157,0.05) 0%, transparent 50%);
  animation: aurora 20s ease-in-out infinite;
  pointer-events: none;
  z-index: 0;
}
@keyframes aurora {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  25% { transform: translate(2%, -3%) rotate(1deg); }
  50% { transform: translate(-1%, 2%) rotate(-1deg); }
  75% { transform: translate(3%, 1%) rotate(0.5deg); }
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--border-hover); }

/* Header */
.header {
  position: relative; z-index: 1;
  background: var(--bg-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  padding: 14px 24px;
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}
.logo {
  width: 38px; height: 38px;
  background: var(--gradient);
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
  box-shadow: 0 4px 20px rgba(124,92,252,0.3);
  animation: logoGlow 3s ease-in-out infinite;
}
@keyframes logoGlow {
  0%, 100% { box-shadow: 0 4px 20px rgba(124,92,252,0.3); }
  50% { box-shadow: 0 4px 30px rgba(124,92,252,0.5), 0 0 40px rgba(6,214,160,0.2); }
}
.header h1 {
  font-size: 17px; font-weight: 700;
  background: var(--gradient-text);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.header .subtitle { font-size: 11px; color: var(--text-muted); margin-top: 1px; }
.header .status {
  margin-left: auto;
  display: flex; align-items: center; gap: 6px;
  font-size: 11px; color: var(--accent2);
  background: rgba(6,214,160,0.1);
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px solid rgba(6,214,160,0.2);
}
.header .status .dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--accent2);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

/* Layout */
.container {
  display: flex; flex: 1; overflow: hidden;
  position: relative; z-index: 1;
}

/* Sidebar - Glassmorphism */
.sidebar {
  width: 280px; flex-shrink: 0;
  background: var(--bg-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
}
.sidebar-header {
  padding: 20px 20px 12px;
  font-size: 11px; font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
}
.sidebar-nav { padding: 4px 12px; flex: 1; overflow-y: auto; }
.nav-item {
  padding: 10px 14px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-dim);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 2px;
  border: 1px solid transparent;
}
.nav-item:hover {
  background: var(--bg-glass);
  color: var(--text);
  border-color: var(--border);
}
.nav-item.active {
  background: rgba(124,92,252,0.12);
  color: var(--accent);
  border-color: rgba(124,92,252,0.2);
}
.nav-item .icon { font-size: 15px; width: 22px; text-align: center; opacity: 0.8; }
.sidebar-footer {
  padding: 14px 20px;
  border-top: 1px solid var(--border);
  font-size: 10px; color: var(--text-muted);
  text-align: center;
}

/* Main */
.main {
  flex: 1; display: flex; flex-direction: column;
  overflow: hidden;
  background: rgba(255,255,255,0.01);
}

/* Messages */
.messages {
  flex: 1; overflow-y: auto;
  padding: 28px 32px;
  display: flex; flex-direction: column; gap: 28px;
  scroll-behavior: smooth;
}

/* Message */
.message {
  display: flex; gap: 16px;
  animation: msgIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  max-width: 820px;
}
@keyframes msgIn {
  from { opacity: 0; transform: translateY(12px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.message.user { flex-direction: row-reverse; }

.avatar {
  width: 38px; height: 38px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 17px; flex-shrink: 0;
}
.avatar.ghost {
  background: var(--gradient);
  box-shadow: 0 4px 15px rgba(124,92,252,0.25);
}
.avatar.user {
  background: rgba(6,214,160,0.15);
  border: 1px solid rgba(6,214,160,0.25);
}

/* Bubble - Glassmorphism */
.bubble {
  background: var(--bg-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 16px 20px;
  line-height: 1.75;
  font-size: 14px;
  max-width: 720px;
  position: relative;
  transition: border-color 0.2s;
}
.bubble:hover { border-color: var(--border-hover); }
.bubble.user {
  background: rgba(124,92,252,0.08);
  border-color: rgba(124,92,252,0.2);
}
.bubble.user:hover { border-color: rgba(124,92,252,0.35); }

.bubble .role {
  font-size: 10px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.8px;
  margin-bottom: 8px; opacity: 0.6;
}
.bubble.ghost .role { color: var(--accent); }
.bubble.user .role { color: var(--accent2); }

/* Code blocks */
.bubble pre {
  background: rgba(0,0,0,0.4);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  overflow-x: auto;
  font-size: 13px;
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  margin: 12px 0;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}
.bubble code {
  font-family: 'SF Mono', 'Fira Code', monospace;
  background: rgba(0,0,0,0.3);
  padding: 2px 7px;
  border-radius: 5px;
  font-size: 12px;
  border: 1px solid var(--border);
}

/* Status */
.bubble .success { color: var(--accent2); font-weight: 600; }
.bubble .error { color: var(--accent3); font-weight: 600; }
.bubble .info { color: var(--accent); }

/* Typing */
.typing { display: flex; gap: 5px; padding: 6px 0; }
.typing span {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--accent);
  animation: typing 1.4s infinite;
}
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
  30% { transform: translateY(-8px); opacity: 1; }
}

/* Input Area - Glassmorphism */
.input-area {
  padding: 16px 28px 20px;
  background: var(--bg-glass);
  backdrop-filter: blur(20px);
  border-top: 1px solid var(--border);
}
.input-wrap { max-width: 820px; margin: 0 auto; }

.input-box {
  display: flex; align-items: flex-end; gap: 12px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 14px 18px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.input-box:focus-within {
  border-color: rgba(124,92,252,0.5);
  box-shadow: 0 0 0 3px rgba(124,92,252,0.1), 0 4px 20px rgba(124,92,252,0.08);
  background: rgba(255,255,255,0.06);
}
.input-box textarea {
  flex: 1;
  background: transparent; border: none; outline: none;
  color: var(--text);
  font-size: 14px; font-family: inherit;
  resize: none;
  min-height: 24px; max-height: 120px;
  line-height: 1.6;
}
.input-box textarea::placeholder { color: var(--text-muted); }
.input-box button {
  background: var(--gradient);
  border: none; border-radius: 10px;
  padding: 10px 22px;
  color: #fff;
  font-size: 13px; font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}
.input-box button:hover { opacity: 0.85; transform: scale(1.02); }
.input-box button:disabled {
  opacity: 0.3; cursor: not-allowed; transform: none;
}

/* Quick Actions - Bento style */
.quick-actions {
  display: flex; gap: 8px;
  margin-top: 14px; flex-wrap: wrap;
}
.quick-actions button {
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 7px 14px;
  color: var(--text-dim);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.quick-actions button:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: rgba(124,92,252,0.08);
  transform: translateY(-1px);
}

/* Welcome */
.welcome {
  text-align: center;
  padding: 50px 20px;
  max-width: 520px;
  margin: 0 auto;
}
.welcome .logo-big {
  font-size: 56px; margin-bottom: 20px;
  animation: float 4s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
.welcome h2 {
  font-size: 22px; font-weight: 700;
  background: var(--gradient-text);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 10px;
}
.welcome p {
  color: var(--text-dim);
  font-size: 14px;
  line-height: 1.7;
}

/* Responsive */
@media (max-width: 768px) {
  .sidebar { display: none; }
  .messages { padding: 16px 12px; }
  .input-area { padding: 12px 14px; }
}
</style>
</head>
<body>

<div class="header">
  <div class="logo">&#128123;</div>
  <div>
    <h1>Ghost Agent</h1>
    <div class="subtitle">智能代码助手</div>
  </div>
  <div class="status"><span class="dot"></span>在线</div>
</div>

<div class="container">
  <div class="sidebar">
    <div class="sidebar-header">快捷操作</div>
    <div class="sidebar-nav">
      <div class="nav-item active" onclick="sq('write a data analysis script')">
        <span class="icon">&#128202;</span>数据分析
      </div>
      <div class="nav-item" onclick="sq('write a math calculator')">
        <span class="icon">&#128437;</span>计算器
      </div>
      <div class="nav-item" onclick="sq('write a web API server')">
        <span class="icon">&#128295;</span>API 服务器
      </div>
      <div class="nav-item" onclick="sq('write a file organizer')">
        <span class="icon">&#128193;</span>文件整理
      </div>
      <div class="nav-item" onclick="sq('write a web scraper')">
        <span class="icon">&#128268;</span>网页爬虫
      </div>
      <div class="nav-item" onclick="sq('write a number guessing game')">
        <span class="icon">&#127918;</span>小游戏
      </div>
      <div class="nav-item" onclick="sq('status')">
        <span class="icon">&#128269;</span>状态
      </div>
      <div class="nav-item" onclick="clearChat()">
        <span class="icon">&#128465;</span>清空对话
      </div>
    </div>
    <div class="sidebar-footer">Ghost Agent v3.0 | 端口 26602</div>
  </div>

  <div class="main">
    <div class="messages" id="m">
      <div class="welcome" id="welcome">
        <div class="logo-big">&#128123;</div>
        <h2>欢迎使用 Ghost Agent</h2>
        <p>我是一个 AI 驱动的代码助手，可以帮你写代码、调试错误、自动修复 Bug。在下方输入你的需求，或使用左侧快捷操作开始。</p>
      </div>
    </div>

    <div class="input-area">
      <div class="input-wrap">
        <div class="input-box">
          <textarea id="i" placeholder="输入你的需求...（回车发送，Shift+回车换行）" rows="1" onkeydown="handleKey(event)"></textarea>
          <button id="b" onclick="send()">发送</button>
        </div>
        <div class="quick-actions">
          <button onclick="sq('write a data analysis script')">数据分析</button>
          <button onclick="sq('write a math calculator')">计算器</button>
          <button onclick="sq('write a web API server')">API 服务器</button>
          <button onclick="sq('write a file organizer')">文件整理</button>
          <button onclick="sq('write a web scraper')">网页爬虫</button>
          <button onclick="sq('status')">状态</button>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
var isFirstMessage = true;
function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
}
function sq(t) { document.getElementById('i').value = t; send(); }
function clearChat() {
  document.getElementById('m').innerHTML = '<div class="welcome" id="welcome"><div class="logo-big">&#128123;</div><h2>欢迎使用 Ghost Agent</h2><p>我是一个 AI 驱动的代码助手，可以帮你写代码、调试错误、自动修复 Bug。</p></div>';
  isFirstMessage = true;
}
function send() {
  var i = document.getElementById('i');
  var t = i.value.trim();
  if (!t) return;
  i.value = '';
  document.getElementById('b').disabled = true;
  if (isFirstMessage) { var w = document.getElementById('welcome'); if (w) w.remove(); isFirstMessage = false; }
  addMsg('user', t);
  addTyping();
  fetch('/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: t})
  }).then(function(r) { return r.json(); }).then(function(d) {
    removeTyping();
    document.getElementById('b').disabled = false;
    var c = '';
    if (d.success) {
      c = '<span class="success">&#10003; 任务完成</span>';
      if (d.output) c += '<pre>' + esc(d.output) + '</pre>';
    } else {
      c = '<span class="error">&#10007; 任务失败</span>';
      if (d.error) c += '<pre>' + esc(d.error) + '</pre>';
    }
    addMsg('ghost', c);
  }).catch(function(e) {
    removeTyping();
    document.getElementById('b').disabled = false;
    addMsg('ghost', '<span class="error">错误: ' + esc(String(e)) + '</span>');
  });
}
function addMsg(type, content) {
  var m = document.getElementById('m');
  var d = document.createElement('div');
  d.className = 'message ' + type;
  var av = type === 'ghost' ? '<div class="avatar ghost">&#128123;</div>' : '<div class="avatar user">&#128100;</div>';
  var role = type === 'ghost' ? '<div class="role">Ghost Agent</div>' : '<div class="role">你</div>';
  d.innerHTML = av + '<div class="bubble ' + type + '">' + role + content + '</div>';
  m.appendChild(d);
  m.scrollTop = m.scrollHeight;
}
function addTyping() {
  var m = document.getElementById('m');
  var d = document.createElement('div');
  d.className = 'message ghost'; d.id = 'typing';
  d.innerHTML = '<div class="avatar ghost">&#128123;</div><div class="bubble ghost"><div class="role">Ghost Agent</div><div class="typing"><span></span><span></span><span></span></div></div>';
  m.appendChild(d); m.scrollTop = m.scrollHeight;
}
function removeTyping() { var t = document.getElementById('typing'); if (t) t.remove(); }
function esc(t) { var d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
document.getElementById('i').addEventListener('input', function() { this.style.height = 'auto'; this.style.height = Math.min(this.scrollHeight, 120) + 'px'; });
</script>
</body>
</html>"""


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
            self.send_json({"status": "ok", "version": "3.0", "tasks": len(a.history)})
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
                self.send_json({"success": False, "error": "请输入内容"})
                return
            if msg.lower() == "status":
                a = get_agent()
                self.send_json({"success": True, "output": "Ghost Agent v3.0\\n后端: " + a.ai.__class__.__name__ + "\\n任务数: " + str(len(a.history))})
                return
            try:
                a = get_agent()
                result = a.do(msg)
                self.send_json({"success": result["success"], "output": (result.get("output") or "")[:2000], "error": (result.get("error") or "")[:500] if not result["success"] else None})
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
    def log_message(self, *a): pass

def main():
    port = 26602
    server = HTTPServer(("0.0.0.0", port), Handler)
    print("Ghost Agent Web UI v3.0 - Awwwards Style")
    print("http://localhost:" + str(port))
    try: server.serve_forever()
    except KeyboardInterrupt: print("\\nStopped")

if __name__ == "__main__":
    main()
