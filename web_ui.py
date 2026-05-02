# -*- coding: utf-8 -*-
"""
Ghost Agent Web UI v2.0 - DeepSeek Style
Port 26602
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
  --bg-primary: #0d1117;
  --bg-secondary: #161b22;
  --bg-tertiary: #21262d;
  --bg-input: #0d1117;
  --border: #30363d;
  --text-primary: #e6edf3;
  --text-secondary: #8b949e;
  --text-muted: #6e7681;
  --accent: #58a6ff;
  --accent-hover: #79c0ff;
  --green: #3fb950;
  --red: #f85149;
  --orange: #d29922;
  --purple: #bc8cff;
  --bubble-user: #238636;
  --bubble-ghost: var(--bg-secondary);
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.header {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}
.header .logo {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}
.header h1 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}
.header .subtitle {
  font-size: 12px;
  color: var(--text-muted);
}
.header .status { color: var(--green); }
.header .status {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--green);
}
.header .status .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--green);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* Sidebar + Main */
.container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Sidebar */
.sidebar {
  width: 260px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--border);
}
.sidebar-header h2 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.sidebar-nav {
  padding: 8px;
  flex: 1;
  overflow-y: auto;
}
.nav-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  transition: all 0.15s;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}
.nav-item:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}
.nav-item.active {
  background: var(--bg-tertiary);
  color: var(--accent);
}
.nav-item .icon {
  font-size: 14px;
  width: 20px;
  text-align: center;
}
.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--border);
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
}

/* Main Chat Area */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-primary);
}

/* Messages */
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  scroll-behavior: smooth;
}
.messages::-webkit-scrollbar {
  width: 6px;
}
.messages::-webkit-scrollbar-track {
  background: transparent;
}
.messages::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 3px;
}

/* Message */
.message {
  display: flex;
  gap: 16px;
  animation: fadeIn 0.3s ease;
  max-width: 800px;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.message.user {
  flex-direction: row-reverse;
}
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}
.avatar.ghost {
  background: linear-gradient(135deg, var(--accent), var(--purple));
}
.avatar.user {
  background: var(--bubble-user);
}

.bubble {
  background: var(--bubble-ghost);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 18px;
  line-height: 1.7;
  font-size: 14px;
  max-width: 700px;
  position: relative;
}
.bubble.user {
  background: var(--bubble-user);
  border-color: var(--bubble-user);
}
.bubble .role {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
  color: var(--accent);
}
.bubble.user .role {
  color: rgba(255,255,255,0.7);
}

/* Code blocks in bubbles */
.bubble pre {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px;
  overflow-x: auto;
  font-size: 13px;
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  margin: 10px 0;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}
.bubble code {
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  background: var(--bg-primary);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  border: 1px solid var(--border);
}

/* Status indicators */
.bubble .success { color: var(--green); font-weight: 600; }
.bubble .error { color: var(--red); font-weight: 600; }
.bubble .info { color: var(--accent); }

/* Thinking block */
.thinking {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 16px;
  margin: 8px 0;
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
}

/* Input Area */
.input-area {
  padding: 16px 24px 20px;
  background: var(--bg-primary);
  border-top: 1px solid var(--border);
}
.input-wrap {
  max-width: 800px;
  margin: 0 auto;
  position: relative;
}
.input-box {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 16px;
  transition: border-color 0.2s;
}
.input-box:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.15);
}
.input-box textarea {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
  resize: none;
  min-height: 24px;
  max-height: 120px;
  line-height: 1.5;
}
.input-box textarea::placeholder {
  color: var(--text-muted);
}
.input-box button {
  background: var(--accent);
  border: none;
  border-radius: 8px;
  padding: 8px 18px;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
}
.input-box button:hover {
  background: var(--accent-hover);
}
.input-box button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background: var(--bg-tertiary);
}

/* Quick Actions */
.quick-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}
.quick-actions button {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 6px 14px;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.quick-actions button:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--bg-tertiary);
}

/* Typing indicator */
.typing {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}
.typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: typing 1.4s infinite;
}
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

/* Responsive */
@media (max-width: 768px) {
  .sidebar { display: none; }
  .messages { padding: 16px; }
  .input-area { padding: 12px 16px; }
}

/* Welcome message */
.welcome {
  text-align: center;
  padding: 40px 20px;
  max-width: 500px;
  margin: 0 auto;
}
.welcome .logo-big {
  font-size: 48px;
  margin-bottom: 16px;
}
.welcome h2 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
}
.welcome p {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
}
</style>
</head>
<body>

<div class="header">
  <div class="logo">&#128123;</div>
  <div>
    <h1>Ghost Agent</h1>
    <div class="subtitle">AI-Powered Code Agent</div>
  </div>
  <div class="status"><span class="dot"></span>在线</div>
</div>

<div class="container">
  <div class="sidebar">
    <div class="sidebar-header"><h2>快捷操作</h2></div>
    <div class="sidebar-nav">
      <div class="nav-item active" onclick="sq('write a data analysis script')">
        <span class="icon">&#128202;</span> 数据分析
      </div>
      <div class="nav-item" onclick="sq('write a math calculator')">
        <span class="icon">&#128437;</span> 计算器
      </div>
      <div class="nav-item" onclick="sq('write a web API server')">
        <span class="icon">&#128295;</span> API 服务器
      </div>
      <div class="nav-item" onclick="sq('write a file organizer')">
        <span class="icon">&#128193;</span> 文件整理
      </div>
      <div class="nav-item" onclick="sq('write a web scraper')">
        <span class="icon">&#128268;</span> 网页爬虫
      </div>
      <div class="nav-item" onclick="sq('write a number guessing game')">
        <span class="icon">&#127918;</span> 小游戏
      </div>
      <div class="nav-item" onclick="sq('status')">
        <span class="icon">&#128269;</span> 状态
      </div>
      <div class="nav-item" onclick="clearChat()">
        <span class="icon">&#128465;</span> 清空对话
      </div>
    </div>
    <div class="sidebar-footer">Ghost Agent v2.1 | 端口 26602</div>
  </div>

  <div class="main">
    <div class="messages" id="m">
      <div class="welcome" id="welcome">
        <div class="logo-big">&#128123;</div>
        <h2>欢迎使用 Ghost Agent</h2>
        <p>我是一个 AI 驱动的代码助手。可以帮你写代码、调试错误、自动修复 Bug。在下方输入你的需求，或使用左侧快捷操作。</p>
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
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    send();
  }
}

function sq(t) {
  document.getElementById('i').value = t;
  send();
}

function clearChat() {
  document.getElementById('m').innerHTML = '<div class="welcome" id="welcome"><div class="logo-big">&#128123;</div><h2>Welcome to Ghost Agent</h2><p>I am an AI-powered code agent. I can write code, debug errors, and auto-fix bugs.</p></div>';
  isFirstMessage = true;
}

function send() {
  var i = document.getElementById('i');
  var t = i.value.trim();
  if (!t) return;
  i.value = '';
  document.getElementById('b').disabled = true;

  // Remove welcome message
  if (isFirstMessage) {
    var w = document.getElementById('welcome');
    if (w) w.remove();
    isFirstMessage = false;
  }

  addMsg('user', t);
  addTyping();

  fetch('/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: t})
  })
  .then(function(r) { return r.json(); })
  .then(function(d) {
    removeTyping();
    document.getElementById('b').disabled = false;
    var c = '';
    if (d.success) {
      c = '<span class="success">&#10003; 任务完成</span>';
      if (d.output) {
        c += '<pre>' + esc(d.output) + '</pre>';
      }
    } else {
      c = '<span class="error">&#10007; 任务失败</span>';
      if (d.error) {
        c += '<pre>' + esc(d.error) + '</pre>';
      }
    }
    addMsg('ghost', c);
  })
  .catch(function(e) {
    removeTyping();
    document.getElementById('b').disabled = false;
    addMsg('ghost', '<span class="error">错误: ' + esc(String(e)) + '</span>');
  });
}

function addMsg(type, content) {
  var m = document.getElementById('m');
  var d = document.createElement('div');
  d.className = 'message ' + type;
  var av = type === 'ghost'
    ? '<div class="avatar ghost">&#128123;</div>'
    : '<div class="avatar user">&#128100;</div>';
  var role = type === 'ghost'
    ? '<div class="role">Ghost Agent</div>'
    : '<div class="role">你</div>';
  d.innerHTML = av + '<div class="bubble ' + type + '">' + role + content + '</div>';
  m.appendChild(d);
  m.scrollTop = m.scrollHeight;
}

function addTyping() {
  var m = document.getElementById('m');
  var d = document.createElement('div');
  d.className = 'message ghost';
  d.id = 'typing';
  d.innerHTML = '<div class="avatar ghost">&#128123;</div><div class="bubble ghost"><div class="role">Ghost Agent</div><div class="typing"><span></span><span></span><span></span></div></div>';
  m.appendChild(d);
  m.scrollTop = m.scrollHeight;
}

function removeTyping() {
  var t = document.getElementById('typing');
  if (t) t.remove();
}

function esc(t) {
  var d = document.createElement('div');
  d.textContent = t;
  return d.innerHTML;
}

// Auto-resize textarea
document.getElementById('i').addEventListener('input', function() {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});
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
        info = "Ghost Agent v2.1\\nBackend: " + a.ai.__class__.__name__ + "\\nTasks: " + str(len(a.history))
        self.send_json({"success": True, "output": info})
        return
      try:
        a = get_agent()
        result = a.do(msg)
        self.send_json({
          "success": result["success"],
          "output": (result.get("output") or "")[:2000],
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
  print("Ghost Agent Web UI v2.0 - DeepSeek Style")
  print("URL: http://localhost:" + str(port))
  print("Press Ctrl+C to stop")
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    print("\\nStopped")


if __name__ == "__main__":
  main()
