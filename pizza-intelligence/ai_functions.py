# ai_functions.py
"""
AI-powered functions using Gemini API instead of static pattern matching
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Dict, Tuple, Optional
import asyncio
import json
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Initialize Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    gemini_model = None

async def ai_evaluate_story(story: str) -> Tuple[int, str]:
    """
    AI-powered story evaluation using Gemini API
    Returns: (rating_1_to_10, explanation)
    """
    
    if not gemini_model:
        from functions import evaluate_story_quality
        fallback_rating = evaluate_story_quality(story)
        return fallback_rating, "Used fallback evaluation (Gemini not configured)"
    
    prompt = f"""
    You are a fun pizza story evaluator for a conference coupon system. 
    Rate this pizza story on a scale of 1-10 based on:
    - Creativity and originality (40%)
    - Pizza relevance and enthusiasm (30%) 
    - Storytelling quality and engagement (20%)
    - Length and effort (10%)

    Story to evaluate: "{story}"

    Respond with ONLY a JSON object like this:
    {{"rating": 7, "explanation": "Great story with good details about the pizza experience. Shows real enthusiasm and has some creative elements."}}
    
    Be generous but fair - this is meant to be fun! Stories about pizza adventures, weird toppings, memorable moments, or food disasters all deserve good ratings if they show effort.
    """
    
    try:
        response = await asyncio.to_thread(gemini_model.generate_content, prompt)
        if response and response.text:
            # Try to parse JSON response
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                rating = min(10, max(1, int(result.get('rating', 5))))
                explanation = result.get('explanation', 'Gemini evaluation completed')
                return rating, explanation
        
        # Fallback to rule-based if AI fails
        from functions import evaluate_story_quality
        fallback_rating = evaluate_story_quality(story)
        return fallback_rating, "Used fallback evaluation (Gemini unavailable)"
        
    except Exception as e:
        print(f"Gemini evaluation error: {e}")
        from functions import evaluate_story_quality
        fallback_rating = evaluate_story_quality(story)
        return fallback_rating, "Used fallback evaluation (Gemini error)"

async def ai_generate_personalized_response(story: str, rating: int, tier: str, coupon_code: str) -> str:
    """
    Generate personalized response based on user's story using Gemini AI
    """
    
    if not gemini_model:
        # Fallback to static response
        tier_messages = {
            "PREMIUM": f"🎉 Amazing story! Your coupon: **{coupon_code}** - Gets you a LARGE premium pizza! 🏆",
            "STANDARD": f"😊 Great story! Your coupon: **{coupon_code}** - Gets you a MEDIUM pizza! 👍", 
            "BASIC": f"🍕 Thanks for sharing! Your coupon: **{coupon_code}** - Gets you a tasty pizza! 🙂"
        }
        return tier_messages.get(tier, f"Your coupon: {coupon_code}")
    
    prompt = f"""
    You are a fun, enthusiastic pizza agent at a tech conference. A user just shared this pizza story and earned a {tier} tier coupon.

    User's story: "{story}"
    Story rating: {rating}/10
    Coupon code: {coupon_code}
    Coupon tier: {tier}

    Write a personalized, encouraging response that:
    1. Acknowledges something specific from their story
    2. Shows enthusiasm appropriate to their rating
    3. Clearly presents their coupon code
    4. Explains what pizza they get
    5. Keeps it fun and pizza-themed (use emojis!)

    Make it feel personal and genuine, not generic. 2-4 sentences max.
    """
    
    try:
        response = await asyncio.to_thread(gemini_model.generate_content, prompt)
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print(f"Gemini response generation error: {e}")
    
    # Fallback to static response
    tier_messages = {
        "PREMIUM": f"🎉 Amazing story! Your coupon: **{coupon_code}** - Gets you a LARGE premium pizza! 🏆",
        "STANDARD": f"😊 Great story! Your coupon: **{coupon_code}** - Gets you a MEDIUM pizza! 👍", 
        "BASIC": f"🍕 Thanks for sharing! Your coupon: **{coupon_code}** - Gets you a tasty pizza! 🙂"
    }
    return tier_messages.get(tier, f"Your coupon: {coupon_code}")

async def ai_detect_spam_or_abuse(message: str, user_history: list = None) -> Tuple[bool, str]:
    """
    AI-powered spam and abuse detection using Gemini
    Returns: (is_suspicious, reason)
    """
    
    if not gemini_model:
        # Fallback - basic check
        message_lower = message.lower()
        spam_indicators = ['buy now', 'click here', 'free money', 'http://', 'https://']
        
        for indicator in spam_indicators:
            if indicator in message_lower:
                return True, f"Contains spam indicator: {indicator}"
        
        return False, "Passed basic checks"
    
    # Build context
    history_context = ""
    if user_history:
        recent_messages = user_history[-3:]  # Last 3 messages
        history_context = f"User's recent messages: {recent_messages}"
    
    prompt = f"""
    You are a content moderator for a fun pizza coupon system at a tech conference.
    
    Analyze this message for:
    - Spam or bot-like behavior
    - Inappropriate content 
    - Attempts to game the system
    - Non-pizza related requests that seem malicious
    
    Message: "{message}"
    {history_context}
    
    Respond with JSON only:
    {{"suspicious": false, "reason": "Message appears genuine and appropriate"}}
    
    Be lenient - this is a fun conference activity. Only flag obvious spam, abuse, or system gaming attempts.
    """
    
    try:
        response = await asyncio.to_thread(gemini_model.generate_content, prompt)
        if response and response.text:
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get('suspicious', False), result.get('reason', 'Gemini analysis')
    except Exception as e:
        print(f"Gemini moderation error: {e}")
    
    # Fallback - basic check
    message_lower = message.lower()
    spam_indicators = ['buy now', 'click here', 'free money', 'http://', 'https://']
    
    for indicator in spam_indicators:
        if indicator in message_lower:
            return True, f"Contains spam indicator: {indicator}"
    
    return False, "Passed basic checks"

async def ai_understand_user_intent(message: str) -> Dict[str, any]:
    """
    Understand what the user wants using Gemini AI instead of keyword matching
    """
    
    if not gemini_model:
        # Fallback - keyword matching
        message_lower = message.lower()
        pizza_keywords = ['pizza', 'coupon', 'hungry', 'food', 'eat']
        
        if any(keyword in message_lower for keyword in pizza_keywords):
            return {
                "intent": "request_pizza",
                "wants_coupon": True,
                "topic": "pizza request",
                "confidence": 0.7
            }
        
        return {
            "intent": "other",
            "wants_coupon": False,
            "topic": "unclear",
            "confidence": 0.5
        }
    
    prompt = f"""
    Analyze this message to understand what the user wants from a pizza intelligence system.
    
    Message: "{message}"
    
    Classify the intent and respond with JSON only:
    {{
        "intent": "request_pizza|ask_question|complaint|greeting|story_sharing|other",
        "wants_coupon": true/false,
        "topic": "brief description",
        "confidence": 0.95
    }}
    
    Intents:
    - request_pizza: Wants a pizza coupon
    - ask_question: Asking about how it works
    - complaint: Unhappy with something
    - greeting: Just saying hi
    - story_sharing: Telling a story (might be response to prompt)
    - other: Something else
    """
    
    try:
        response = await asyncio.to_thread(gemini_model.generate_content, prompt)
        if response and response.text:
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
    except Exception as e:
        print(f"Gemini intent analysis error: {e}")
    
    # Fallback - keyword matching
    message_lower = message.lower()
    pizza_keywords = ['pizza', 'coupon', 'hungry', 'food', 'eat']
    
    if any(keyword in message_lower for keyword in pizza_keywords):
        return {
            "intent": "request_pizza",
            "wants_coupon": True,
            "topic": "pizza request",
            "confidence": 0.7
        }
    
    return {
        "intent": "other",
        "wants_coupon": False,
        "topic": "unclear",
        "confidence": 0.5
    }

async def ai_generate_dynamic_prompts() -> str:
    """
    Generate variety in story prompts using Gemini AI for TamuHacks
    """
    
    if not gemini_model:
        # Fallback with TamuHacks theme
        import random
        fallback_prompts = [
            "🍕 Hey TamuHacks hacker! Welcome to Fetch.ai's Pizza Paradise! ✨\n\nYou're crushing code, building amazing projects, and bringing innovation from universities across the country - you definitely deserve pizza! 🎓\n\nBut first, I need to hear your most epic pizza story! Tell me about:\n• Your craziest late-night coding pizza session\n• Your dream hackathon fuel (aka pizza combo)\n• A time pizza saved your project\n• Or any pizza-related tale!\n\nThe more creative and fun your story, the better your coupon! Fetch.ai is here to fuel your innovation! 🎭🚀",
            "🍕 Greetings, TamuHacks innovator! I'm the Pizza Genie! 🧞‍♂️\n\nFetch.ai sees you grinding away at this hackathon, bringing brilliant ideas from campuses nationwide! You've earned a pizza break! 🎓✨\n\nTo unlock your pizza treasures, complete the ancient ritual of... STORYTELLING! 📚\n\nShare your most legendary pizza tale:\n• The weirdest topping combo during an all-nighter\n• Your best pizza-fueled hackathon memory\n• Why hackers like you deserve free pizza\n• A pizza moment that kept you going\n\nMake it interesting - boring stories get basic coupons! 😉🚀",
            "🍕 Pizza patrol reporting for TamuHacks duty! 🚔\n\nFetch.ai has detected elevated hunger levels among brilliant hackers from universities across the nation! You're building the future - time to fuel up! 🎓⚡\n\nBefore I issue your emergency pizza coupon, I need your pizza credentials:\n\nTell me a story about:\n• How pizza powers your coding sessions\n• The most memorable hackathon pizza moment\n• A pizza story worth sharing with fellow hackers\n• Why pizza makes innovation possible\n\nThe TamuHacks Pizza Council (powered by Fetch.ai) will review your application! 📋✨🚀"
        ]
        return random.choice(fallback_prompts)
    
    prompt = """
    Generate a fun, engaging prompt asking TamuHacks hackers to share a pizza story for a coupon.
    
    Context: This is for TamuHacks hackathon, where university students from across the country are building 
    amazing projects. Fetch.ai is the main sponsor/co-host providing pizza.
    
    Make it creative and different from typical prompts. Include:
    - Fun personality/theme (pizza genie, pizza detective, pizza time traveler, etc.)
    - Acknowledge they're brilliant hackers working hard
    - Mention Fetch.ai sponsoring/providing pizza
    - Reference hackathon vibes (coding, all-nighters, innovation)
    - Mention that better stories get better coupons
    - Use emojis and make it engaging
    - Keep it 3-4 sentences max
    
    Be creative with themes like: pizza time travel, pizza superhero, pizza scientist, hackathon pizza oracle, etc.
    """
    
    try:
        response = await asyncio.to_thread(gemini_model.generate_content, prompt)
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print(f"Gemini prompt generation error: {e}")
    
    # Fallback with TamuHacks theme
    import random
    fallback_prompts = [
        "🍕 Hey TamuHacks hacker! Welcome to Fetch.ai's Pizza Paradise! ✨\n\nYou're crushing code, building amazing projects, and bringing innovation from universities across the country - you definitely deserve pizza! 🎓\n\nBut first, I need to hear your most epic pizza story! Tell me about:\n• Your craziest late-night coding pizza session\n• Your dream hackathon fuel (aka pizza combo)\n• A time pizza saved your project\n• Or any pizza-related tale!\n\nThe more creative and fun your story, the better your coupon! Fetch.ai is here to fuel your innovation! 🎭🚀",
        "🍕 Greetings, TamuHacks innovator! I'm the Pizza Genie! 🧞‍♂️\n\nFetch.ai sees you grinding away at this hackathon, bringing brilliant ideas from campuses nationwide! You've earned a pizza break! 🎓✨\n\nTo unlock your pizza treasures, complete the ancient ritual of... STORYTELLING! 📚\n\nShare your most legendary pizza tale:\n• The weirdest topping combo during an all-nighter\n• Your best pizza-fueled hackathon memory\n• Why hackers like you deserve free pizza\n• A pizza moment that kept you going\n\nMake it interesting - boring stories get basic coupons! 😉🚀",
        "🍕 Pizza patrol reporting for TamuHacks duty! 🚔\n\nFetch.ai has detected elevated hunger levels among brilliant hackers from universities across the nation! You're building the future - time to fuel up! 🎓⚡\n\nBefore I issue your emergency pizza coupon, I need your pizza credentials:\n\nTell me a story about:\n• How pizza powers your coding sessions\n• The most memorable hackathon pizza moment\n• A pizza story worth sharing with fellow hackers\n• Why pizza makes innovation possible\n\nThe TamuHacks Pizza Council (powered by Fetch.ai) will review your application! 📋✨🚀"
    ]
    return random.choice(fallback_prompts)

# Testing functions
async def test_ai_functions():
    """Test Gemini AI functions"""
    
    print("🧪 Testing Gemini AI Functions")
    print("=" * 40)
    
    # Test story evaluation
    test_story = "I once ate pizza in Italy and it changed my life! The cheese was perfect and the crust was like heaven. I'll never forget that moment."
    
    print(f"\n📖 Test Story: '{test_story}'")
    
    # Test story evaluation
    print("\n⭐ Test Story Evaluation:")
    rating, explanation = await ai_evaluate_story(test_story)
    print(f"Rating: {rating}/10")
    print(f"Explanation: {explanation}")
    
    # Test personalized response
    print("\n💬 Test Personalized Response:")
    response = await ai_generate_personalized_response(test_story, rating, "STANDARD", "TEST-123")
    print(f"Response: {response}")
    
    # Test intent understanding
    print("\n🎯 Test Intent Understanding:")
    intent = await ai_understand_user_intent("I want pizza!")
    print(f"Intent: {intent}")
    
    # Test dynamic prompts
    print("\n✨ Test Dynamic Prompt Generation:")
    prompt = await ai_generate_dynamic_prompts()
    print(f"Prompt: {prompt[:100]}...")
    
    # Test spam detection
    print("\n🛡️ Test Spam Detection:")
    is_spam, reason = await ai_detect_spam_or_abuse("This is a genuine pizza story!")
    print(f"Is Spam: {is_spam}, Reason: {reason}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ai_functions())