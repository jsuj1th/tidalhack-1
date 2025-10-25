# aws_bedrock.py
"""
AWS Bedrock integration for AI functions
Replaces Gemini API with AWS Bedrock models
"""

import json
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Tuple, Optional, Any
import asyncio
from aws_config import get_aws_services, BEDROCK_MODEL_ID
from bedrock_models import format_request_body, parse_response, get_model_config

class BedrockAI:
    """AWS Bedrock AI integration with multi-model support"""
    
    def __init__(self, model_id: str = None):
        self.aws = get_aws_services()
        self.bedrock = self.aws.bedrock
        self.model_id = model_id or BEDROCK_MODEL_ID
        self.model_config = get_model_config(self.model_id.split('.')[-1].split('-')[0])
        
        print(f"🤖 Initialized Bedrock AI with model: {self.model_id}")
        print(f"   Provider: {self.model_config.get('provider', 'unknown')}")
        print(f"   Max tokens: {self.model_config.get('max_tokens', 'unknown')}")
    
    def switch_model(self, model_id: str):
        """Switch to a different model"""
        self.model_id = model_id
        self.model_config = get_model_config(model_id.split('.')[-1].split('-')[0])
        print(f"🔄 Switched to model: {self.model_id}")
    
    async def _invoke_model(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Invoke Bedrock model with prompt using model-specific formatting"""
        try:
            # Get model configuration
            model_config = get_model_config(self.model_id.split('.')[-1].split('-')[0])
            
            # Format request body based on model
            body = format_request_body(self.model_id, prompt, max_tokens, temperature)
            
            # Invoke model
            response = await asyncio.to_thread(
                self.bedrock.invoke_model,
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Use model-specific response parsing
            return parse_response(self.model_id, response_body)
            
        except Exception as e:
            print(f"Bedrock model invocation error: {e}")
            print(f"Model ID: {self.model_id}")
            print(f"Response body (if available): {locals().get('response_body', 'N/A')}")
            raise

    async def evaluate_story(self, story: str) -> Tuple[int, str]:
        """
        AI-powered story evaluation using AWS Bedrock
        Returns: (rating_1_to_10, explanation)
        """
        
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
            response = await self._invoke_model(prompt, max_tokens=500, temperature=0.3)
            
            # Try to parse JSON response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                rating = min(10, max(1, int(result.get('rating', 5))))
                explanation = result.get('explanation', 'Bedrock evaluation completed')
                return rating, explanation
            
            # Fallback if JSON parsing fails
            return 5, "Bedrock evaluation completed (fallback)"
            
        except Exception as e:
            print(f"Bedrock story evaluation error: {e}")
            # Fallback to rule-based evaluation
            from functions import evaluate_story_quality
            fallback_rating = evaluate_story_quality(story)
            return fallback_rating, "Used fallback evaluation (Bedrock error)"

    async def generate_personalized_response(self, story: str, rating: int, tier: str, coupon_code: str) -> str:
        """
        Generate personalized response based on user's story using Bedrock AI
        """
        
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
            response = await self._invoke_model(prompt, max_tokens=300, temperature=0.8)
            return response.strip()
            
        except Exception as e:
            print(f"Bedrock response generation error: {e}")
            # Fallback to static response
            tier_messages = {
                "PREMIUM": f"🎉 Amazing story! Your coupon: **{coupon_code}** - Gets you a LARGE premium pizza! 🏆",
                "STANDARD": f"😊 Great story! Your coupon: **{coupon_code}** - Gets you a MEDIUM pizza! 👍", 
                "BASIC": f"🍕 Thanks for sharing! Your coupon: **{coupon_code}** - Gets you a tasty pizza! 🙂"
            }
            return tier_messages.get(tier, f"Your coupon: {coupon_code}")

    async def detect_spam_or_abuse(self, message: str, user_history: list = None) -> Tuple[bool, str]:
        """
        AI-powered spam and abuse detection using Bedrock
        Returns: (is_suspicious, reason)
        """
        
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
            response = await self._invoke_model(prompt, max_tokens=200, temperature=0.2)
            
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get('suspicious', False), result.get('reason', 'Bedrock analysis')
                
        except Exception as e:
            print(f"Bedrock moderation error: {e}")
        
        # Fallback - basic check
        message_lower = message.lower()
        spam_indicators = ['buy now', 'click here', 'free money', 'http://', 'https://']
        
        for indicator in spam_indicators:
            if indicator in message_lower:
                return True, f"Contains spam indicator: {indicator}"
        
        return False, "Passed basic checks"

    async def understand_user_intent(self, message: str) -> Dict[str, Any]:
        """
        Understand what the user wants using Bedrock AI
        """
        
        prompt = f"""
        Analyze this message to understand what the user wants from a pizza coupon agent.
        
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
            response = await self._invoke_model(prompt, max_tokens=200, temperature=0.3)
            
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
                
        except Exception as e:
            print(f"Bedrock intent analysis error: {e}")
        
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

    async def generate_dynamic_prompts(self) -> str:
        """
        Generate variety in story prompts using Bedrock AI for TidalHACKS25
        """
        
        prompt = """
        Generate a fun, engaging prompt asking TidalHACKS25 hackers to share a pizza story for a coupon.
        
        Context: This is for TidalHACKS25 hackathon, where university students from across the country are building 
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
            response = await self._invoke_model(prompt, max_tokens=400, temperature=0.9)
            return response.strip()
            
        except Exception as e:
            print(f"Bedrock prompt generation error: {e}")
            
            # Fallback with TidalHACKS25 theme
            import random
            fallback_prompts = [
                "🍕 Hey TidalHACKS25 hacker! Welcome to Fetch.ai's Pizza Paradise! ✨\n\nYou're crushing code, building amazing projects, and bringing innovation from universities across the country - you definitely deserve pizza! 🎓\n\nBut first, I need to hear your most epic pizza story! Tell me about:\n• Your craziest late-night coding pizza session\n• Your dream hackathon fuel (aka pizza combo)\n• A time pizza saved your project\n• Or any pizza-related tale!\n\nThe more creative and fun your story, the better your coupon! Fetch.ai is here to fuel your innovation! 🎭🚀",
                "🍕 Greetings, TidalHACKS25 innovator! I'm the Pizza Genie! 🧞‍♂️\n\nFetch.ai sees you grinding away at this hackathon, bringing brilliant ideas from campuses nationwide! You've earned a pizza break! 🎓✨\n\nTo unlock your pizza treasures, complete the ancient ritual of... STORYTELLING! 📚\n\nShare your most legendary pizza tale:\n• The weirdest topping combo during an all-nighter\n• Your best pizza-fueled hackathon memory\n• Why hackers like you deserve free pizza\n• A pizza moment that kept you going\n\nMake it interesting - boring stories get basic coupons! 😉🚀"
            ]
            return random.choice(fallback_prompts)

# Global Bedrock AI instance
bedrock_ai = None

def get_bedrock_ai() -> BedrockAI:
    """Get or create Bedrock AI instance"""
    global bedrock_ai
    if bedrock_ai is None:
        bedrock_ai = BedrockAI()
    return bedrock_ai

# Testing functions
async def test_bedrock_functions():
    """Test Bedrock AI functions"""
    
    print("🧪 Testing AWS Bedrock AI Functions")
    print("=" * 40)
    
    try:
        ai = get_bedrock_ai()
        
        # Test story evaluation
        test_story = "I once ate pizza in Italy and it changed my life! The cheese was perfect and the crust was like heaven. I'll never forget that moment."
        
        print(f"\n📖 Test Story: '{test_story}'")
        
        # Test story evaluation
        print("\n⭐ Test Story Evaluation:")
        rating, explanation = await ai.evaluate_story(test_story)
        print(f"Rating: {rating}/10")
        print(f"Explanation: {explanation}")
        
        # Test personalized response
        print("\n💬 Test Personalized Response:")
        response = await ai.generate_personalized_response(test_story, rating, "STANDARD", "TEST-123")
        print(f"Response: {response}")
        
        # Test intent understanding
        print("\n🎯 Test Intent Understanding:")
        intent = await ai.understand_user_intent("I want pizza!")
        print(f"Intent: {intent}")
        
        # Test dynamic prompts
        print("\n✨ Test Dynamic Prompt Generation:")
        prompt = await ai.generate_dynamic_prompts()
        print(f"Prompt: {prompt[:100]}...")
        
        # Test spam detection
        print("\n🛡️ Test Spam Detection:")
        is_spam, reason = await ai.detect_spam_or_abuse("This is a genuine pizza story!")
        print(f"Is Spam: {is_spam}, Reason: {reason}")
        
        print("\n✅ All Bedrock AI functions working!")
        
    except Exception as e:
        print(f"❌ Bedrock AI test failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_bedrock_functions())