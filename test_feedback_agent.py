#!/usr/bin/env python3
"""
Test client for hackathon feedback agent using uAgents protocol
"""
import asyncio
from uagents import Agent, Context
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    TextContent,
    StartSessionContent,
    chat_protocol_spec,
)
from datetime import datetime, timezone
from uuid import uuid4

# Create test agent
test_agent = Agent(
    name="test-client",
    seed="test_client_seed_123",
    port=8002
)

# Your feedback agent address from the logs
FEEDBACK_AGENT_ADDRESS = "agent1qvgxz9dxgj98xxl487l9w2wj6w5hxpa47hreqhth6txvyzgvly43ujy7n8m"

def create_chat_message(text: str, start_session: bool = False) -> ChatMessage:
    """Create a chat message"""
    content = []
    if start_session:
        content.append(StartSessionContent(type="start-session"))
    content.append(TextContent(type="text", text=text))
    
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=content,
    )

@test_agent.on_event("startup")
async def startup(ctx: Context):
    """Test the feedback agent on startup"""
    ctx.logger.info("🚀 Starting feedback agent test...")
    
    # Wait a moment for everything to initialize
    await asyncio.sleep(2)
    
    # Test 1: Initial greeting
    ctx.logger.info("Test 1: Sending initial greeting...")
    greeting_msg = create_chat_message(
        "Hi, I want to give feedback about the hackathon", 
        start_session=True
    )
    await ctx.send(FEEDBACK_AGENT_ADDRESS, greeting_msg)
    
    # Wait and send feedback
    await asyncio.sleep(5)
    
    # Test 2: Send actual feedback
    ctx.logger.info("Test 2: Sending feedback...")
    feedback_msg = create_chat_message(
        "I'm really excited about this hackathon! I'm hoping to learn more about "
        "AI and machine learning, especially neural networks. I'd love to see some "
        "good workshops on deep learning and maybe some mentorship from industry experts. "
        "I'm also looking forward to networking with other developers and working on "
        "innovative projects that could make a real impact."
    )
    await ctx.send(FEEDBACK_AGENT_ADDRESS, feedback_msg)
    
    # Wait and test rate limiting
    await asyncio.sleep(5)
    
    # Test 3: Test rate limiting
    ctx.logger.info("Test 3: Testing additional feedback...")
    additional_msg = create_chat_message(
        "I also have some thoughts about the venue and logistics that I'd like to share."
    )
    await ctx.send(FEEDBACK_AGENT_ADDRESS, additional_msg)

@test_agent.on_message(ChatMessage)
async def handle_response(ctx: Context, sender: str, msg: ChatMessage):
    """Handle responses from the feedback agent"""
    ctx.logger.info(f"📨 Got response from {sender}:")
    for content in msg.content:
        if hasattr(content, 'text'):
            print(f"🤖 Agent Response: {content.text}")
            print("-" * 50)

if __name__ == "__main__":
    print("🧪 Testing Hackathon Feedback Agent")
    print("=" * 50)
    print(f"Feedback Agent: {FEEDBACK_AGENT_ADDRESS}")
    print(f"Test Client: {test_agent.address}")
    print("=" * 50)
    
    # Run the test
    test_agent.run()