#!/usr/bin/env python3
"""
Quick setup checker for Pizza Intelligence
"""

import os
from email_utils import test_email_configuration
from config import USE_GEMINI, USE_AI_EVALUATION, USE_AI_RESPONSES, USE_AI_PROMPTS

def check_setup():
    print("🍕 Pizza Intelligence - Setup Check")
    print("=" * 50)
    
    # Check email configuration
    print("\n📧 Email Configuration:")
    email_config = test_email_configuration()
    if email_config['configured']:
        print(f"   ✅ {email_config['message']}")
    else:
        print(f"   ❌ {email_config['message']}")
        print("   💡 Tip: Edit .env file with your email credentials")
    
    # Check AI configuration
    print("\n🤖 AI Configuration:")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key and gemini_key != "your_gemini_api_key_here":
        print("   ✅ Gemini API key configured")
        print(f"   📊 AI Evaluation: {'✅ Enabled' if USE_AI_EVALUATION else '❌ Disabled'}")
        print(f"   💬 AI Responses: {'✅ Enabled' if USE_AI_RESPONSES else '❌ Disabled'}")
        print(f"   ✨ AI Prompts: {'✅ Enabled' if USE_AI_PROMPTS else '❌ Disabled'}")
    else:
        print("   ⚠️  Gemini API key not configured (using fallback functions)")
        print("   💡 Tip: Add GEMINI_API_KEY to .env file for AI features")
    
    # Check dependencies
    print("\n📦 Dependencies:")
    try:
        import flask
        print("   ✅ Flask installed")
    except ImportError:
        print("   ❌ Flask not installed - run: pip install flask")
    
    try:
        import google.generativeai
        print("   ✅ Google Generative AI installed")
    except ImportError:
        print("   ❌ Google Generative AI not installed - run: pip install google-generativeai")
    
    # Overall status
    print("\n🎯 Overall Status:")
    if email_config['configured'] and gemini_key:
        print("   🚀 Ready for production! All features enabled.")
    elif email_config['configured']:
        print("   👍 Ready to go! Email works, AI features will use fallbacks.")
    else:
        print("   ⚠️  Basic functionality ready, but email needs setup.")
    
    print("\n🏃‍♂️ To start the app:")
    print("   python pizza_coupon_app.py")
    print("   Then open: http://127.0.0.1:5002")

if __name__ == "__main__":
    check_setup()