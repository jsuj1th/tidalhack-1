#!/usr/bin/env python3
"""
Quick email test using stored user configuration
"""

from email_utils import send_coupon_email, test_email_configuration
from functions import generate_coupon_code, evaluate_story_quality
from user_config import get_user_email, get_test_config
import asyncio
from ai_functions import ai_evaluate_story, ai_generate_personalized_response

def quick_test():
    """Quick test with stored user email"""
    
    print("🍕 Quick Email Test with Stored Configuration")
    print("=" * 50)
    
    # Get user config
    user_config = get_test_config()
    user_email = user_config['email']
    user_name = user_config['name']
    
    print(f"📧 Using stored email: {user_email}")
    print(f"👤 User: {user_name}")
    
    # Test email configuration
    print("\n1. Testing Email Configuration...")
    config_result = test_email_configuration()
    print(f"   Status: {'✅' if config_result['configured'] else '❌'}")
    
    if not config_result['configured']:
        print(f"   Error: {config_result['message']}")
        return
    
    # Generate a test coupon
    print("\n2. Generating Test Coupon...")
    test_story = f"Hey {user_name}! I had the most amazing pizza during CalHacks! It was a pepperoni masterpiece that fueled my coding marathon. The cheese was perfectly melted and the crust was crispy. It gave me the energy to debug for 8 hours straight and build an incredible AI project!"
    
    # Use AI evaluation if available
    try:
        print("   Using AI evaluation...")
        rating, explanation = asyncio.run(ai_evaluate_story(test_story))
        print(f"   AI Rating: {rating}/10")
        print(f"   AI Explanation: {explanation[:100]}...")
    except Exception as e:
        print(f"   AI evaluation failed: {e}")
        rating = evaluate_story_quality(test_story)
        print(f"   Fallback Rating: {rating}/10")
    
    # Generate coupon
    coupon_code, tier = generate_coupon_code(user_config['user_id'], rating, True)
    print(f"   Coupon Code: {coupon_code}")
    print(f"   Tier: {tier}")
    
    # Generate personalized response
    try:
        print("\n3. Generating Personalized Response...")
        response = asyncio.run(ai_generate_personalized_response(test_story, rating, tier, coupon_code))
        print(f"   AI Response: {response[:150]}...")
    except Exception as e:
        print(f"   AI response failed: {e}")
        response = f"🎉 Great story, {user_name}! Your coupon: {coupon_code} - Tier: {tier}"
    
    # Send email
    print(f"\n4. Sending Email to {user_email}...")
    result = send_coupon_email(
        user_email,
        coupon_code,
        tier,
        rating,
        response
    )
    
    if result['success']:
        print(f"   ✅ {result['message']}")
        print("   📧 Check your inbox (and spam folder)!")
        print(f"   🎫 Coupon Code: {coupon_code}")
    else:
        print(f"   ❌ {result['message']}")
    
    print("\n🎉 Quick test complete!")

if __name__ == "__main__":
    quick_test()