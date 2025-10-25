#!/usr/bin/env python3
"""
Script to validate and test Gemini API key and find available models
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def test_api_key():
    """Test if the API key is working"""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ No GEMINI_API_KEY found in environment")
        return False
    
    print(f"🔑 Testing API key: {api_key[:10]}...")
    
    try:
        genai.configure(api_key=api_key)
        print("✅ API key configured successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to configure API key: {e}")
        return False

def list_available_models():
    """List available models"""
    print("\n📋 Attempting to list available models...")
    
    try:
        models = genai.list_models()
        print("✅ Successfully retrieved model list:")
        
        generation_models = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                generation_models.append(model)
                print(f"   ✓ {model.name} - {model.display_name}")
        
        if generation_models:
            print(f"\n🎯 Found {len(generation_models)} models that support generateContent")
            return generation_models[0].name  # Return first available model
        else:
            print("⚠️  No models found that support generateContent")
            return None
            
    except Exception as e:
        print(f"❌ Failed to list models: {e}")
        print("   This might be due to:")
        print("   1. Invalid API key")
        print("   2. Insufficient permissions")
        print("   3. Billing not enabled")
        print("   4. Network connectivity issues")
        return None

def test_model_generation(model_name):
    """Test content generation with a specific model"""
    print(f"\n🧪 Testing content generation with {model_name}...")
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello! Can you help me test this API?")
        
        if response and response.text:
            print("✅ Content generation successful!")
            print(f"   Response: {response.text[:100]}...")
            return True
        else:
            print("❌ Content generation returned empty response")
            return False
            
    except Exception as e:
        print(f"❌ Content generation failed: {e}")
        return False

def test_common_models():
    """Test common Gemini model names"""
    common_models = [
        "gemini-pro",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "models/gemini-pro",
        "models/gemini-1.5-pro", 
        "models/gemini-1.5-flash"
    ]
    
    print("\n🔍 Testing common model names...")
    
    for model_name in common_models:
        print(f"\n   Testing {model_name}...")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Test")
            if response and response.text:
                print(f"   ✅ {model_name} works!")
                return model_name
        except Exception as e:
            print(f"   ❌ {model_name} failed: {str(e)[:100]}...")
    
    return None

def main():
    """Main validation function"""
    print("🚀 Gemini API Validation Tool")
    print("=" * 50)
    
    # Test 1: API Key
    if not test_api_key():
        print("\n💡 To fix this:")
        print("   1. Go to https://aistudio.google.com/app/apikey")
        print("   2. Create a new API key")
        print("   3. Update your .env file with GEMINI_API_KEY=your_new_key")
        return False
    
    # Test 2: List Models
    working_model = list_available_models()
    
    if working_model:
        # Test 3: Content Generation
        if test_model_generation(working_model):
            print(f"\n🎉 Success! Use this model in your config: {working_model}")
            print(f"\n📝 Update config.py:")
            print(f'   GEMINI_MODEL = "{working_model}"')
            return True
    else:
        # Test 4: Try common models
        working_model = test_common_models()
        if working_model:
            print(f"\n🎉 Found working model: {working_model}")
            print(f"\n📝 Update config.py:")
            print(f'   GEMINI_MODEL = "{working_model}"')
            return True
    
    print("\n❌ No working models found")
    print("\n🔧 Troubleshooting steps:")
    print("   1. Check your API key at https://aistudio.google.com/app/apikey")
    print("   2. Ensure billing is enabled if required")
    print("   3. Try generating a new API key")
    print("   4. Check Google AI Studio documentation")
    
    print("\n✅ Good news: The pizza agent will still work with fallback responses!")
    return False

if __name__ == "__main__":
    main()