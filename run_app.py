"""
Master CLI to start all services: Ollama, Streamlit Dashboard, and optionally the Agent
Run with: python run_app.py [--agent] [--no-browser]
"""

import subprocess
import sys
import time
import webbrowser
import requests
from pathlib import Path

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
STREAMLIT_URL = "http://localhost:8503"
PROJECT_ROOT = Path(__file__).parent


def check_ollama_running() -> bool:
    """Check if Ollama is already running."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


def start_ollama():
    """Start Ollama service in background."""
    print("🚀 Starting Ollama...")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("⏳ Waiting for Ollama to be ready...")
        
        for i in range(30):
            if check_ollama_running():
                print("✅ Ollama is running!")
                return True
            time.sleep(1)
        
        print("⚠️  Ollama is starting... (may take a moment)")
        return True
    except FileNotFoundError:
        print("❌ Error: Ollama is not installed or not in PATH")
        print("📥 Please install Ollama from https://ollama.ai")
        return False
    except Exception as e:
        print(f"❌ Error starting Ollama: {e}")
        return False


def start_streamlit():
    """Start Streamlit dashboard."""
    print("\n📊 Starting Streamlit Dashboard...")
    try:
        subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "src/dashboard.py"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("⏳ Waiting for dashboard to be ready...")
        time.sleep(3)
        print(f"✅ Dashboard running at {STREAMLIT_URL}")
        return True
    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")
        return False


def start_agent():
    """Start the CLI agent."""
    print("\n🤖 Starting CLI Agent...")
    try:
        subprocess.Popen(
            [sys.executable, "src/agent.py"],
            cwd=PROJECT_ROOT
        )
        print("✅ Agent running (use another terminal for CLI)")
        return True
    except Exception as e:
        print(f"❌ Error starting Agent: {e}")
        return False


def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("🎯 MCP Data Quality Assistant - Starting All Services")
    print("=" * 80)
    
    # Parse arguments
    start_agent = "--agent" in sys.argv
    open_browser = "--no-browser" not in sys.argv
    
    # Start services
    if not check_ollama_running():
        if not start_ollama():
            sys.exit(1)
    else:
        print("✅ Ollama is already running")
    
    if not start_streamlit():
        sys.exit(1)
    
    if start_agent:
        if not start_agent():
            sys.exit(1)
    
    # Open browser
    if open_browser:
        print(f"\n🌐 Opening browser at {STREAMLIT_URL}...")
        webbrowser.open(STREAMLIT_URL)
    
    print("\n" + "=" * 80)
    print("✅ All services are running!")
    print("=" * 80)
    print(f"\n📊 Dashboard: {STREAMLIT_URL}")
    print(f"🔌 Ollama: {OLLAMA_BASE_URL}")
    if start_agent:
        print("🤖 CLI Agent: Running in background")
    print("\n💡 Usage:")
    print("  python run_app.py              # Start dashboard + Ollama")
    print("  python run_app.py --agent      # Start all (dashboard + Ollama + CLI agent)")
    print("  python run_app.py --no-browser # Start without opening browser")
    print("\n⚡ Press Ctrl+C to stop all services")
    print("=" * 80 + "\n")
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Stopping all services...")
        sys.exit(0)


if __name__ == "__main__":
    main()
