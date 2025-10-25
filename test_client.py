#!/usr/bin/env python3
"""
Simple test client for the hackathon feedback agent
"""
import asyncio
import aiohttp
import json
from datetime import datetime, timezone
from uuid import uuid4

# Your agent's address from the logs
AGENT_ADDRESS = "agent1qvgxz9dxgj98xxl487l9w2wj6w5hxpa47hreqhth6txvyzgvly43ujy7n8m"
AGENT_URL = "http://127.0.0.1:8001"

async def send_message(session, message_text):
    """Send a chat message to the agent"""
    message = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "msg_id": str(uuid4()),
        "content": [
            {"type": "text", "text": message_text}
        ]
    }
    
    try:
        async with session.post(f"{AGENT_URL}/submit", json=message) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Message sent: {message_text[:50]}...")
                return result
            else:
                print(f"❌ Failed to send message: {response.status}")
                return None
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return None

async def test_conversation():
    """Test a full conversation flow"""
    async with aiohttp.ClientSession() as session:
        print("🚀 Testing Hackathon Feedback Agent")
        print("=" * 50)
        
        # Test 1: Initial greeting
        print("\n1. Testing initial greeting...")
        await send_message(session, "Hi, I want to give feedback")
        await asyncio.sleep(2)
        
        # Test 2: Provide feedback
        print("\n2. Testing feedback submission...")
        feedback = """I'm really excited about this hackathon! I'm hoping to learn more about 
        AI and machine learning, especially neural networks. I'd love to see some good workshops 
        on deep learning and maybe some mentorship from industry experts. I'm also looking 
        forward to networking with other developers and working on innovative projects that 
        could make a real impact."""
        
        await send_message(session, feedback)
        await asyncio.sleep(3)
        
        # Test 3: Try another feedback (rate limiting test)
        print("\n3. Testing rate limiting...")
        await send_message(session, "I have more feedback about the venue and logistics")
        await asyncio.sleep(2)
        
        print("\n✅ Test completed! Check your agent logs for responses.")

if __name__ == "__main__":
    print("Starting test client...")
    asyncio.run(test_conversation())