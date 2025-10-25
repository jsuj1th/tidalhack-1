# hybrid_aws_agent.py
"""
Hybrid AWS Agent: Uses AWS services (DynamoDB, S3, SES) with original Gemini API
Best of both worlds: AWS scalability + Gemini AI availability
"""

from dotenv import load_dotenv
load_dotenv()  # Load environment variables first

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
    StartSessionContent,
    EndSessionContent,
)
from functions import generate_coupon_code, evaluate_story_quality
from config import USE_RANDOM_CODES, ENABLE_ANALYTICS
from ai_functions import ai_evaluate_story, ai_generate_personalized_response, ai_detect_spam_or_abuse, ai_understand_user_intent, ai_generate_dynamic_prompts
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any, Dict
from uagents import Model
import os
import json
import re

# Configuration from environment
USE_AWS_SERVICES = os.getenv("USE_AWS_SERVICES", "true").lower() == "true"
USE_BEDROCK_AI = os.getenv("USE_BEDROCK_AI", "false").lower() == "true"
USE_DYNAMODB = os.getenv("USE_DYNAMODB", "true").lower() == "true"
USE_S3_STORAGE = os.getenv("USE_S3_STORAGE", "true").lower() == "true"
USE_SES_EMAIL = os.getenv("USE_SES_EMAIL", "true").lower() == "true"
USE_GEMINI = os.getenv("USE_GEMINI", "true").lower() == "true"

USE_AI_EVALUATION = os.getenv("USE_AI_EVALUATION", "true").lower() == "true"
USE_AI_RESPONSES = os.getenv("USE_AI_RESPONSES", "true").lower() == "true"
USE_AI_MODERATION = os.getenv("USE_AI_MODERATION", "true").lower() == "true"
USE_AI_PROMPTS = os.getenv("USE_AI_PROMPTS", "true").lower() == "true"

# Initialize AWS services (optional)
dynamodb_manager = None
s3_manager = None
ses_manager = None

if USE_AWS_SERVICES:
    try:
        if USE_DYNAMODB:
            from aws_dynamodb import get_dynamodb_manager
            dynamodb_manager = get_dynamodb_manager()
            print("✅ DynamoDB initialized")
        if USE_S3_STORAGE:
            from aws_s3 import get_s3_manager
            s3_manager = get_s3_manager()
            print("✅ S3 initialized")
        if USE_SES_EMAIL:
            from aws_ses import get_ses_manager
            ses_manager = get_ses_manager()
            print("✅ SES initialized")
    except Exception as e:
        print(f"⚠️ AWS services initialization failed: {e}")
        print("Falling back to local storage")
        USE_AWS_SERVICES = False

agent = Agent(name="fetch-pizza-hybrid", seed="pizza_coupon_agent_hybrid_2024", port=8004, mailbox=True)

chat_proto = Protocol(spec=chat_protocol_spec)

# User session states
USER_STATES = {
    "INITIAL": "initial",
    "WAITING_FOR_STORY": "waiting_for_story",
    "STORY_RECEIVED": "story_received",
    "COUPON_ISSUED": "coupon_issued"
}

# Pizza-themed responses for TidalHACKS 2025
INITIAL_RESPONSES = [
    "🍕💻 Hey TidalHACKS 2025 hacker! Your code is compiling, time for a pizza break! ✨\n\nYou're out here building the future, and Fetch.ai wants to fuel your late-night debugging sessions with pizza! 🎓\n\n**Tell me YOUR pizza story!** Maybe it was:\n• That legendary 3am pizza that powered your breakthrough\n• A pizza moment that saved your hackathon project\n• An epic slice during your most intense debugging session\n• Or any other pizza tale from your coding adventures!\n\n🏆 Pro tip: Epic stories unlock bigger pizzas! Everyone gets rewarded! Let's see what pizza.execute() returns! 🚀",
    
    "🧙‍♂️🍕 Greetings, TidalHACKS 2025 code wizard! The Pizza Genie has materialized! ✨\n\nYou're casting powerful algorithms and debugging spells - Fetch.ai sees your hustle and wants to reward your magic with pizza! 💻⚡\n\n**Share YOUR greatest pizza tale!** For example:\n• Maybe it was that weird topping combo that powered an all-nighter\n• Or your most epic pizza-fueled breakthrough moment\n• Perhaps when pizza literally saved your merge conflict\n• Any perfect slice during your hackathon grind!\n\n⭐ Remember: Legendary stories earn PREMIUM pizzas, good ones get STANDARD, all stories get rewarded! Cast your best spell and unlock your pizza.reward()! 🎁"
]

