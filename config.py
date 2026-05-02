# -*- coding: utf-8 -*-
"""
Ghost Agent v2.1 - Interactive Configuration
Run this in PowerShell to configure your AI backend
"""
import json
import os
from pathlib import Path

CONFIG_FILE = Path("ghost_agent_config.json")

def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return {"backend": "template", "openai_key": "", "ollama_host": "http://localhost:11434", "ollama_model": "codellama"}

def save_config(config):
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print("Config saved to " + str(CONFIG_FILE))

def main():
    print("=" * 50)
    print("Ghost Agent v2.1 - Configuration")
    print("=" * 50)
    print()
    print("Select AI Backend:")
    print("  1. TemplateBackend (default, no API key)")
    print("  2. LongCatBackend (LongCat model)")
    print("  3. OpenAIBackend (ChatGPT)")
    print("  4. OllamaBackend (local model)")
    print()
    
    choice = input("Enter choice (1/2/3): ").strip()
    config = load_config()
    
    if choice == "2":
        config["backend"] = "longcat"
        model = input("Model (default: longcat/LongCat-2.0-Preview): ").strip()
        if model:
            config["longcat_model"] = model
        print("LongCat backend configured!")
        
    elif choice == "3":
        config["backend"] = "openai"
        key = input("Enter OpenAI API key: ").strip()
        config["openai_key"] = key
        model = input("Model (default: gpt-4): ").strip()
        if model:
            config["openai_model"] = model
        else:
            config["openai_model"] = "gpt-4"
        print("OpenAI backend configured!")
        
    elif choice == "4":
        config["backend"] = "ollama"
        host = input("Ollama host (default: http://localhost:11434): ").strip()
        if host:
            config["ollama_host"] = host
        model = input("Model (default: codellama): ").strip()
        if model:
            config["ollama_model"] = model
        print("Ollama backend configured!")
        
    else:
        config["backend"] = "template"
        print("Template backend selected (no API key needed)")
    
    save_config(config)
    print()
    print("Usage in Python:")
    print("  from ghost_v21 import create_agent")
    print("  agent = create_agent()")
    print("  agent.do('your requirement')")

if __name__ == "__main__":
    main()
