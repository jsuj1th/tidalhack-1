#!/usr/bin/env python3
"""
Launch the Pizza Intelligence Admin Dashboard
"""

import subprocess
import sys
import os

def main():
    print("🍕 Starting Pizza Intelligence Admin Dashboard...")
    print("=" * 50)
    
    # Check if streamlit is installed
    try:
        import streamlit
        print("✅ Streamlit found")
    except ImportError:
        print("❌ Streamlit not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit", "plotly"])
        print("✅ Streamlit installed")
    
    # Check if plotly is installed
    try:
        import plotly
        print("✅ Plotly found")
    except ImportError:
        print("❌ Plotly not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly"])
        print("✅ Plotly installed")
    
    # Launch the dashboard
    print("\n🚀 Launching admin dashboard...")
    print("📱 The dashboard will open in your browser")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "admin_dashboard.py",
            "--server.port", "8502",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")

if __name__ == "__main__":
    main()