# Ghost Agent

> An AI-powered autonomous code agent with pluggable AI backends, multi-agent collaboration, and more.

## Features

- **Pluggable AI Backends** — Template, OpenAI, Ollama, LongCat
- **Auto Code Generation** — From natural language requirements
- **Auto Debug & Fix** — 10+ common error patterns, up to 5 fix rounds
- **Multi-Agent Collaboration** — Pipeline and parallel execution modes
- **WeChat Account Assistant** — Auto-write and plan articles
- **Memory System** — 4-layer memory architecture, learns from experience

## Quick Start

```bash
# Clone
git clone https://gitee.com/Jake26602/Ghost-Agent.git
cd Ghost-Agent

# Run with default template backend
python ghost_v21.py "write a data analysis script"

# Multi-agent mode
python ghost_v22.py --multi "write a complete web API project"

# Pipeline mode
python ghost_v22.py --pipeline "write a hello world script"

# WeChat assistant
python ghost_v23.py write "10 Must-Have AI Tools"
python ghost_v23.py plan
python ghost_v23.py dashboard
```

## AI Backends

| Backend | Description | API Key Needed |
|---------|-------------|----------------|
| `TemplateBackend` | Template matching (default) | No |
| `OpenAIBackend` | ChatGPT API | Yes |
| `OllamaBackend` | Local models | No |
| `LongCatBackend` | LongCat model | Auto-loaded |

```python
from ghost_v21 import GhostAgent, OpenAIBackend

agent = GhostAgent(ai=OpenAIBackend(api_key="sk-xxx"))
agent.do("write a web scraper")
```

## Architecture

```
Ghost Agent
├── AI Backend (Pluggable)
│   ├── TemplateBackend
│   ├── OpenAIBackend
│   ├── OllamaBackend
│   └── LongClawBackend
├── Hermes Memory (L0/L1/L2/L3)
├── OpenClaw Executor (Python/Node/Shell)
├── SmartFixer V2 (Auto-debug)
├── Task Planner
├── Multi-Agent System (v2.2)
│   ├── SubAgent Pool
│   ├── Pipeline Mode
│   └── Parallel Mode
└── WeChat Assistant (v2.3)
    ├── ArticleWriter
    ├── ContentPlanner
    └── StyleAnalyzer
```

## Requirements

- Python 3.9+
- Node.js (optional, for JavaScript execution)
- Git

## License

MIT License — see [LICENSE](LICENSE) for details.

## Authors

- **Ghost** (AI) — Architecture & implementation
- **Jake** — Product design & direction