def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=content,
    )

def extract_email_from_message(message: str) -> str:
    """Extract email from user_details in message content"""
    try:
        # Look for <user_details><email>...</email></user_details> pattern
        email_match = re.search(r'<user_details><email>([^<]+)</email></user_details>', message)
        if email_match:
            return email_match.group(1).strip()
        
        # Fallback: look for any email pattern in the message
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, message)
        if email_match:
            return email_match.group(0)
        
        return ""
    except Exception as e:
        print(f"Error extracting email: {e}")
        return ""

def clean_story_text(message: str) -> str:
    """Remove metadata and extract just the story part"""
    try:
        # Remove everything from [Additional Context] onwards
        if '[Additional Context]' in message:
            story = message.split('[Additional Context]')[0].strip()
        else:
            story = message
        
        # Remove any remaining XML-like tags
        story = re.sub(r'<[^>]+>', '', story)
        return story.strip()
    except Exception as e:
        print(f"Error cleaning story: {e}")
        return message

def get_user_state(ctx: Context, sender: str) -> str:
    """Get current state for user"""
    if USE_DYNAMODB and dynamodb_manager:
        return dynamodb_manager.get_user_state(sender) or USER_STATES["INITIAL"]
    else:
        # Fallback to local storage
        user_hash = sender[:8]  # Simple hash
        state = ctx.storage.get(f"state_{user_hash}")
        return state if state is not None else USER_STATES["INITIAL"]

def set_user_state(ctx: Context, sender: str, state: str):
    """Set state for user"""
    if USE_DYNAMODB and dynamodb_manager:
        dynamodb_manager.set_user_state(sender, state)
    else:
        # Fallback to local storage
        user_hash = sender[:8]
        ctx.storage.set(f"state_{user_hash}", state)

def has_user_received_coupon(ctx: Context, sender: str) -> bool:
    """Check if user already received a coupon"""
    if USE_DYNAMODB and dynamodb_manager:
        return dynamodb_manager.has_user_received_coupon(sender)
    else:
        # Fallback to local storage
        user_hash = sender[:8]
        result = ctx.storage.get(f"coupon_issued_{user_hash}")
        return result if result is not None else False

def mark_coupon_issued(ctx: Context, sender: str, coupon_code: str, tier: str, rating: int, story: str = ""):
    """Mark that user has received a coupon"""
    if USE_DYNAMODB and dynamodb_manager:
        dynamodb_manager.mark_coupon_issued(sender, coupon_code, tier, rating, story)
    else:
        # Fallback to local storage
        user_hash = sender[:8]
        ctx.storage.set(f"coupon_issued_{user_hash}", True)
        ctx.storage.set(f"coupon_code_{user_hash}", coupon_code)

def get_user_coupon(ctx: Context, sender: str) -> str:
    """Get user's existing coupon code"""
    if USE_DYNAMODB and dynamodb_manager:
        return dynamodb_manager.get_user_coupon(sender) or ""
    else:
        # Fallback to local storage
        user_hash = sender[:8]
        coupon = ctx.storage.get(f"coupon_code_{user_hash}")
        return coupon if coupon is not None else ""

def record_analytics_event(event_type: str, sender: str, data: Dict[str, Any]):
    """Record analytics event"""
    if USE_DYNAMODB and dynamodb_manager:
        user_id = sender[:16]  # Simple user ID
        dynamodb_manager.record_analytics_event(event_type, user_id, data)
    
    # Also backup to S3 if enabled
    if USE_S3_STORAGE and s3_manager:
        try:
            analytics_data = {
                "event_type": event_type,
                "user_id": sender[:16],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data
            }
            s3_manager.upload_analytics_data(analytics_data, f"events/{event_type}_{datetime.now().timestamp()}.json")
        except Exception as e:
            print(f"S3 analytics backup failed: {e}")

@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"Got a message from {sender}: {msg.content}")
    
    # Store session sender
    ctx.storage.set(str(ctx.session), sender)
    
    # Send acknowledgement
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id),
    )

    for item in msg.content:
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Got a start session message from {sender}")
            continue
        elif isinstance(item, TextContent):
            await process_user_message(ctx, sender, item.text)
        else:
            ctx.logger.info(f"Got unexpected content from {sender}")

