#!/usr/bin/env python3
"""
Check the status of the Pizza Agent
"""

import requests
import json

def check_agent_status():
    """Check if the agent is running and accessible"""
    print("🔍 Checking Pizza Agent Status")
    print("=" * 40)
    
    # Check if the agent is running on port 8002
    try:
        response = requests.get("http://127.0.0.1:8002", timeout=5)
        print(f"✅ Agent is responding on port 8002")
        print(f"Status Code: {response.status_code}")
        if response.text:
            print(f"Response: {response.text[:200]}...")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to agent on port 8002")
        print("   The agent might not be running or is not accessible via HTTP")
    except requests.exceptions.Timeout:
        print("⏰ Connection timeout - agent might be busy")
    except Exception as e:
        print(f"❌ Error checking agent: {e}")
    
    print("\n📋 Agent Information:")
    print("Agent Address: agent1qdpc8rhwgz0ueqds7ceq9xll3kahtw6swxms9z4kuaw20ufpnn48sdwlt9h")
    print("Port: 8002")
    print("Protocol: uAgents framework (not HTTP web server)")
    
    print("\n🌐 Access Methods:")
    print("1. AgentVerse Inspector:")
    print("   https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A8002&address=agent1qdpc8rhwgz0ueqds7ceq9xll3kahtw6swxms9z4kuaw20ufpnn48sdwlt9h")
    print("\n2. Test Client:")
    print("   python test_client.py")
    print("\n3. Direct Agent Communication:")
    print("   Use uAgents framework to send ChatMessage objects")

if __name__ == "__main__":
    check_agent_status()