#!/usr/bin/env python3
"""
Simple test client to interact with the Pizza Agent
"""

import asyncio
from uagents import Agent, Context
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    TextContent,
    StartSessionContent,
)
from datetime import datetime, timezone
from uuid import uuid4

# Create a test client agent
client = Agent(name="pizza-tester", seed="test_client_seed", port=8003)

# Pizza agent address (from the running agent)
PIZZA_AGENT_ADDRESS = "agent1qdpc8rhwgz0ueqds7ceq9xll3kahtw6swxms9z4kuaw20ufpnn48sdwlt9h"

def create_chat_message(text: str, start_session: bool = False) -> ChatMessage:
    """Create a chat message"""
    content = [TextContent(type="text", text=text)]
    if start_session:
        content.insert(0, StartSessionContent(type="start-session"))
    
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=content,
    )

@client.on_event("startup")
async def startup(ctx: Context):
    """Send test messages to the pizza agent"""
    print("🧪 Starting Pizza Agent Test Client")
    print(f"Client Address: {client.address}")
    print(f"Pizza Agent Address: {PIZZA_AGENT_ADDRESS}")
    print("-" * 50)
    
    # Wait a moment for the agent to be ready
    await asyncio.sleep(2)
    
    # Test 1: Initial greeting
    print("📤 Test 1: Sending initial greeting...")
    greeting = create_chat_message("Hello! I want pizza!", start_session=True)
    await ctx.send(PIZZA_AGENT_ADDRESS, greeting)
    
    # Wait for response
    await asyncio.sleep(3)
    
    # Test 2: Pizza story
    print("📤 Test 2: Sending pizza story...")
    story = create_chat_message(
        "I once had the most amazing pizza during a hackathon! I was coding until 3am "
        "and getting really tired. Then my teammate ordered this incredible pepperoni pizza "
        "with extra cheese. The moment I took a bite, I got a burst of energy and solved "
        "the bug I'd been working on for hours! That pizza literally saved our project "
        "and we ended up winning second place. Best pizza ever! 🍕"
    )
    await ctx.send(PIZZA_AGENT_ADDRESS, story)
    
    print("✅ Test messages sent! Check the pizza agent logs for responses.")
    print("💡 You can also check the AgentVerse inspector for real-time interaction.")

@client.on_message(ChatMessage)
async def handle_response(ctx: Context, sender: str, msg: ChatMessage):
    """Handle responses from the pizza agent"""
    print(f"\n📥 Response from Pizza Agent:")
    print(f"Sender: {sender}")
    for content in msg.content:
        if hasattr(content, 'text'):
            print(f"Message: {content.text}")
    print("-" * 50)

if __name__ == "__main__":
    print("🍕 Pizza Agent Test Client")
    print("This will send test messages to your pizza agent.")
    print("Make sure the pizza agent is running first!")
    print()
    
    try:
        client.run()
    except KeyboardInterrupt:
        print("\n👋 Test client stopped.")