async def process_coupon_generation(ctx: Context, sender: str, story: str, story_rating: int, original_message: str = ""):
    """Process coupon generation and send personalized response"""
    
    # Check if user already got a coupon (race condition protection)
    if has_user_received_coupon(ctx, sender):
        return
    
    try:
        # Generate coupon based on story rating
        coupon_code, coupon_tier = generate_coupon_code(sender, story_rating, USE_RANDOM_CODES)
        
        # Mark coupon as issued
        mark_coupon_issued(ctx, sender, coupon_code, coupon_tier, story_rating, story)
        set_user_state(ctx, sender, USER_STATES["COUPON_ISSUED"])
        
        # Generate response using original Gemini API
        if USE_AI_RESPONSES and USE_GEMINI:
            try:
                response = await ai_generate_personalized_response(story, story_rating, coupon_tier, coupon_code)
                ctx.logger.info(f"Generated Gemini response for {sender}")
            except Exception as e:
                ctx.logger.error(f"Gemini response generation failed: {e}")
                user_email = extract_email_from_message(original_message if original_message else story)
                response = generate_static_response(story_rating, coupon_code, coupon_tier, user_email)
        else:
            # Static response based on rating
            user_email = extract_email_from_message(original_message if original_message else story)
            response = generate_static_response(story_rating, coupon_code, coupon_tier, user_email)
        
        # Record analytics
        record_analytics_event("coupon_issued", sender, {
            "coupon_code": coupon_code,
            "tier": coupon_tier,
            "rating": story_rating,
            "story_length": len(story),
            "email": extract_email_from_message(original_message if original_message else story)
        })
        
        ctx.logger.info(f"Issued coupon {coupon_code} to {sender} with rating {story_rating}")
        await ctx.send(sender, create_text_chat(response))
        
    except Exception as e:
        ctx.logger.error(f"Error in coupon generation: {e}")
        # Fallback - issue basic coupon with static response
        coupon_code, _ = generate_coupon_code(sender, 5, USE_RANDOM_CODES)
        mark_coupon_issued(ctx, sender, coupon_code, "BASIC", 5, story)
        
        await ctx.send(
            sender,
            create_text_chat(
                f"🍕 Thanks for your story! Here's your pizza coupon!\n\n"
                f"**🎫 Your Coupon Code: {coupon_code}**\n\n"
                f"📱 Show this code to any food vendor at the conference for your free pizza! 🎉"
            )
        )

def generate_static_response(story_rating: int, coupon_code: str, coupon_tier: str, user_email: str = "") -> str:
    """Generate static response based on story rating (fallback)"""
    
    # Base response based on rating
    if story_rating >= 8:
        base_response = (
            f"🎉 WOW! That story was AMAZING! You've earned a PREMIUM coupon!\n\n"
            f"**🎫 Your Coupon Code: {coupon_code}**\n\n"
            f"🍕 This gets you a LARGE pizza with premium toppings!\n"
            f"📱 Just show this code to any food vendor at the conference\n"
            f"⭐ Story Rating: {story_rating}/10 - Storytelling Master! 🏆"
        )
    elif story_rating >= 6:
        base_response = (
            f"😊 Great story! You've earned a solid coupon!\n\n"
            f"**🎫 Your Coupon Code: {coupon_code}**\n\n"
            f"🍕 This gets you a MEDIUM pizza with your choice of toppings!\n"
            f"📱 Show this code to any food vendor at the conference\n"
            f"⭐ Story Rating: {story_rating}/10 - Well done! 👍"
        )
    else:
        base_response = (
            f"🍕 Thanks for the story! Here's your coupon!\n\n"
            f"**🎫 Your Coupon Code: {coupon_code}**\n\n"
            f"🍕 This gets you a tasty REGULAR pizza!\n"
            f"📱 Show this code to any food vendor at the conference\n"
            f"⭐ Story Rating: {story_rating}/10 - Every story deserves pizza! 🙂"
        )
    
    # Add email option if SES is enabled and email is provided
    if USE_SES_EMAIL and ses_manager and user_email:
        try:
            if ses_manager.validate_email(user_email):
                base_response += (
                    f"\n\n📧 **Email Option Available!**\n"
                    f"Want this coupon sent to {user_email}? Just reply with 'send email' and I'll deliver it to your inbox via AWS SES! 📬"
                )
        except:
            pass
    
    return base_response

