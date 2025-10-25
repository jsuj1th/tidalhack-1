#!/usr/bin/env python3
"""
Test script for hackathon feedback system
Validates all components work correctly
"""

import asyncio
import json
import os
from datetime import datetime
from uuid import uuid4

# Import our modules
from functions import (
    store_feedback,
    analyze_feedback_sentiment,
    categorize_feedback,
    validate_feedback,
    get_feedback_summary
)
from ai_functions import (
    ai_analyze_feedback,
    ai_generate_response,
    ai_categorize_feedback,
    ai_detect_spam
)
from aws_services import (
    create_dynamodb_table,
    store_feedback_dynamodb,
    get_feedback_from_dynamodb,
    test_aws_services
)
from config import HACKATHON_ID, HACKATHON_NAME, GOOGLE_API_KEY

class FeedbackSystemTester:
    def __init__(self):
        self.test_feedback = [
            "I'm really excited about this hackathon! I hope to learn about AI and machine learning, and maybe build something cool with APIs.",
            "I'm worried about the venue logistics. Will there be enough parking? Also, I hope the WiFi is reliable for development work.",
            "Looking forward to the networking opportunities and meeting other developers. I want to find a good team to work with.",
            "The workshop schedule looks great! I'm particularly interested in the blockchain and web3 sessions.",
            "spam test message asdf qwerty"  # This should be detected as spam
        ]
    
    async def test_core_functions(self):
        """Test core feedback processing functions"""
        print("🧪 Testing Core Functions")
        print("-" * 30)
        
        for i, feedback in enumerate(self.test_feedback[:4]):  # Skip spam test
            print(f"\nTest {i+1}: {feedback[:50]}...")
            
            # Test validation
            is_valid, error = await validate_feedback(feedback)
            print(f"  ✅ Validation: {'Valid' if is_valid else f'Invalid - {error}'}")
            
            # Test sentiment analysis
            sentiment = await analyze_feedback_sentiment(feedback)
            print(f"  ✅ Sentiment: {sentiment}")
            
            # Test categorization
            category = await categorize_feedback(feedback)
            print(f"  ✅ Category: {category}")
            
            # Test storage
            feedback_data = {
                "feedback_id": str(uuid4()),
                "user_hash": f"TEST{i+1:03d}",
                "hackathon_id": HACKATHON_ID,
                "feedback_text": feedback,
                "timestamp": datetime.now().isoformat(),
                "analysis": {
                    "sentiment": sentiment,
                    "category": category
                },
                "metadata": {
                    "test": True,
                    "message_length": len(feedback)
                }
            }
            
            try:
                await store_feedback(feedback_data)
                print(f"  ✅ Storage: Success")
            except Exception as e:
                print(f"  ❌ Storage: Failed - {e}")
    
    async def test_ai_functions(self):
        """Test AI-powered functions"""
        print("\n🤖 Testing AI Functions")
        print("-" * 30)
        
        if not GOOGLE_API_KEY:
            print("⚠️  Google API key not configured - skipping AI tests")
            return
        
        test_feedback = self.test_feedback[0]  # Use first feedback for AI tests
        
        try:
            # Test AI analysis
            print(f"\nTesting AI analysis...")
            analysis = await ai_analyze_feedback(test_feedback)
            print(f"  ✅ AI Analysis: {analysis}")
            
            # Test AI response generation
            print(f"\nTesting AI response generation...")
            response = await ai_generate_response(test_feedback, analysis)
            print(f"  ✅ AI Response: {response[:100]}...")
            
            # Test AI categorization
            print(f"\nTesting AI categorization...")
            category = await ai_categorize_feedback(test_feedback)
            print(f"  ✅ AI Category: {category}")
            
            # Test spam detection
            print(f"\nTesting spam detection...")
            spam_feedback = self.test_feedback[-1]  # Last one is spam
            is_spam = await ai_detect_spam(spam_feedback)
            print(f"  ✅ Spam Detection: {'Spam detected' if is_spam else 'Not spam'}")
            
        except Exception as e:
            print(f"  ❌ AI Functions failed: {e}")
    
    async def test_aws_services(self):
        """Test AWS service connections"""
        print("\n☁️  Testing AWS Services")
        print("-" * 30)
        
        try:
            await test_aws_services()
            
            # Test DynamoDB operations
            print(f"\nTesting DynamoDB operations...")
            
            # Create table
            success = await create_dynamodb_table()
            print(f"  ✅ Table Creation: {'Success' if success else 'Failed/Exists'}")
            
            # Test data storage and retrieval
            test_data = {
                "feedback_id": str(uuid4()),
                "user_hash": "TESTAWS",
                "hackathon_id": HACKATHON_ID,
                "feedback_text": "Test feedback for AWS integration",
                "timestamp": datetime.now().isoformat(),
                "analysis": {"sentiment": "neutral", "category": "GENERAL"},
                "metadata": {"test": True}
            }
            
            try:
                await store_feedback_dynamodb(test_data)
                print(f"  ✅ DynamoDB Storage: Success")
                
                # Try to retrieve
                feedback_list = await get_feedback_from_dynamodb(HACKATHON_ID, limit=5)
                print(f"  ✅ DynamoDB Retrieval: {len(feedback_list)} items found")
                
            except Exception as e:
                print(f"  ❌ DynamoDB Operations: {e}")
                
        except Exception as e:
            print(f"  ❌ AWS Services: {e}")
    
    async def test_analytics(self):
        """Test analytics generation"""
        print("\n📊 Testing Analytics")
        print("-" * 30)
        
        try:
            summary = await get_feedback_summary(HACKATHON_ID)
            print(f"  ✅ Analytics Summary:")
            print(f"     Total feedback: {summary.get('total_feedback', 0)}")
            print(f"     Sentiment distribution: {summary.get('sentiment_distribution', {})}")
            print(f"     Category distribution: {summary.get('category_distribution', {})}")
            
        except Exception as e:
            print(f"  ❌ Analytics: {e}")
    
    async def run_all_tests(self):
        """Run all tests"""
        print(f"🚀 Testing Hackathon Feedback System")
        print(f"   Hackathon: {HACKATHON_NAME}")
        print(f"   ID: {HACKATHON_ID}")
        print("=" * 50)
        
        # Run tests
        await self.test_core_functions()
        await self.test_ai_functions()
        await self.test_aws_services()
        await self.test_analytics()
        
        print("\n" + "=" * 50)
        print("🎉 Testing Complete!")
        print("\nIf all tests passed, your system is ready for deployment!")
        print("\nNext steps:")
        print("1. Configure your .env file with proper credentials")
        print("2. Deploy to AWS using the setup script or Terraform")
        print("3. Start the agent with: python agent.py")

async def main():
    """Main test function"""
    tester = FeedbackSystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())