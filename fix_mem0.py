import re

path = r"C:\Users\shenz\.openclaw\workspace\code-agent\ghost_v31.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old_init = '''    def __init__(self, user_id="ghost_agent", agent_id="main", use_local=True):
        self.user_id = user_id
        self.agent_id = agent_id
        self._mem0_available = False
        self._fallback = {}
        
        try:
            from mem0 import Memory
            if use_local:
                # Local mode: uses Qdrant (embedded) + local LLM for extraction
                config = {
                    "vector_store": {
                        "provider": "qdrant",
                        "config": {
                            "host": "localhost",
                            "port": 6333,
                            "path": str(MEMORY_DIR / "qdrant"),
                        }
                    },
                    "llm": {
                        "provider": "ollama",
                        "config": {
                            "model": "llama3",
                            "ollama_base_url": "http://localhost:11434",
                        }
                    },
                    "embedder": {
                        "provider": "ollama",
                        "config": {
                            "model": "nomic-embed-text",
                            "ollama_base_url": "http://localhost:11434",
                        }
                    },
                }
                # Simplified config - use default Memory() which auto-configures
                self.memory = Memory()
            else:
                self.memory = Memory()
            self._mem0_available = True
            print("[mem0] Initialized successfully")
        except ImportError:
            print("[mem0] Not installed, using JSON fallback")
        except Exception as e:
            print("[mem0] Init failed: " + str(e)[:80] + ", using JSON fallback")'''

new_init = '''    def __init__(self, user_id="ghost_agent", agent_id="main", api_key=None):
        self.user_id = user_id
        self.agent_id = agent_id
        self._mem0_available = False
        self._fallback = {}
        
        # Read API key from parameter, then environment variable
        self.api_key = api_key or os.environ.get("MEM0_API_KEY", "")
        
        try:
            from mem0 import Memory
            
            if self.api_key:
                # Cloud mode: use mem0 platform API (handles vector storage + LLM + embeddings)
                self.memory = Memory(api_key=self.api_key)
                self._mem0_available = True
                print("[mem0] Cloud mode initialized (API key: " + self.api_key[:8] + "...)")
            else:
                # Local mode: try local Qdrant + Ollama
                try:
                    self.memory = Memory()
                    self._mem0_available = True
                    print("[mem0] Local mode initialized")
                except Exception as e:
                    print("[mem0] Local init failed: " + str(e)[:80])
                    print("[mem0] Set MEM0_API_KEY env var for cloud mode")
            
        except ImportError:
            print("[mem0] Not installed, using JSON fallback. Run: pip install mem0ai")
        except Exception as e:
            print("[mem0] Init failed: " + str(e)[:80] + ", using JSON fallback")'''

if old_init in content:
    content = content.replace(old_init, new_init)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Mem0Memory.__init__ updated to read MEM0_API_KEY from env var")
else:
    print("ERROR: Could not find old_init pattern")
    # Print a snippet to debug
    idx = content.find("def __init__(self, user_id=")
    if idx >= 0:
        print("Found __init__ at index", idx)
        print(repr(content[idx:idx+100]))
