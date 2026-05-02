# -*- coding: utf-8 -*-
"""
Ghost Chat - Terminal Chat Interface for Ghost Agent
Run this in PowerShell to chat with Ghost Agent

Usage:
    python ghost_chat.py
"""
import sys
import os
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

from ghost_v21 import GhostAgent, TemplateBackend


def main():
    print("=" * 60)
    print("Ghost Chat v1.0")
    print("Chat with Ghost Agent in terminal")
    print("Type 'quit' or 'exit' to leave")
    print("Type 'help' for commands")
    print("=" * 60)
    print()
    
    agent = GhostAgent()
    
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        
        if not user_input:
            continue
        
        cmd = user_input.lower()
        
        if cmd in ("quit", "exit", "q"):
            print("Bye!")
            break
        elif cmd == "help":
            print("Commands:")
            print("  help          - Show this help")
            print("  quit/exit     - Leave")
            print("  status        - Show agent status")
            print("  clear         - Clear history")
            print("  <anything>    - Send to Ghost Agent")
            print()
            continue
        elif cmd == "status":
            print("Agent: GhostAgent v2.1")
            print("Backend: " + agent.ai.__class__.__name__)
            print("Tasks completed: " + str(len(agent.history)))
            print()
            continue
        elif cmd == "clear":
            agent.history.clear()
            print("History cleared")
            print()
            continue
        
        # Process with Ghost Agent
        print()
        try:
            result = agent.do(user_input)
            if result["success"]:
                print("[Ghost] Task completed!")
                if result["output"]:
                    print(result["output"][:500])
            else:
                print("[Ghost] Task failed: " + str(result.get("error", "Unknown"))[:200])
        except Exception as e:
            print("[Ghost] Error: " + str(e)[:200])
        print()


if __name__ == "__main__":
    main()
