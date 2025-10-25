"""
OpenAI LLM Integration for Pizza Agent
Handles intent detection and dynamic message generation with robust fallback mechanisms
"""

import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from typing import Tuple, Dict
import json
import asyncio
from functools import wraps

# Load environment variables
load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Fallback tracking and configuration
openai_failures = 0
max_failures_before_fallback = 3  # After 3 failures, use ASI1/static for next requests
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "8.0"))  # Timeout in seconds
OPENAI_RETRY_COUNT = int(os.getenv("OPENAI_RETRY_COUNT", "2"))  # Number of retries

def get_openai_status() -> dict:
    """Get current OpenAI status for monitoring"""
    global openai_failures
    return {
        "failures": openai_failures,
        "status": "degraded" if openai_failures >= max_failures_before_fallback else "healthy",
        "using_fallback": openai_failures >= max_failures_before_fallback,
        "client_available": openai_client is not None
    }

def reset_openai_failures():
    """Reset failure counter (useful for testing or manual recovery)"""
    global openai_failures
    openai_failures = 0
    print("OpenAI failure counter reset")

def with_fallback(fallback_func):
    """Decorator to add automatic fallback on failure"""
    @wraps(fallback_func)
    async def wrapper(*args, **kwargs):
        global openai_failures
        
        try:
            # Try OpenAI first
            result = await fallback_func(*args, **kwargs)
            # Success - reset failure counter
            openai_failures = max(0, openai_failures - 1)
            return result
        except Exception as e:
            openai_failures += 1
            print(f"OpenAI error (failure #{openai_failures}): {e}")
            
            # Return fallback response
            if fallback_func.__name__ == 'openai_understand_intent':
                return {"intent": "request_coupon", "wants_coupon": True, "topic": "pizza", "confidence": 0.7}
            else:
                # For prompts and responses, will be handled in function
                raise
    
    return wrapper

async def openai_understand_intent(message: str, retry_count: int = None) -> Dict:
    """
    Use OpenAI to understand user intent from their message with fallback
    Returns: dict with intent, wants_coupon, topic, confidence
    """
    
    if retry_count is None:
        retry_count = OPENAI_RETRY_COUNT
    
    # Check if too many failures - skip to fallback
    global openai_failures
    if openai_failures >= max_failures_before_fallback:
        print(f"Skipping OpenAI (too many failures: {openai_failures}), using fallback")
        return {"intent": "request_coupon", "wants_coupon": True, "topic": "pizza", "confidence": 0.7}
    
    if not openai_client:
        return {"intent": "unknown", "wants_coupon": False, "topic": "unclear", "confidence": 0.0}
    
    prompt = f"""
    Analyze this message from a CalHacks 12.0 hackathon participant and determine their intent.
    
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
            response = await asyncio.wait_for(
                openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an intent classifier for a pizza coupon agent at CalHacks 12.0. Respond only with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=100
                ),
                timeout=OPENAI_TIMEOUT
            )
            
            result = response.choices[0].message.content.strip()
            # Try to parse JSON
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                intent_data = json.loads(json_match.group())
                # Success - reset failure counter
                openai_failures = max(0, openai_failures - 1)
                return intent_data
            
        except asyncio.TimeoutError:
            print(f"OpenAI intent timeout (attempt {attempt + 1}/{retry_count})")
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5)  # Brief delay before retry
        except Exception as e:
            print(f"OpenAI intent detection error (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5)
    
    # All attempts failed - increment failure counter
    openai_failures += 1
    print(f"OpenAI intent detection failed after {retry_count} attempts (total failures: {openai_failures})")
    
    # Fallback: assume they want pizza if message mentions pizza-related words
    message_lower = message.lower()
    if any(word in message_lower for word in ["pizza", "coupon", "hungry", "food"]):
        return {"intent": "request_coupon", "wants_coupon": True, "topic": "pizza", "confidence": 0.7}
    
    return {"intent": "unknown", "wants_coupon": False, "topic": "unclear", "confidence": 0.5}


async def openai_generate_unique_prompt(retry_count: int = None) -> str:
    """
    Generate a unique, creative prompt using OpenAI for CalHacks 12.0 with fallback
    """
    
    if retry_count is None:
        retry_count = OPENAI_RETRY_COUNT
    
    # Check if too many failures - skip to fallback
    global openai_failures
    if openai_failures >= max_failures_before_fallback:
        print(f"Skipping OpenAI prompt generation (too many failures: {openai_failures}), using fallback")
        import random
        return random.choice(get_fallback_prompts())
    
    if not openai_client:
        # Fallback to static prompts
        import random
        fallback_prompts = get_fallback_prompts()
        return random.choice(fallback_prompts)
    
    prompt = """
    Create ONE single, fun, and engaging prompt asking a CalHacks 12.0 hacker to share their pizza story.
    
    Context:
    - CalHacks 12.0 is a hackathon with university students from across the country
    - Fetch.ai is sponsoring and providing pizza coupons
    - Better stories get better pizza coupons (PREMIUM, STANDARD, or BASIC)
    
    Requirements:
    - Choose ONE fun hacker-themed personality (Pizza Wizard, Code Sorcerer, Debug Detective, Pizza.js Bot, etc.)
    - Use coding/programming language naturally (pizza.execute(), git commit, merge conflict, debugging, stack, deploy, etc.)
    - Acknowledge they're brilliant hackers grinding at CalHacks 12.0
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
                openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a creative prompt generator for a pizza coupon bot at CalHacks 12.0. Generate ONE single fun prompt that celebrates hackers and pizza. Do not create multiple examples or numbered prompts."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,  # Balanced creativity and control
                    max_tokens=250
                ),
                timeout=OPENAI_TIMEOUT
            )
            
            # Success - reset failure counter
            openai_failures = max(0, openai_failures - 1)
            return response.choices[0].message.content.strip()
            
        except asyncio.TimeoutError:
            print(f"OpenAI prompt timeout (attempt {attempt + 1}/{retry_count})")
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"OpenAI prompt generation error (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5)
    
    # All attempts failed - increment failure counter and use fallback
    openai_failures += 1
    print(f"OpenAI prompt generation failed after {retry_count} attempts (total failures: {openai_failures})")
    import random
    fallback_prompts = get_fallback_prompts()
    return random.choice(fallback_prompts)


