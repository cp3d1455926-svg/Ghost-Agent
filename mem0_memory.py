# -*- coding: utf-8 -*-
"""
OpenClaw Memory Enhancement with mem0
让小鬼的记忆系统支持语义搜索
"""
import os
import json
import re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent if "__file__" in dir() else Path.cwd()
CONFIG_PATH = WORKSPACE / "code-agent/ghost_agent_config.json"
MEMORY_DIR = WORKSPACE / "memory"


class OpenClawMem0:
    """OpenClaw 记忆增强：基于 mem0 的语义搜索"""

    def __init__(self):
        self._mem0_available = False
        self._client = None
        self.api_key = self._load_api_key()

    def _load_api_key(self):
        key = os.environ.get("MEM0_API_KEY", "")
        if not key and CONFIG_PATH.exists():
            try:
                config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                key = config.get("mem0_api_key", "")
            except Exception:
                pass
        return key

    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                from mem0 import MemoryClient
                self._client = MemoryClient(api_key=self.api_key)
                self._mem0_available = True
            except Exception as e:
                print("[mem0] Init failed: " + str(e)[:80])
        return self._client

    def is_available(self):
        return self.client is not None

    def remember(self, content, category="general", user_id="xiaogui"):
        """Store a memory in mem0"""
        if not self.client:
            return False
        try:
            result = self.client.add(
                [{"role": "user", "content": content}],
                user_id=user_id,
                metadata={"category": category, "source": "openclaw"},
            )
            return "event_id" in result or result.get("status") == "PENDING"
        except Exception as e:
            print("[mem0] Remember failed: " + str(e)[:80])
            return False

    def search(self, query, user_id="xiaogui", limit=5):
        """Search memories using semantic search"""
        if not self.client:
            return []
        try:
            results = self.client.search(
                query=query,
                filters={"user_id": user_id},
                limit=limit,
            )
            return [
                {
                    "content": r.get("memory", ""),
                    "score": r.get("score", 0),
                    "category": r.get("metadata", {}).get("category", ""),
                    "created_at": r.get("created_at", ""),
                }
                for r in results.get("results", [])
            ]
        except Exception as e:
            print("[mem0] Search failed: " + str(e)[:80])
            return []

    def sync_from_memory_files(self, user_id="xiaogui"):
        """Sync existing memory files to mem0 (one memory per bullet point)"""
        count = 0

        # Sync MEMORY.md
        memory_md = WORKSPACE / "MEMORY.md"
        if memory_md.exists():
            content = memory_md.read_text(encoding="utf-8")
            # Extract individual bullet points
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("- ") or line.startswith("* "):
                    memory_text = line[2:].strip()
                    if len(memory_text) > 10:
                        category = self._categorize(memory_text)
                        if self.remember(memory_text, category=category, user_id=user_id):
                            count += 1

        # Sync daily memory files
        if MEMORY_DIR.exists():
            for md_file in sorted(MEMORY_DIR.glob("*.md")):
                if md_file.name == "MEMORY.md":
                    continue
                content = md_file.read_text(encoding="utf-8")
                # Extract key events (lines with - or *)
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("- ") or line.startswith("* "):
                        memory_text = line[2:].strip()
                        if len(memory_text) > 15:
                            date_str = md_file.stem
                            if self.remember(
                                f"[{date_str}] {memory_text}",
                                category="daily_log",
                                user_id=user_id,
                            ):
                                count += 1

        return count

    def _categorize(self, text):
        """Auto-categorize a memory based on content"""
        text_lower = text.lower()
        if any(k in text_lower for k in ["jake", "用户", "名字", "年龄"]):
            return "user_info"
        if any(k in text_lower for k in ["项目", "ghost", "agent", "skill", "仓库"]):
            return "projects"
        if any(k in text_lower for k in ["小说", "创作", "公众号", "文章"]):
            return "creations"
        if any(k in text_lower for k in ["经验", "教训", "学习", "规则"]):
            return "lessons"
        if any(k in text_lower for k in ["待办", "todo", "计划"]):
            return "todos"
        return "general"


# Singleton
_mem0_instance = None

def get_mem0():
    global _mem0_instance
    if _mem0_instance is None:
        _mem0_instance = OpenClawMem0()
    return _mem0_instance