async def process_user_message(ctx: Context, sender: str, message: str):
    """Process user message based on conversation state"""
    user_state = get_user_state(ctx, sender)
    
    # Extract email and clean story text
    user_email = extract_email_from_message(message)
    clean_message = clean_story_text(message)
    message_lower = clean_message.lower()
    
    ctx.logger.info(f"Processing message from {sender} in state {user_state}: {clean_message[:50]}...")
    
    # Record analytics
    record_analytics_event("request", sender, {"message_length": len(clean_message)})
    
    # Check if user already has a coupon
    if has_user_received_coupon(ctx, sender):
        existing_coupon = get_user_coupon(ctx, sender)
        
        # Check if user is requesting email delivery
        if any(phrase in message_lower for phrase in ["send email", "email me", "via email", "by email", "email it"]):
            user_email = extract_email_from_message(message)
            if USE_SES_EMAIL and ses_manager and user_email:
                try:
                    if ses_manager.validate_email(user_email):
                        # Try to send email via AWS SES
                        email_result = ses_manager.send_coupon_email(
                            user_email, 
                            existing_coupon, 
                            "STANDARD",  # Default tier
                            7,  # Default rating
                            f"Here's your TidalHACKS pizza coupon: {existing_coupon}"
                        )
                        
                        if email_result["success"]:
                            await ctx.send(
                                sender,
                                create_text_chat(
                                    f"📧 Perfect! I've sent your coupon **{existing_coupon}** to {user_email} via AWS SES!\n\n"
                                    f"Check your inbox (and spam folder) for a beautifully formatted email with all the details! 🎉\n"
                                    f"Message ID: {email_result.get('message_id', 'N/A')}"
                                )
                            )
                        else:
                            await ctx.send(
                                sender,
                                create_text_chat(
                                    f"❌ Sorry, I couldn't send the email: {email_result['message']}\n\n"
                                    f"But here's your coupon again: **{existing_coupon}** 📱"
                                )
                            )
                    else:
                        await ctx.send(
                            sender,
                            create_text_chat(
                                f"📧 I'd love to email your coupon via AWS SES, but I need a valid email address!\n\n"
                                f"Please include your email like: 'send email to john@example.com'\n\n"
                                f"Or just use your coupon: **{existing_coupon}** 📱"
                            )
                        )
                except Exception as e:
                    await ctx.send(
                        sender,
                        create_text_chat(
                            f"❌ Email service is currently unavailable.\n\n"
                            f"But here's your coupon: **{existing_coupon}** 📱"
                        )
                    )
                return
        
        await ctx.send(
            sender,
            create_text_chat(
                f"🍕 Hey there! You already got your pizza coupon: **{existing_coupon}**\n\n"
                f"Just show this code to any participating food vendor at the conference! 📱\n"
                f"💡 Want it emailed via AWS SES? Just say 'send email to your@email.com'!\n"
                f"One delicious pizza per person - enjoy your slice! 🎉"
            )
        )
        return
    
    if user_state == USER_STATES["INITIAL"]:
        # User is asking for pizza - send story prompt
        if any(word in message_lower for word in ["pizza", "coupon", "hungry", "food", "eat"]):
            if USE_AI_PROMPTS and USE_GEMINI:
                try:
                    response = await ai_generate_dynamic_prompts()
                    ctx.logger.info(f"Generated Gemini prompt: {response[:50]}...")
                except Exception as e:
                    ctx.logger.error(f"Gemini prompt generation failed: {e}")
                    import random
                    response = random.choice(INITIAL_RESPONSES)
            else:
                import random
                response = random.choice(INITIAL_RESPONSES)
            
            set_user_state(ctx, sender, USER_STATES["WAITING_FOR_STORY"])
            await ctx.send(sender, create_text_chat(response))
        else:
            # Use AI to understand user intent
            if USE_AI_EVALUATION and USE_GEMINI:
                try:
                    intent_data = await ai_understand_user_intent(message)
                    
                    if intent_data.get("wants_coupon", False):
                        response = "🍕 I can help you get a pizza coupon at TidalHACKS 2025! Just ask me for pizza! 🚀"
                    else:
                        response = "🍕 Hi there! I'm the TidalHACKS 2025 Pizza Agent powered by AWS & Fetch.ai! Say 'I want pizza' to get started! 🚀"
                except Exception as e:
                    response = "🍕 Hi there! I'm the TidalHACKS 2025 Pizza Agent powered by AWS & Fetch.ai! Say 'I want pizza' to get started! 🚀"
            else:
                response = "🍕 Hi there! I'm the TidalHACKS 2025 Pizza Agent powered by AWS & Fetch.ai! Say 'I want pizza' to get started! 🚀"
            
            await ctx.send(sender, create_text_chat(response))
    
    elif user_state == USER_STATES["WAITING_FOR_STORY"]:
        # User provided a story - evaluate it
        
        if len(clean_message.strip()) < 10:
            await ctx.send(
                sender,
                create_text_chat(
                    "🤔 That's a pretty short story! Come on, give me something more interesting!\n\n"
                    "Tell me about a pizza memory, your favorite toppings, or why you deserve free pizza! "
                    "I promise it'll be worth it! 📖✨"
                )
            )
            return
        
        # AI-powered spam detection (optional)
        if USE_AI_MODERATION and USE_GEMINI:
            try:
                is_suspicious, reason = await ai_detect_spam_or_abuse(clean_message)
                if is_suspicious:
                    ctx.logger.warning(f"Suspicious message from {sender}: {reason}")
                    await ctx.send(
                        sender,
                        create_text_chat(
                            "🤔 Hmm, that doesn't seem like a genuine pizza story. "
                            "Try sharing a real personal experience with pizza! 🍕"
                        )
                    )
                    return
            except Exception as e:
                ctx.logger.error(f"Spam detection failed: {e}")
        
        set_user_state(ctx, sender, USER_STATES["STORY_RECEIVED"])
        
        if USE_AI_EVALUATION and USE_GEMINI:
            # Use original Gemini API for story evaluation
            try:
                story_rating, explanation = await ai_evaluate_story(clean_message)
                ctx.logger.info(f"Gemini evaluated story: rating={story_rating}, explanation={explanation}")
                
                # Generate coupon immediately
                await process_coupon_generation(ctx, sender, clean_message, story_rating, message)
                
            except Exception as e:
                ctx.logger.error(f"Gemini evaluation failed: {e}")
                # Fallback to rule-based evaluation
                story_rating = evaluate_story_quality(clean_message)
                await process_coupon_generation(ctx, sender, clean_message, story_rating, message)
        else:
            # Fallback to rule-based evaluation
            story_rating = evaluate_story_quality(clean_message)
            await process_coupon_generation(ctx, sender, clean_message, story_rating, message)
    
    else:
        # Invalid state or already processed
        await ctx.send(
            sender,
            create_text_chat(
                "🍕 Something went wrong! Let's start over - just ask me for pizza again! 🔄"
            )
        )
        set_user_state(ctx, sender, USER_STATES["INITIAL"])

