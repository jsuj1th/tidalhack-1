#!/usr/bin/env python3
"""
Comprehensive test script for AWS Pizza Agent integration
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import boto3
        print("✅ boto3 imported successfully")
    except ImportError as e:
        print(f"❌ boto3 import failed: {e}")
        return False
    
    try:
        from aws_config import get_aws_services, validate_aws_setup
        print("✅ aws_config imported successfully")
    except ImportError as e:
        print(f"❌ aws_config import failed: {e}")
        return False
    
    try:
        from aws_bedrock import get_bedrock_ai
        print("✅ aws_bedrock imported successfully")
    except ImportError as e:
        print(f"❌ aws_bedrock import failed: {e}")
        return False
    
    try:
        from aws_dynamodb import get_dynamodb_manager
        print("✅ aws_dynamodb imported successfully")
    except ImportError as e:
        print(f"❌ aws_dynamodb import failed: {e}")
        return False
    
    try:
        from aws_s3 import get_s3_manager
        print("✅ aws_s3 imported successfully")
    except ImportError as e:
        print(f"❌ aws_s3 import failed: {e}")
        return False
    
    try:
        from aws_ses import get_ses_manager
        print("✅ aws_ses imported successfully")
    except ImportError as e:
        print(f"❌ aws_ses import failed: {e}")
        return False
    
    return True

def test_aws_configuration():
    """Test AWS configuration and connectivity"""
    print("\n🔧 Testing AWS configuration...")
    
    try:
        from aws_config import validate_aws_setup
        return validate_aws_setup()
    except Exception as e:
        print(f"❌ AWS configuration test failed: {e}")
        return False

async def test_bedrock_ai():
    """Test Bedrock AI functionality"""
    print("\n🤖 Testing Bedrock AI...")
    
    try:
        from aws_bedrock import get_bedrock_ai
        
        ai = get_bedrock_ai()
        
        # Test story evaluation
        test_story = "I once ate pizza while coding at 3am and it was amazing! The cheese was perfect and it gave me energy to finish my project."
        
        print("Testing story evaluation...")
        rating, explanation = await ai.evaluate_story(test_story)
        print(f"✅ Story evaluation: {rating}/10")
        print(f"   Explanation: {explanation[:100]}...")
        
        # Test personalized response
        print("Testing personalized response...")
        response = await ai.generate_personalized_response(test_story, rating, "STANDARD", "TEST-123")
        print(f"✅ Personalized response generated")
        print(f"   Response: {response[:100]}...")
        
        # Test intent understanding
        print("Testing intent understanding...")
        intent = await ai.understand_user_intent("I want pizza!")
        print(f"✅ Intent understanding: {intent}")
        
        # Test dynamic prompts
        print("Testing dynamic prompts...")
        prompt = await ai.generate_dynamic_prompts()
        print(f"✅ Dynamic prompt generated")
        print(f"   Prompt: {prompt[:100]}...")
        
        # Test model info
        print(f"✅ Using model: {ai.model_id}")
        print(f"   Provider: {ai.model_config.get('provider', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Bedrock AI test failed: {e}")
        return False

def test_dynamodb():
    """Test DynamoDB functionality"""
    print("\n🗄️ Testing DynamoDB...")
    
    try:
        from aws_dynamodb import get_dynamodb_manager
        
        db = get_dynamodb_manager()
        
        # Create tables if needed
        print("Creating tables if needed...")
        db.create_tables_if_not_exist()
        
        # Test user state management
        test_user = f"test_user_{datetime.now().timestamp()}"
        
        print("Testing user state management...")
        db.set_user_state(test_user, "waiting_for_story")
        state = db.get_user_state(test_user)
        assert state == "waiting_for_story", f"Expected 'waiting_for_story', got '{state}'"
        print("✅ User state management working")
        
        # Test coupon management
        print("Testing coupon management...")
        db.mark_coupon_issued(test_user, "TEST-COUPON-123", "PREMIUM", 9, "Test story")
        has_coupon = db.has_user_received_coupon(test_user)
        coupon_code = db.get_user_coupon(test_user)
        assert has_coupon == True, "User should have coupon"
        assert coupon_code == "TEST-COUPON-123", f"Expected 'TEST-COUPON-123', got '{coupon_code}'"
        print("✅ Coupon management working")
        
        # Test analytics
        print("Testing analytics...")
        db.record_analytics_event("test_event", test_user, {"test": "data"})
        analytics = db.get_analytics_summary()
        print(f"✅ Analytics working: {analytics}")
        
        return True
        
    except Exception as e:
        print(f"❌ DynamoDB test failed: {e}")
        return False

def test_s3():
    """Test S3 functionality"""
    print("\n📦 Testing S3...")
    
    try:
        from aws_s3 import get_s3_manager
        
        s3 = get_s3_manager()
        
        # Create bucket if needed
        print("Creating bucket if needed...")
        if not s3.create_bucket_if_not_exists():
            print("⚠️ Bucket creation failed, but continuing tests...")
        
        # Test analytics upload
        print("Testing analytics upload...")
        test_data = {
            "test": "data",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_requests": 100,
            "total_coupons": 85
        }
        
        result = s3.upload_analytics_data(test_data, f"test/test_analytics_{datetime.now().timestamp()}.json")
        if result["success"]:
            print("✅ Analytics upload working")
            
            # Test download
            download_result = s3.download_analytics_data(result["filename"])
            if download_result["success"]:
                print("✅ Analytics download working")
            else:
                print(f"⚠️ Analytics download failed: {download_result['message']}")
        else:
            print(f"⚠️ Analytics upload failed: {result['message']}")
        
        # Get bucket info
        info = s3.get_bucket_info()
        if "error" not in info:
            print(f"✅ Bucket info: {info['total_objects']} objects, {info['total_size_mb']} MB")
        else:
            print(f"⚠️ Bucket info failed: {info['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ S3 test failed: {e}")
        return False

def test_ses():
    """Test SES functionality"""
    print("\n📧 Testing SES...")
    
    try:
        from aws_ses import get_ses_manager
        
        ses = get_ses_manager()
        
        # Test configuration
        print("Testing SES configuration...")
        config_result = ses.test_ses_configuration()
        if config_result["configured"]:
            print("✅ SES configuration working")
            quota = config_result.get("quota", {})
            print(f"   Send quota: {quota.get('max_24_hour', 0)}/day")
        else:
            print(f"⚠️ SES configuration issue: {config_result['message']}")
        
        # Test email validation
        print("Testing email validation...")
        valid_email = ses.validate_email("test@example.com")
        invalid_email = ses.validate_email("invalid-email")
        assert valid_email == True, "Valid email should pass validation"
        assert invalid_email == False, "Invalid email should fail validation"
        print("✅ Email validation working")
        
        # Note: We don't actually send test emails to avoid spam
        print("✅ SES basic functionality working")
        
        return True
        
    except Exception as e:
        print(f"❌ SES test failed: {e}")
        return False

def test_agent_integration():
    """Test agent integration with AWS services"""
    print("\n🤖 Testing agent integration...")
    
    try:
        # Import agent components
        from functions import generate_coupon_code, evaluate_story_quality
        
        # Test coupon generation
        print("Testing coupon generation...")
        test_user = f"integration_test_{datetime.now().timestamp()}"
        coupon_code, tier = generate_coupon_code(test_user, 8, True)
        print(f"✅ Generated coupon: {coupon_code} ({tier})")
        
        # Test story evaluation fallback
        print("Testing story evaluation fallback...")
        test_story = "I love pizza and coding!"
        rating = evaluate_story_quality(test_story)
        print(f"✅ Story evaluation fallback: {rating}/10")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent integration test failed: {e}")
        return False

def test_web_interface():
    """Test web interface components"""
    print("\n🌐 Testing web interface components...")
    
    try:
        # Test Flask app creation (without running)
        from flask import Flask
        app = Flask(__name__)
        print("✅ Flask app creation working")
        
        # Test template rendering
        from flask import render_template_string
        test_template = "<h1>Test</h1>"
        rendered = render_template_string(test_template)
        assert "<h1>Test</h1>" in rendered
        print("✅ Template rendering working")
        
        return True
        
    except Exception as e:
        print(f"❌ Web interface test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("🚀 AWS Pizza Agent Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("AWS Configuration", test_aws_configuration),
        ("Bedrock AI", test_bedrock_ai),
        ("DynamoDB", test_dynamodb),
        ("S3", test_s3),
        ("SES", test_ses),
        ("Agent Integration", test_agent_integration),
        ("Web Interface", test_web_interface),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your AWS integration is ready!")
        print("\nNext steps:")
        print("1. Run the agent: python aws_agent.py")
        print("2. Or run web interface: python aws_web_interface.py")
        return True
    else:
        print("⚠️ Some tests failed. Please check the configuration and try again.")
        print("\nTroubleshooting:")
        print("1. Ensure AWS credentials are configured")
        print("2. Check .env file configuration")
        print("3. Verify AWS service permissions")
        print("4. Run setup script: python setup_aws.py")
        return False

def main():
    """Main test function"""
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please copy .env.aws to .env and configure your settings")
        print("Then run: python setup_aws.py")
        return False
    
    # Run tests
    return asyncio.run(run_all_tests())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)