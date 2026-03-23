#!/usr/bin/env python3
"""
GigBridge Server Startup Script
Starts the Flask server for the CLI application
"""

import subprocess
import sys
import time
import requests
from threading import Thread

def check_server():
    """Check if server is running"""
    try:
        response = requests.get("http://127.0.0.1:5000/freelancers/1", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_flask_server():
    """Start Flask server in background"""
    print("🚀 Starting GigBridge Flask Server...")
    print("📍 Server will be available at: http://127.0.0.1:5000")
    print("⏳ Please wait...")
    
    try:
        # Start Flask server
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    """Main function"""
    print("=" * 50)
    print("🌉 GIGBRIDGE SERVER STARTUP")
    print("=" * 50)
    
    # Check if server is already running
    if check_server():
        print("✅ Server is already running!")
        print("🌐 You can now run: python cli_test.py")
        return
    
    # Start the server
    print("🔧 Starting Flask server...")
    try:
        start_flask_server()
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Make sure port 5000 is not in use")
        print("2. Check if app.py exists in current directory")
        print("3. Verify Python dependencies are installed")

if __name__ == "__main__":
    main()
