"""
Google Gemini AI Integration for Pizza Agent
Handles intent detection and dynamic message generation with robust fallback mechanisms
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Tuple, Dict
import json
import asyncio
from functools import wraps
import time

# Load environment variables
load_dotenv()

# Initialize Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    gemini_model = None

# Fallback tracking and configuration
gemini_failures = 0
max_failures_before_fallback = 3  # After 3 failures, use static for next requests
GEMINI_TIMEOUT = float(os.getenv("GEMINI_TIMEOUT", "10.0"))  # Timeout in seconds
GEMINI_RETRY_COUNT = int(os.getenv("GEMINI_RETRY_COUNT", "2"))  # Number of retries

def get_gemini_status() -> dict:
    """Get current Gemini status for monitoring"""
    global gemini_failures
    return {
        "failures": gemini_failures,
        "status": "degraded" if gemini_failures >= max_failures_before_fallback else "healthy",
        "using_fallback": gemini_failures >= max_failures_before_fallback,
        "client_available": gemini_model is not None
    }

def reset_gemini_failures():
    """Reset failure counter (useful for testing or manual recovery)"""
    global gemini_failures
    gemini_failures = 0
    print("Gemini failure counter reset")

async def gemini_understand_intent(message: str, retry_count: int = None) -> Dict:
    """
    Use Gemini to understand user intent from their message with fallback
    Returns: dict with intent, wants_coupon, topic, confidence
    """
    
    if retry_count is None:
        retry_count = GEMINI_RETRY_COUNT
    
    # Check if too many failures - skip to fallback
    global gemini_failures
    if gemini_failures >= max_failures_before_fallback:
        print(f"Skipping Gemini (too many failures: {gemini_failures}), using fallback")
        return {"intent": "request_coupon", "wants_coupon": True, "topic": "pizza", "confidence": 0.7}
    
    if not gemini_model:
        return {"intent": "unknown", "wants_coupon": False, "topic": "unclear", "confidence": 0.0}
    
    prompt = f"""
    Analyze this message from a TidalHACKS25 hackathon participant and determine their intent.
    
    Message: "{message}"
    
    Determine:
    1. Do they want a pizza coupon? (yes/no)
    2. What's their main intent? (request_coupon, greeting, question, story, other)
    3. Confidence level (0.0-1.0)
    
    Respond with ONLY a JSON object like:
    {{"wants_coupon": true, "intent": "request_coupon", "topic": "pizza", "confidence": 0.95}}
    """
    
    for attempt in range(retry_count):
        try:
            # Use asyncio to add timeout functionality
            response = await asyncio.wait_for(
                asyncio.to_thread(gemini_model.generate_content, prompt),
                timeout=GEMINI_TIMEOUT
            )
            
            result = response.text.strip()
            # Try to parse JSON
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                intent_data = json.loads(json_match.group())
                # Success - reset failure counter
                gemini_failures = max(0, gemini_failures - 1)
                return intent_data
            
        except asyncio.TimeoutError:
            print(f"Gemini intent timeout (attempt {attempt + 1}/{retry_count})")
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5)  # Brief delay before retry
        except Exception as e:
            print(f"Gemini intent detection error (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5)
    
    # All attempts failed - increment failure counter
    gemini_failures += 1
    print(f"Gemini intent detection failed after {retry_count} attempts (total failures: {gemini_failures})")
    
    # Fallback: assume they want pizza if message mentions pizza-related words
    message_lower = message.lower()
    if any(word in message_lower for word in ["pizza", "coupon", "hungry", "food"]):
        return {"intent": "request_coupon", "wants_coupon": True, "topic": "pizza", "confidence": 0.7}
    
    return {"intent": "unknown", "wants_coupon": False, "topic": "unclear", "confidence": 0.5}


async def gemini_generate_unique_prompt(retry_count: int = None) -> str:
    """
    Generate a unique, creative prompt using Gemini for TidalHACKS25 with fallback
    """
    
    if retry_count is None:
        retry_count = GEMINI_RETRY_COUNT
    
    # Check if too many failures - skip to fallback
    global gemini_failures
    if gemini_failures >= max_failures_before_fallback:
        print(f"Skipping Gemini prompt generation (too many failures: {gemini_failures}), using fallback")
        import random
        return random.choice(get_fallback_prompts())
    
    if not gemini_model:
        # Fallback to static prompts
        import random
        fallback_prompts = get_fallback_prompts()
        return random.choice(fallback_prompts)
    
    prompt = """
    Create ONE single, fun, and engaging prompt asking a TidalHACKS25 hacker to share their pizza story.
    
    Context:
    - TidalHACKS25 is a hackathon with university students from across the country
    - Fetch.ai is sponsoring and providing pizza coupons
    - Better stories get better pizza coupons (PREMIUM, STANDARD, or BASIC)
    
    Requirements:
    - Choose ONE fun hacker-themed personality (Pizza Wizard, Code Sorcerer, Debug Detective, Pizza.js Bot, etc.)
    - Use coding/programming language naturally (pizza.execute(), git commit, merge conflict, debugging, stack, deploy, etc.)
    - Acknowledge they're brilliant hackers grinding at TidalHACKS25
    - Mention Fetch.ai naturally as the pizza provider
    - CLEARLY state: "Tell me YOUR pizza story" or "Share YOUR pizza tale" at the start
    - Include 3-4 example prompts as BULLET POINTS (not separate questions) like:
      • "Maybe it was a 3am pizza that saved your project"
      • "Or that perfect slice during a breakthrough"
      (These are inspiration, not separate questions to answer!)
    - Reference specific hackathon/coding vibes (all-nighters, breakthroughs, debugging)
    - Use tech emojis (💻, 🚀, ⚡, 🔥) along with pizza emojis
    - Keep it 4-5 sentences total
    - Sound energetic and tech-focused, like talking to fellow developers
    - End with clear incentive: "Epic stories unlock bigger pizzas! Everyone gets rewarded!"
    - Make it VERY CLEAR they need to share ONE story, not answer multiple questions
    
    Return ONLY ONE prompt, not multiple examples. Be creative and vary the personality each time.
    """
    
    for attempt in range(retry_count):
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(gemini_model.generate_content, prompt),
                timeout=GEMINI_TIMEOUT
            )
            
            # Success - reset failure counter
            gemini_failures = max(0, gemini_failures - 1)
            return response.text.strip()
            
        except asyncio.TimeoutError:
            print(f"Gemini prompt timeout (attempt {attempt + 1}/{retry_count})")
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Gemini prompt generation error (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5)
    
    # All attempts failed - increment failure counter and use fallback
    gemini_failures += 1
    print(f"Gemini prompt generation failed after {retry_count} attempts (total failures: {gemini_failures})")
    import random
    fallback_prompts = get_fallback_prompts()
    return random.choice(fallback_prompts)


async def gemini_generate_response_message(story: str, rating: int, tier: str, coupon_code: str, retry_count: int = None) -> str:
    """
    Generate a unique, personalized response using Gemini with fallback
    """
    
    if retry_count is None:
        retry_count = GEMINI_RETRY_COUNT
    
    # Check if too many failures - skip to fallback
    global gemini_failures
    if gemini_failures >= max_failures_before_fallback:
        print(f"Skipping Gemini response generation (too many failures: {gemini_failures}), using static response")
        return generate_static_response(rating, coupon_code, tier)
    
    if not gemini_model:
        return generate_static_response(rating, coupon_code, tier)
    
    tier_descriptions = {
        "PREMIUM": "LARGE pizza with PREMIUM toppings",
        "STANDARD": "MEDIUM pizza with classic toppings",
        "BASIC": "PERSONAL pizza"
    }
    
    prompt = f"""
    Generate a fun, personalized response to this pizza story from a TidalHACKS25 hacker.
    
    Story: "{story}"
    Rating: {rating}/10
    Coupon Tier: {tier}
    Coupon Code: {coupon_code}
    Pizza Reward: {tier_descriptions.get(tier, "pizza")}
    
    Create a response that:
    1. Acknowledges something specific from their story (be genuine!)
    2. Shows enthusiasm appropriate to their rating (more excited for higher ratings)
    3. Clearly presents their coupon code in bold: **{coupon_code}**
    4. Explains what pizza they get
    5. Mentions they can show it at the TidalHACKS25 food booth
    6. Uses emojis and keeps it fun
    7. Keep it 3-4 sentences
    
    Match the energy to the rating:
    - 8-10: Very excited, amazed, lots of celebration
    - 6-7: Positive, friendly, encouraging
    - 1-5: Still positive, everyone deserves pizza!
    """
    
    for attempt in range(retry_count):
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(gemini_model.generate_content, prompt),
                timeout=GEMINI_TIMEOUT
            )
            
            # Success - reset failure counter
            gemini_failures = max(0, gemini_failures - 1)
            return response.text.strip()
            
        except asyncio.TimeoutError:
            print(f"Gemini response timeout (attempt {attempt + 1}/{retry_count})")
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Gemini response generation error (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5)
    
    # All attempts failed - increment failure counter and use fallback
    gemini_failures += 1
    print(f"Gemini response generation failed after {retry_count} attempts (total failures: {gemini_failures})")
    return generate_static_response(rating, coupon_code, tier)


async def gemini_evaluate_story(story: str, retry_count: int = None) -> Tuple[int, str]:
    """
    AI-powered story evaluation using Gemini API
    Returns: (rating_1_to_10, explanation)
    """
    
    if retry_count is None:
        retry_count = GEMINI_RETRY_COUNT
    
    # Check if too many failures - skip to fallback
    global gemini_failures
    if gemini_failures >= max_failures_before_fallback:
        print(f"Skipping Gemini story evaluation (too many failures: {gemini_failures}), using fallback")
        from functions import evaluate_story_quality
        fallback_rating = evaluate_story_quality(story)
        return fallback_rating, "Used fallback evaluation (Gemini unavailable)"
    
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
    
    for attempt in range(retry_count):
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(gemini_model.generate_content, prompt),
                timeout=GEMINI_TIMEOUT
            )
            
            if response and response.text:
                # Try to parse JSON response
                import re
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    rating = min(10, max(1, int(result.get('rating', 5))))
                    explanation = result.get('explanation', 'Gemini evaluation completed')
                    # Success - reset failure counter
                    gemini_failures = max(0, gemini_failures - 1)
                    return rating, explanation
            
        except asyncio.TimeoutError:
            print(f"Gemini story evaluation timeout (attempt {attempt + 1}/{retry_count})")
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Gemini story evaluation error (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5)
    
    # All attempts failed - increment failure counter and use fallback
    gemini_failures += 1
    print(f"Gemini story evaluation failed after {retry_count} attempts (total failures: {gemini_failures})")
    
    # Fallback to rule-based if Gemini fails
    from functions import evaluate_story_quality
    fallback_rating = evaluate_story_quality(story)
    return fallback_rating, "Used fallback evaluation (Gemini error)"


def generate_static_response(rating: int, coupon_code: str, tier: str) -> str:
    """Fallback static responses"""
    
    if rating >= 8:
        return (
            f"🎉 WOW! That's an absolutely INCREDIBLE pizza story! \n\n"
            f"**🎫 Your Coupon Code: {coupon_code}**\n\n"
            f"🍕 This gets you a LARGE pizza with PREMIUM toppings at TidalHACKS25!\n"
            f"📱 Show this code at the Fetch.ai food booth\n"
            f"⭐ Story Rating: {rating}/10 - Your storytelling is chef's kiss! 👨‍🍳✨"
        )
    elif rating >= 6:
        return (
            f"😊 Great pizza story! I love the details!\n\n"
            f"**🎫 Your Coupon Code: {coupon_code}**\n\n"
            f"🍕 This gets you a MEDIUM pizza with classic toppings at TidalHACKS25!\n"
            f"📱 Show this code at the Fetch.ai food booth\n"
            f"⭐ Story Rating: {rating}/10 - Solid storytelling! 👍"
        )
    else:
        return (
            f"🍕 Thanks for the story! Here's your coupon!\n\n"
            f"**🎫 Your Coupon Code: {coupon_code}**\n\n"
            f"🍕 This gets you a tasty PERSONAL pizza at TidalHACKS25!\n"
            f"📱 Show this code at the Fetch.ai food booth\n"
            f"⭐ Story Rating: {rating}/10 - Every story deserves pizza! 🙂"
        )


def get_fallback_prompts() -> list:
    """Static fallback prompts for TidalHACKS25"""
    return [
        "🍕💻 Hey TidalHACKS25 hacker! Your code is compiling, time for a pizza break! ✨\n\nYou're out here building the future, and Fetch.ai wants to fuel your late-night debugging sessions with pizza! 🎓\n\n**Tell me YOUR pizza story!** Maybe it was:\n• That legendary 3am pizza that powered your breakthrough\n• A pizza moment that saved your hackathon project\n• An epic slice during your most intense debugging session\n• Or any other pizza tale from your coding adventures!\n\n🏆 Pro tip: Epic stories unlock bigger pizzas! Everyone gets rewarded! Let's see what pizza.execute() returns! 🚀",
        
        "🧙‍♂️🍕 Greetings, TidalHACKS25 code wizard! The Pizza Genie has materialized! ✨\n\nYou're casting powerful algorithms and debugging spells - Fetch.ai sees your hustle and wants to reward your magic with pizza! 💻⚡\n\n**Share YOUR greatest pizza tale!** For example:\n• Maybe it was that weird topping combo that powered an all-nighter\n• Or your most epic pizza-fueled breakthrough moment\n• Perhaps when pizza literally saved your merge conflict\n• Any perfect slice during your hackathon grind!\n\n⭐ Remember: Legendary stories earn PREMIUM pizzas, good ones get STANDARD, all stories get rewarded! Cast your best spell and unlock your pizza.reward()! 🎁",
        
        "🚨💻 ALERT: Pizza.js has detected a hacker in need at TidalHACKS25! 🍕\n\nFetch.ai's pizza infrastructure is online and ready to deploy fuel directly to your stack! You're pushing commits and crushing bugs - you've earned this! ⚡\n\n**Git commit YOUR pizza story now!** Some ideas:\n• How pizza.fuel() powered your hackathon workflow\n• Your most memorable pizza + code moment\n• A legendary pizza deployment story\n• Or why your dev stack requires pizza dependencies!\n\n🎯 Heads up: Better stories = bigger pizzas! Show us your A-game for premium rewards! Drop your logs and deploy that story! 🚀"
    ]


# Test function
async def test_gemini_functions():
    """Test Gemini integration"""
    
    print("🧪 Testing Gemini Functions")
    print("=" * 40)
    
    # Test 1: Intent detection
    test_message = "I want pizza at TidalHACKS25"
    print(f"\n📝 Test Intent: '{test_message}'")
    intent = await gemini_understand_intent(test_message)
    print(f"Result: {intent}")
    
    # Test 2: Unique prompt generation
    print("\n✨ Test Unique Prompt Generation:")
    prompt1 = await gemini_generate_unique_prompt()
    print(f"Prompt 1: {prompt1[:100]}...")
    
    # Test 3: Response generation
    print("\n💬 Test Response Generation:")
    test_story = "Last night I coded until 3am and ordered pizza. It saved my hackathon project!"
    response = await gemini_generate_response_message(test_story, 7, "STANDARD", "TEST-123")
    print(f"Response: {response}")
    
    # Test 4: Story evaluation
    print("\n⭐ Test Story Evaluation:")
    rating, explanation = await gemini_evaluate_story(test_story)
    print(f"Rating: {rating}/10, Explanation: {explanation}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_gemini_functions())