async def openai_generate_response_message(story: str, rating: int, tier: str, coupon_code: str, retry_count: int = None) -> str:
    """
    Generate a unique, personalized response using OpenAI with fallback
    """
    
    if retry_count is None:
        retry_count = OPENAI_RETRY_COUNT
    
    # Check if too many failures - skip to fallback
    global openai_failures
    if openai_failures >= max_failures_before_fallback:
        print(f"Skipping OpenAI response generation (too many failures: {openai_failures}), using static response")
        return generate_static_response(rating, coupon_code, tier)
    
    if not openai_client:
        return generate_static_response(rating, coupon_code, tier)
    
    tier_descriptions = {
        "PREMIUM": "LARGE pizza with PREMIUM toppings",
        "STANDARD": "MEDIUM pizza with classic toppings",
        "BASIC": "PERSONAL pizza"
    }
    
    prompt = f"""
    Generate a fun, personalized response to this pizza story from a CalHacks 12.0 hacker.
    
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
    5. Mentions they can show it at the CalHacks 12.0 food booth
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
                openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a fun, enthusiastic pizza agent at CalHacks 12.0 powered by Fetch.ai. You celebrate hackers' stories and give personalized responses."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,
                    max_tokens=250
                ),
                timeout=OPENAI_TIMEOUT
            )
            
            # Success - reset failure counter
            openai_failures = max(0, openai_failures - 1)
            return response.choices[0].message.content.strip()
            
        except asyncio.TimeoutError:
            print(f"OpenAI response timeout (attempt {attempt + 1}/{retry_count})")
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"OpenAI response generation error (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                await asyncio.sleep(0.5)
    
    # All attempts failed - increment failure counter and use fallback
    openai_failures += 1
    print(f"OpenAI response generation failed after {retry_count} attempts (total failures: {openai_failures})")
    return generate_static_response(rating, coupon_code, tier)


def generate_static_response(rating: int, coupon_code: str, tier: str) -> str:
    """Fallback static responses"""
    
    if rating >= 8:
        return (
            f"🎉 WOW! That's an absolutely INCREDIBLE pizza story! \n\n"
            f"**🎫 Your Coupon Code: {coupon_code}**\n\n"
            f"🍕 This gets you a LARGE pizza with PREMIUM toppings at CalHacks 12.0!\n"
            f"📱 Show this code at the Fetch.ai food booth\n"
            f"⭐ Story Rating: {rating}/10 - Your storytelling is chef's kiss! 👨‍🍳✨"
        )
    elif rating >= 6:
        return (
            f"😊 Great pizza story! I love the details!\n\n"
            f"**🎫 Your Coupon Code: {coupon_code}**\n\n"
            f"🍕 This gets you a MEDIUM pizza with classic toppings at CalHacks 12.0!\n"
            f"📱 Show this code at the Fetch.ai food booth\n"
            f"⭐ Story Rating: {rating}/10 - Solid storytelling! 👍"
        )
    else:
        return (
            f"🍕 Thanks for the story! Here's your coupon!\n\n"
            f"**🎫 Your Coupon Code: {coupon_code}**\n\n"
            f"🍕 This gets you a tasty PERSONAL pizza at CalHacks 12.0!\n"
            f"📱 Show this code at the Fetch.ai food booth\n"
            f"⭐ Story Rating: {rating}/10 - Every story deserves pizza! 🙂"
        )


def get_fallback_prompts() -> list:
    """Static fallback prompts for CalHacks 12.0"""
    return [
        "🍕💻 Hey CalHacks 12.0 hacker! Your code is compiling, time for a pizza break! ✨\n\nYou're out here building the future, and Fetch.ai wants to fuel your late-night debugging sessions with pizza! 🎓\n\n**Tell me YOUR pizza story!** Maybe it was:\n• That legendary 3am pizza that powered your breakthrough\n• A pizza moment that saved your hackathon project\n• An epic slice during your most intense debugging session\n• Or any other pizza tale from your coding adventures!\n\n🏆 Pro tip: Epic stories unlock bigger pizzas! Everyone gets rewarded! Let's see what pizza.execute() returns! 🚀",
        
        "🧙‍♂️🍕 Greetings, CalHacks 12.0 code wizard! The Pizza Genie has materialized! ✨\n\nYou're casting powerful algorithms and debugging spells - Fetch.ai sees your hustle and wants to reward your magic with pizza! 💻⚡\n\n**Share YOUR greatest pizza tale!** For example:\n• Maybe it was that weird topping combo that powered an all-nighter\n• Or your most epic pizza-fueled breakthrough moment\n• Perhaps when pizza literally saved your merge conflict\n• Any perfect slice during your hackathon grind!\n\n⭐ Remember: Legendary stories earn PREMIUM pizzas, good ones get STANDARD, all stories get rewarded! Cast your best spell and unlock your pizza.reward()! 🎁",
        
        "🚨💻 ALERT: Pizza.js has detected a hacker in need at CalHacks 12.0! 🍕\n\nFetch.ai's pizza infrastructure is online and ready to deploy fuel directly to your stack! You're pushing commits and crushing bugs - you've earned this! ⚡\n\n**Git commit YOUR pizza story now!** Some ideas:\n• How pizza.fuel() powered your hackathon workflow\n• Your most memorable pizza + code moment\n• A legendary pizza deployment story\n• Or why your dev stack requires pizza dependencies!\n\n🎯 Heads up: Better stories = bigger pizzas! Show us your A-game for premium rewards! Drop your logs and deploy that story! 🚀"
    ]


# Test function
async def test_openai_functions():
    """Test OpenAI integration"""
    
    print("🧪 Testing OpenAI Functions")
    print("=" * 40)
    
    # Test 1: Intent detection
    test_message = "I want pizza at CalHacks"
    print(f"\n📝 Test Intent: '{test_message}'")
    intent = await openai_understand_intent(test_message)
    print(f"Result: {intent}")
    
    # Test 2: Unique prompt generation
    print("\n✨ Test Unique Prompt Generation:")
    prompt1 = await openai_generate_unique_prompt()
    print(f"Prompt 1: {prompt1[:100]}...")
    
    # Test 3: Response generation
    print("\n💬 Test Response Generation:")
    test_story = "Last night I coded until 3am and ordered pizza. It saved my hackathon project!"
    response = await openai_generate_response_message(test_story, 7, "STANDARD", "TEST-123")
    print(f"Response: {response}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_openai_functions())
