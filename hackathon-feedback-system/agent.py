# agent.py
"""
Hackathon Feedback Collection Agent
Collects participant expectations and feedback for event improvement
"""

from dotenv import load_dotenv
load_dotenv()

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
    StartSessionContent,
    EndSessionContent,
)
from functions import (
    FeedbackRequest, 
    FeedbackResponse, 
    store_feedback,
    analyze_feedback_sentiment,
    categorize_feedback,
    get_user_feedback_count
)
from config import (
    HACKATHON_NAME,
    HACKATHON_ID,
    USE_AI_ANALYSIS,
    USE_AI_RESPONSES,
    USE_AI_SENTIMENT,
    USE_AI_CATEGORIZATION,
    MAX_REQUESTS_PER_USER,
    MIN_FEEDBACK_LENGTH,
    MAX_FEEDBACK_LENGTH,
    ENABLE_ANALYTICS
)
from ai_functions import (
    ai_analyze_feedback,
    ai_generate_response,
    ai_detect_spam,
    ai_categorize_feedback
)
from aws_services import (
    store_feedback_dynamodb,
    backup_to_s3,
    send_cloudwatch_metrics
)
from datetime import datetime, timezone
from uuid import uuid4
import hashlib
import json
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize agent
agent = Agent(
    name="hackathon-feedback", 
    seed="hackathon_feedback_seed_2024",
    port=8001,
    mailbox=True
)

chat_proto = Protocol(spec=chat_protocol_spec)

# User session states
USER_STATES = {
    "INITIAL": "initial",
    "WAITING_FOR_FEEDBACK": "waiting_for_feedback",
    "FEEDBACK_RECEIVED": "feedback_received",
    "COMPLETED": "completed"
}

# Welcome messages for hackathon participants
WELCOME_MESSAGES = [
    f"🚀 Welcome to {HACKATHON_NAME}! I'm your feedback assistant! 💡\n\n"
    f"Before the event kicks off, I'd love to hear about your expectations! This helps us make the hackathon even better. Tell me:\n\n"
    f"• What are you hoping to learn or achieve?\n"
    f"• What kind of projects excite you?\n"
    f"• Any specific workshops or mentorship you're looking for?\n"
    f"• What would make this hackathon amazing for you?\n\n"
    f"Share your thoughts - every opinion matters! 🎯",
    
    f"🎯 Hey {HACKATHON_NAME} participant! Ready to shape an awesome event? ✨\n\n"
    f"Your expectations and ideas help us create the best possible hackathon experience! I'd love to know:\n\n"
    f"• What's your main goal for this hackathon?\n"
    f"• What technologies or themes interest you most?\n"
    f"• How can we support your learning journey?\n"
    f"• Any suggestions for making networking more effective?\n\n"
    f"Drop your thoughts here - let's build something great together! 🔥",
    
    f"💭 Hi there, future {HACKATHON_NAME} innovator! 🌟\n\n"
    f"Every great hackathon starts with understanding what participants want to achieve. Help us make this event incredible by sharing:\n\n"
    f"• Your experience level and what you want to learn\n"
    f"• Types of challenges or problem domains you're excited about\n"
    f"• What kind of support would help you succeed?\n"
    f"• Ideas for improving the overall hackathon experience\n\n"
    f"Your input directly influences how we run the event! 🎪"
]

def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    """Create a chat message with text content"""
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=content,
    )

def get_user_hash(sender: str) -> str:
    """Generate consistent hash for user identification"""
    return hashlib.sha256(sender.encode()).hexdigest()[:8].upper()

def extract_email_from_message(message: str) -> str:
    """Extract email from user message if provided"""
    try:
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, message)
        return email_match.group(0) if email_match else ""
    except Exception as e:
        logger.error(f"Error extracting email: {e}")
        return ""

def clean_feedback_text(message: str) -> str:
    """Clean and normalize feedback text"""
    try:
        # Remove any XML-like tags or metadata
        cleaned = re.sub(r'<[^>]+>', '', message)
        return cleaned.strip()
    except Exception as e:
        logger.error(f"Error cleaning feedback: {e}")
        return message

def get_user_state(ctx: Context, sender: str) -> str:
    """Get current conversation state for user"""
    user_hash = get_user_hash(sender)
    state = ctx.storage.get(f"state_{user_hash}")
    return state if state is not None else USER_STATES["INITIAL"]

def set_user_state(ctx: Context, sender: str, state: str):
    """Set conversation state for user"""
    user_hash = get_user_hash(sender)
    ctx.storage.set(f"state_{user_hash}", state)

