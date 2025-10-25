#!/usr/bin/env python3
"""
Demo script showing the email coupon feature
"""

import sys
import os
from email_utils import test_email_configuration, send_coupon_email, validate_email
from functions import generate_coupon_code, evaluate_story_quality
from user_config import get_user_email, get_test_config

def demo_email_feature():
    """Demonstrate the email coupon functionality"""
    
    print("🍕 Pizza Agent Email Feature Demo")
    print("=" * 50)
    
    # Test email configuration
    print("\n1. Testing Email Configuration...")
    config_result = test_email_configuration()
    print(f"   Configured: {'✅' if config_result['configured'] else '❌'}")
    print(f"   Message: {config_result['message']}")
    
    if not config_result['configured']:
        print("\n💡 To enable email features:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your email credentials:")
        print("      EMAIL_ADDRESS=your_email@gmail.com")
        print("      EMAIL_PASSWORD=your_app_password")
        print("   3. For Gmail, use an App Password (not regular password)")
        print("\n📖 See EMAIL_SETUP.md for detailed instructions")
        return
    
    # Test email validation
    print("\n2. Testing Email Validation...")
    test_emails = [
        "valid@example.com",
        "invalid-email",
        "test@domain",
        "user@university.edu"
    ]
    
    for email in test_emails:
        is_valid = validate_email(email)
        print(f"   {email}: {'✅' if is_valid else '❌'}")
    
    # Generate a sample coupon
    print("\n3. Generating Sample Coupon...")
    test_story = "I had amazing pizza during my hackathon! It gave me energy to code all night and win!"
    story_rating = evaluate_story_quality(test_story)
    coupon_code, tier = generate_coupon_code("demo_user", story_rating, True)
    
    print(f"   Story Rating: {story_rating}/10")
    print(f"   Coupon Code: {coupon_code}")
    print(f"   Tier: {tier}")
    
    # Ask user if they want to test email sending
    print("\n4. Email Sending Test (Optional)")
    default_email = get_user_email()
    test_email = input(f"   Enter your email to test sending (or press Enter for {default_email}): ").strip()
    
    if not test_email:
        test_email = default_email
    
    if test_email:
        if validate_email(test_email):
            print(f"   Sending test coupon to {test_email}...")
            
            result = send_coupon_email(
                test_email,
                coupon_code,
                tier,
                story_rating,
                f"🎉 This is a test email from the Pizza Agent! Your story rated {story_rating}/10!"
            )
            
            if result['success']:
                print(f"   ✅ {result['message']}")
                print("   📧 Check your inbox (and spam folder)!")
            else:
                print(f"   ❌ {result['message']}")
        else:
            print("   ❌ Invalid email address format")
    else:
        print("   ⏭️  Skipped email test")
    
    print("\n5. Web Interface Demo")
    print("   Run: python web_test_interface.py")
    print("   Then visit: http://127.0.0.1:5000")
    print("   Try the 'Generate Full Coupon Response' feature!")
    
    print("\n🎉 Demo Complete!")
    print("\nNext Steps:")
    print("• Configure email credentials in .env file")
    print("• Test the web interface")
    print("• Try the chat agent with email requests")
    print("• Read EMAIL_SETUP.md for full documentation")

if __name__ == "__main__":
    demo_email_feature()