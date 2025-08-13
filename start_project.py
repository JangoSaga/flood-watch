#!/usr/bin/env python3
"""
Startup script for FloodML project
This script starts both the backend and frontend services.
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

# Resolve repository root (directory containing this script)
REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = (REPO_ROOT / "FloodML-master").resolve()
FRONTEND_DIR = (REPO_ROOT / "frontend" / "floodguard").resolve()


def check_backend_dependencies():
    """Check if backend dependencies are installed"""
    try:
        import flask
        import flask_cors
        import requests
        import sklearn
        return True
    except ImportError as e:
        print(f"❌ Backend dependency missing: {e}")
        print("📦 Run: pip install -r FloodML-master/requirements.txt")
        return False


def check_frontend_dependencies():
    """Check if frontend dependencies are installed"""
    if not FRONTEND_DIR.exists():
        print(f"❌ Frontend directory not found: {FRONTEND_DIR}")
        return False

    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print("❌ Frontend dependencies not installed")
        print("📦 Run: cd frontend/floodguard && npm install")
        return False

    return True


def start_backend():
    """Start the Flask backend"""
    print("🚀 Starting Flask backend...")

    # Check if .env exists
    env_path = BACKEND_DIR / ".env"
    if not env_path.exists():
        print("⚠️  .env file not found. Creating one...")
        subprocess.run([sys.executable, "setup.py"], cwd=str(BACKEND_DIR))
        print("📝 Please edit .env file and add your Visual Crossing API key")
        print("   Then restart the application")
        return None

    try:
        process = subprocess.Popen(
            [sys.executable, "app.py"],
            cwd=str(BACKEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(3)  # Wait for startup

        if process.poll() is None:
            print("✅ Backend started successfully at http://localhost:5000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Backend failed to start: {stderr.decode()}")
            return None
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return None


def start_frontend():
    """Start the Next.js frontend"""
    print("🚀 Starting Next.js frontend...")

    try:
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(FRONTEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(5)  # Wait for startup

        if process.poll() is None:
            print("✅ Frontend started successfully at http://localhost:3000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Frontend failed to start: {stderr.decode()}")
            return None
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        return None


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutting down services...")
    sys.exit(0)


def main():
    print("🌊 FloodML Project Startup")
    print("=" * 40)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Check dependencies
    print("\n1. Checking dependencies...")
    if not check_backend_dependencies():
        return

    if not check_frontend_dependencies():
        return

    print("✅ All dependencies are installed")

    # Start services
    print("\n2. Starting services...")

    backend_process = start_backend()
    if not backend_process:
        print("❌ Failed to start backend. Exiting...")
        return

    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ Failed to start frontend. Stopping backend...")
        backend_process.terminate()
        return

    print("\n🎉 Both services are running!")
    print("\n📱 Access the application:")
    print("   Frontend: http://localhost:3000")
    print("   Backend API: http://localhost:5000")
    print("\n🛑 Press Ctrl+C to stop all services")

    try:
        # Keep the script running
        while True:
            time.sleep(1)

            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process stopped unexpectedly")
                break

            if frontend_process.poll() is not None:
                print("❌ Frontend process stopped unexpectedly")
                break

    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal...")
    finally:
        # Cleanup
        print("🧹 Cleaning up processes...")
        if backend_process:
            backend_process.terminate()
            backend_process.wait()
        if frontend_process:
            frontend_process.terminate()
            frontend_process.wait()
        print("✅ All services stopped")


if __name__ == "__main__":
    main()