def get_feedback_count(ctx: Context, sender: str) -> int:
    """Get number of feedback submissions from user"""
    user_hash = get_user_hash(sender)
    count = ctx.storage.get(f"feedback_count_{user_hash}")
    return count if count is not None else 0

def increment_feedback_count(ctx: Context, sender: str):
    """Increment feedback count for user"""
    user_hash = get_user_hash(sender)
    current_count = get_feedback_count(ctx, sender)
    ctx.storage.set(f"feedback_count_{user_hash}", current_count + 1)

@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages"""
    ctx.logger.info(f"Got message from {sender}: {msg.content}")
    
    # Store session sender
    ctx.storage.set(str(ctx.session), sender)
    
    # Send acknowledgement
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc), 
            acknowledged_msg_id=msg.msg_id
        ),
    )

    # Process message content
    for item in msg.content:
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Started session with {sender}")
            continue
        elif isinstance(item, TextContent):
            await process_user_message(ctx, sender, item.text)
        else:
            ctx.logger.info(f"Unexpected content type from {sender}")

async def process_user_message(ctx: Context, sender: str, message: str):
    """Process user message based on conversation state"""
    user_state = get_user_state(ctx, sender)
    feedback_count = get_feedback_count(ctx, sender)
    
    # Extract email and clean message
    user_email = extract_email_from_message(message)
    clean_message = clean_feedback_text(message)
    message_lower = clean_message.lower()
    
    ctx.logger.info(f"Processing message from {sender} in state {user_state}")
    
    # Check rate limiting
    if feedback_count >= MAX_REQUESTS_PER_USER:
        await ctx.send(
            sender,
            create_text_chat(
                f"🙏 Thanks for all your feedback! You've already shared {feedback_count} responses.\n\n"
                f"We really appreciate your input for {HACKATHON_NAME}. "
                f"If you have urgent feedback, please reach out to the organizers directly! 📧"
            )
        )
        return
    
    if user_state == USER_STATES["INITIAL"]:
        # User is starting conversation - send welcome message
        if any(word in message_lower for word in ["feedback", "expectation", "hackathon", "help", "hi", "hello"]):
            import random
            welcome_msg = random.choice(WELCOME_MESSAGES)
            set_user_state(ctx, sender, USER_STATES["WAITING_FOR_FEEDBACK"])
            await ctx.send(sender, create_text_chat(welcome_msg))
        else:
            # Generic greeting
            await ctx.send(
                sender,
                create_text_chat(
                    f"👋 Hi there! I'm the {HACKATHON_NAME} feedback assistant!\n\n"
                    f"I'm here to collect your expectations and suggestions to make this hackathon amazing. "
                    f"Just say 'I want to give feedback' to get started! 🚀"
                )
            )
    
    elif user_state == USER_STATES["WAITING_FOR_FEEDBACK"]:
        # User is providing feedback
        
        # Validate feedback length
        if len(clean_message.strip()) < MIN_FEEDBACK_LENGTH:
            await ctx.send(
                sender,
                create_text_chat(
                    f"🤔 That's a bit short! Could you share a bit more detail?\n\n"
                    f"I'm looking for your thoughts on what you hope to get out of {HACKATHON_NAME}. "
                    f"Even a few sentences would be super helpful! 💭"
                )
            )
            return
        
        if len(clean_message) > MAX_FEEDBACK_LENGTH:
            await ctx.send(
                sender,
                create_text_chat(
                    f"📝 Wow, that's detailed! Could you summarize your main points in fewer words?\n\n"
                    f"I want to make sure I capture your key expectations clearly. "
                    f"Try to keep it under {MAX_FEEDBACK_LENGTH} characters. Thanks! ✂️"
                )
            )
            return
        
        # Check for spam (optional)
        if USE_AI_ANALYSIS:
            try:
                is_spam = await ai_detect_spam(clean_message)
                if is_spam:
                    await ctx.send(
                        sender,
                        create_text_chat(
                            "🤖 That doesn't seem like genuine feedback. "
                            "Please share your real thoughts about the hackathon! 🎯"
                        )
                    )
                    return
            except Exception as e:
                ctx.logger.error(f"Spam detection failed: {e}")
        
        # Process the feedback
        await process_feedback_submission(ctx, sender, clean_message, user_email, message)
    
    else:
        # User already completed or in invalid state
        await ctx.send(
            sender,
            create_text_chat(
                f"🎉 Thanks for your previous feedback! "
                f"If you have more thoughts about {HACKATHON_NAME}, feel free to share them! 💡"
            )
        )
        set_user_state(ctx, sender, USER_STATES["INITIAL"])

async def process_feedback_submission(ctx: Context, sender: str, feedback: str, email: str, original_message: str):
    """Process and store feedback submission"""
    try:
        user_hash = get_user_hash(sender)
        timestamp = datetime.now(timezone.utc)
        
        # Analyze feedback with AI
        analysis_results = {}
        
        if USE_AI_SENTIMENT:
            try:
                sentiment = await analyze_feedback_sentiment(feedback)
                analysis_results["sentiment"] = sentiment
            except Exception as e:
                ctx.logger.error(f"Sentiment analysis failed: {e}")
                analysis_results["sentiment"] = "neutral"
        
        if USE_AI_CATEGORIZATION:
            try:
                category = await ai_categorize_feedback(feedback)
                analysis_results["category"] = category
            except Exception as e:
                ctx.logger.error(f"Categorization failed: {e}")
                analysis_results["category"] = "GENERAL"
        
        # Prepare feedback data
        feedback_data = {
            "feedback_id": str(uuid4()),
            "user_hash": user_hash,
            "user_email": email,
            "feedback_text": feedback,
            "timestamp": timestamp.isoformat(),
            "hackathon_id": HACKATHON_ID,
            "analysis": analysis_results,
            "metadata": {
                "message_length": len(feedback),
                "submission_count": get_feedback_count(ctx, sender) + 1
            }
        }
        
        # Store in DynamoDB
        try:
            await store_feedback_dynamodb(feedback_data)
            ctx.logger.info(f"Stored feedback in DynamoDB for {user_hash}")
        except Exception as e:
            ctx.logger.error(f"Failed to store in DynamoDB: {e}")
            # Fallback to local storage
            await store_feedback(feedback_data)
        
        # Backup to S3 (async)
        try:
            await backup_to_s3(feedback_data)
        except Exception as e:
            ctx.logger.error(f"S3 backup failed: {e}")
        
        # Send CloudWatch metrics
        try:
            await send_cloudwatch_metrics("FeedbackSubmitted", 1, {
                "Category": analysis_results.get("category", "GENERAL"),
                "Sentiment": analysis_results.get("sentiment", "neutral")
            })
        except Exception as e:
            ctx.logger.error(f"CloudWatch metrics failed: {e}")
        
        # Update user state and count
        increment_feedback_count(ctx, sender)
        set_user_state(ctx, sender, USER_STATES["COMPLETED"])
        
        # Generate personalized response
        if USE_AI_RESPONSES:
            try:
                response = await ai_generate_response(feedback, analysis_results)
            except Exception as e:
                ctx.logger.error(f"AI response generation failed: {e}")
                response = generate_static_response(analysis_results)
        else:
            response = generate_static_response(analysis_results)
        
        await ctx.send(sender, create_text_chat(response))
        
        ctx.logger.info(f"Successfully processed feedback from {user_hash}")
        
    except Exception as e:
        ctx.logger.error(f"Error processing feedback: {e}")
        await ctx.send(
            sender,
            create_text_chat(
                f"🔧 Oops! Something went wrong while saving your feedback. "
                f"Don't worry - I've noted your input! Thanks for sharing your thoughts about {HACKATHON_NAME}! 🙏"
            )
        )

def generate_static_response(analysis_results: dict) -> str:
    """Generate static response based on analysis results"""
    sentiment = analysis_results.get("sentiment", "neutral")
    category = analysis_results.get("category", "GENERAL")
    
    base_response = f"🎉 Awesome! Thanks for sharing your expectations for {HACKATHON_NAME}!\n\n"
    
    if sentiment == "positive":
        base_response += "🌟 I can feel your excitement! Your positive energy will definitely contribute to making this hackathon amazing.\n\n"
    elif sentiment == "negative":
        base_response += "🤔 I hear your concerns, and they're really valuable for us to address. Thanks for the honest feedback!\n\n"
    else:
        base_response += "💭 Your thoughtful input helps us understand what participants are looking for.\n\n"
    
    base_response += (
        f"Your feedback has been recorded and will help the organizers improve the event. "
        f"We're working hard to make {HACKATHON_NAME} an incredible experience for everyone!\n\n"
        f"🚀 Get ready for an amazing hackathon! See you at the event!"
    )
    
    return base_response

@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle chat acknowledgements"""
    ctx.logger.info(f"Got acknowledgement from {sender} for {msg.acknowledged_msg_id}")

# Include chat protocol
agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    print(f"🚀 Starting {HACKATHON_NAME} Feedback Collection Agent...")
    print("Agent Address:", agent.address)
    agent.run()