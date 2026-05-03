<div align="center">

# 👻 Ghost Agent

> *"Ghost Agent = OpenClaw执行力 + Hermes记忆 + ClaudeCode编码"*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![mem0](https://img.shields.io/badge/Memory-mem0-8A2BE2.svg)](https://mem0.ai)

<br>

全能型 AI Agent 框架：自动写代码、自动调试、记忆一切。<br>
基于 mem0 语义搜索记忆系统，支持多 Agent 协作、公众号运营、Electron 桌面应用。

<br>

[快速开始](#快速开始) · [功能特性](#功能特性) · [安装](#安装) · [文档](#文档)

</div>

---

## ✨ 功能特性

### 🧠 记忆系统（mem0 驱动）
- **语义搜索** — 用自然语言搜索记忆，不用精确匹配
- **自动提取** — 从对话中自动提取和存储记忆
- **云端同步** — 基于 mem0 平台，跨会话持久化
- **自动降级** — 无网络时自动切换本地 JSON 存储

### 🤖 代码生成 + 自动调试
- **模板匹配** — 内置 10+ 代码模板（数据分析、API服务器、爬虫、游戏等）
- **AI 生成** — 支持 Stepfun / LongCat / OpenAI / Ollama 多种后端
- **自动修复** — 运行出错自动分析并修复（最多 5 轮）
- **多语言** — Python / JavaScript / Shell

### 👥 多 Agent 协作
- **流水线模式** — Coder → Tester → Reviewer 串行执行
- **并行模式** — 多个 Agent 同时执行不同任务
- **任务拆分** — 自动将大任务拆分为子任务

### 📱 公众号运营
- **自动写文章** — List / Tutorial / Story 三种类型
- **内容规划** — 一周内容自动规划
- **风格分析** — 分析并模仿特定写作风格

### 🖥️ 桌面应用（Electron）
- **Web UI** — Awwwards 2026 风格界面
- **Electron 打包** — 支持 NSIS 安装包和便携版

---

## 🚀 快速开始

### 1. 安装

```bash
git clone https://github.com/cp3d1455926-svg/Ghost-Agent.git
cd Ghost-Agent
pip install -r requirements.txt
```

### 2. 配置 AI 后端（可选）

编辑 `ghost_agent_config.json`：

```json
{
  "backend": "stepfun",
  "stepfun_model": "step-3.5-flash",
  "stepfun_base_url": "https://api.stepfun.com/v1",
  "stepfun_api_key": "your-api-key",
  "mem0_api_key": "your-mem0-key"
}
```

### 3. 运行

```bash
# 运行测试
python ghost_v31.py --test

# 执行任务
python ghost_v31.py "write a data analysis script"

# 启动 Web UI
python web_ui.py
# 然后打开 http://localhost:26602
```

---

## 📦 项目结构

```
Ghost-Agent/
├── ghost_v31.py              # v3.1 主程序（mem0记忆 + 可插拔AI）
├── ghost_v30.py              # v3.0（memU记忆）
├── ghost_v23.py              # v2.3（公众号助手）
├── ghost_v22.py              # v2.2（多Agent协作）
├── ghost_v21.py              # v2.1（可插拔AI后端）
├── web_ui.py                 # Web UI（端口26602）
├── ghost_agent_config.json   # AI后端配置
├── electron/                 # Electron桌面应用框架
│   ├── main.js
│   ├── preload.js
│   └── package.json
├── LICENSE
└── README.md
```

---

## 🧠 记忆系统

Ghost Agent 的记忆系统基于 mem0，支持：

```python
from ghost_v31 import create_agent

agent = create_agent()

# 自动记忆
agent.remember("Jake likes Python and AI", category="user_info")

# 语义搜索
results = agent.memory.recall_relevant("What does Jake like?")
# → [{"content": "Jake likes Python and AI", "score": 0.95}]

# 上下文摘要（自动注入到 LLM prompt）
summary = agent.memory.get_context_summary()
```

---

## 🔧 AI 后端

支持多种 AI 后端，可热切换：

| 后端 | 配置 | 说明 |
|------|------|------|
| Stepfun | `backend: "stepfun"` | 默认，step-3.5-flash |
| LongCat | `backend: "longcat"` | LongCat-2.0-Preview |
| OpenAI | `backend: "openai"` | GPT-4 / GPT-4o-mini |
| Ollama | `backend: "ollama"` | 本地模型 |
| Template | `backend: "template"` | 无需 API key |

---

## 🖥️ 桌面应用打包

```bash
cd electron
npm install
npm run build
# 输出: dist/GhostAgent-Setup-3.1.0.exe
```

---

## 📄 License

MIT License — 自由使用、修改、分发。

---

<div align="center">

**Ghost Agent** — 全能型 AI Agent 框架 👻

*Built by [Jake](https://github.com/cp3d1455926-svg) & 小鬼*

</div>
