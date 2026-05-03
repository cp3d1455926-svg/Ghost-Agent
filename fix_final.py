path = r"C:\Users\shenz\.openclaw\workspace\code-agent\ghost_v31.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''        try:
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

new = '''        try:
            from mem0 import MemoryClient, Memory
            
            if self.api_key:
                # Cloud mode: use mem0 platform API (MemoryClient)
                self.memory = MemoryClient(api_key=self.api_key)
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

if old in content:
    content = content.replace(old, new)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Changed to MemoryClient for cloud mode")
else:
    print("ERROR: old pattern not found")
    idx = content.find("Memory(api_key=")
    if idx >= 0:
        print("Found Memory(api_key= at index", idx)
        print(repr(content[idx-50:idx+100]))