@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Got an acknowledgement from {sender} for {msg.acknowledged_msg_id}")

# Include protocols
agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    print("🍕 Starting Hybrid AWS + Gemini Pizza Agent...")
    print("Agent Address:", agent.address)
    
    # Show configuration
    print("🚀 Configuration:")
    print(f"  AWS Services: {'✅' if USE_AWS_SERVICES else '❌'}")
    print(f"  DynamoDB: {'✅' if dynamodb_manager else '❌'}")
    print(f"  S3 Storage: {'✅' if s3_manager else '❌'}")
    print(f"  SES Email: {'✅' if ses_manager else '❌'}")
    print(f"  Gemini API: {'✅' if USE_GEMINI else '❌'}")
    
    # Initialize AWS resources if needed
    if dynamodb_manager:
        try:
            dynamodb_manager.create_tables_if_not_exist()
        except Exception as e:
            print(f"⚠️ DynamoDB table creation failed: {e}")
    
    if s3_manager:
        try:
            s3_manager.create_bucket_if_not_exists()
        except Exception as e:
            print(f"⚠️ S3 bucket creation failed: {e}")
    
    print("\n🎯 This agent uses:")
    print("  • Original Gemini API for AI (always available)")
    print("  • AWS DynamoDB for scalable data storage")
    print("  • AWS S3 for analytics and backups")
    print("  • AWS SES for professional email delivery")
    print("  • Best of both worlds! 🌟")
    
    agent.run()