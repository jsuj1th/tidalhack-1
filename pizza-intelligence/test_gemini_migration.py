#!/usr/bin/env python3
"""
Test script to verify Gemini API migration is working correctly
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment_setup():
    """Test that environment is properly configured"""
    print("🔧 Testing Environment Setup...")
    
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key and gemini_key != "your_gemini_api_key_here":
        print("✅ GEMINI_API_KEY is configured")
        return True
    else:
        print("❌ GEMINI_API_KEY is not configured")
        print("   Please set your Gemini API key in .env file")
        return False

def test_imports():
    """Test that all required modules can be imported"""
    print("\n📦 Testing Imports...")
    
    try:
        import google.generativeai as genai
        print("✅ google-generativeai imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import google-generativeai: {e}")
        return False
    
    try:
        from gemini_functions import (
            gemini_understand_intent,
            gemini_generate_unique_prompt,
            gemini_generate_response_message,
            gemini_evaluate_story
        )
        print("✅ gemini_functions imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import gemini_functions: {e}")
        return False
    
    try:
        from ai_functions import (
            ai_evaluate_story,
            ai_generate_personalized_response,
            ai_understand_user_intent,
            ai_generate_dynamic_prompts
        )
        print("✅ ai_functions imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ai_functions: {e}")
        return False
    
    try:
        from config import USE_GEMINI, GEMINI_MODEL
        print("✅ config imported successfully")
        print(f"   USE_GEMINI: {USE_GEMINI}")
        print(f"   GEMINI_MODEL: {GEMINI_MODEL}")
    except ImportError as e:
        print(f"❌ Failed to import config: {e}")
        return False
    
    return True

async def test_gemini_functions():
    """Test Gemini functions with sample data"""
    print("\n🤖 Testing Gemini Functions...")
    
    try:
        from gemini_functions import (
            gemini_understand_intent,
            gemini_generate_unique_prompt,
            gemini_evaluate_story,
            get_gemini_status
        )
        
        # Check Gemini status
        status = get_gemini_status()
        print(f"   Gemini Status: {status}")
        
        if not status['client_available']:
            print("⚠️  Gemini client not available - testing fallback behavior")
        
        # Test intent understanding
        print("   Testing intent understanding...")
        intent = await gemini_understand_intent("I want pizza!")
        print(f"   Intent result: {intent}")
        
        # Test story evaluation
        print("   Testing story evaluation...")
        test_story = "I had amazing pizza during my last hackathon. It kept me coding all night!"
        rating, explanation = await gemini_evaluate_story(test_story)
        print(f"   Story rating: {rating}/10")
        print(f"   Explanation: {explanation[:100]}...")
        
        # Test prompt generation
        print("   Testing prompt generation...")
        prompt = await gemini_generate_unique_prompt()
        print(f"   Generated prompt: {prompt[:100]}...")
        
        print("✅ Gemini functions test completed")
        return True
        
    except Exception as e:
        print(f"❌ Gemini functions test failed: {e}")
        return False

async def test_ai_functions():
    """Test updated AI functions"""
    print("\n🧠 Testing AI Functions...")
    
    try:
        from ai_functions import (
            ai_evaluate_story,
            ai_generate_personalized_response,
            ai_understand_user_intent,
            ai_generate_dynamic_prompts
        )
        
        # Test story evaluation
        print("   Testing AI story evaluation...")
        test_story = "Pizza saved my hackathon project when I was debugging at 3am!"
        rating, explanation = await ai_evaluate_story(test_story)
        print(f"   AI rating: {rating}/10")
        print(f"   AI explanation: {explanation[:100]}...")
        
        # Test personalized response
        print("   Testing personalized response...")
        response = await ai_generate_personalized_response(test_story, rating, "STANDARD", "TEST-123")
        print(f"   AI response: {response[:100]}...")
        
        # Test intent understanding
        print("   Testing intent understanding...")
        intent = await ai_understand_user_intent("Can I get a pizza coupon?")
        print(f"   AI intent: {intent}")
        
        # Test dynamic prompts
        print("   Testing dynamic prompts...")
        prompt = await ai_generate_dynamic_prompts()
        print(f"   AI prompt: {prompt[:100]}...")
        
        print("✅ AI functions test completed")
        return True
        
    except Exception as e:
        print(f"❌ AI functions test failed: {e}")
        return False

def test_config_migration():
    """Test that configuration has been properly migrated"""
    print("\n⚙️ Testing Configuration Migration...")
    
    try:
        from config import (
            USE_GEMINI, USE_AI_EVALUATION, USE_AI_RESPONSES,
            USE_AI_MODERATION, USE_AI_PROMPTS, GEMINI_MODEL
        )
        
        print(f"   USE_GEMINI: {USE_GEMINI}")
        print(f"   USE_AI_EVALUATION: {USE_AI_EVALUATION}")
        print(f"   USE_AI_RESPONSES: {USE_AI_RESPONSES}")
        print(f"   USE_AI_MODERATION: {USE_AI_MODERATION}")
        print(f"   USE_AI_PROMPTS: {USE_AI_PROMPTS}")
        print(f"   GEMINI_MODEL: {GEMINI_MODEL}")
        
        # Check that old OpenAI config is not being used
        try:
            from config import USE_OPENAI
            if USE_OPENAI:
                print("⚠️  Warning: USE_OPENAI is still True - should be migrated to USE_GEMINI")
            else:
                print("✅ OpenAI configuration properly disabled")
        except ImportError:
            print("✅ OpenAI configuration removed")
        
        print("✅ Configuration migration test completed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

async def main():
    """Run all migration tests"""
    print("🚀 Gemini API Migration Test Suite")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Environment setup
    if test_environment_setup():
        tests_passed += 1
    
    # Test 2: Imports
    if test_imports():
        tests_passed += 1
    
    # Test 3: Configuration
    if test_config_migration():
        tests_passed += 1
    
    # Test 4: Gemini functions
    if await test_gemini_functions():
        tests_passed += 1
    
    # Test 5: AI functions
    if await test_ai_functions():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Gemini migration is successful!")
        print("\n📋 Next Steps:")
        print("   1. Set your GEMINI_API_KEY in .env file")
        print("   2. Run 'python agent.py' to start the pizza agent")
        print("   3. Test with real users to verify functionality")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure 'pip install google-generativeai' was run")
        print("   2. Check that .env file has GEMINI_API_KEY set")
        print("   3. Verify internet connection for API calls")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)