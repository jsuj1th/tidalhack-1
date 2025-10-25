# functions.py
"""
Core functions for hackathon feedback collection and processing
"""

from uagents import Model
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json
import hashlib
import asyncio

class FeedbackRequest(Model):
    feedback_text: str
    user_email: Optional[str] = None
    category: Optional[str] = None

class FeedbackResponse(Model):
    feedback_id: str
    status: str
    message: str
    analysis: Optional[Dict] = None

class FeedbackAnalysis(Model):
    sentiment: str  # positive, negative, neutral
    category: str   # EXPECTATIONS, LOGISTICS, TECHNICAL, etc.
    keywords: List[str]
    confidence: float

# In-memory storage for development (replace with DynamoDB in production)
feedback_storage = []

async def store_feedback(feedback_data: Dict) -> str:
    """
    Store feedback data locally (fallback method)
    In production, this should use DynamoDB
    """
    try:
        feedback_storage.append(feedback_data)
        
        # Also save to file for persistence
        with open("feedback_data.json", "w") as f:
            json.dump(feedback_storage, f, indent=2, default=str)
        
        return feedback_data["feedback_id"]
    except Exception as e:
        print(f"Error storing feedback: {e}")
        raise

async def analyze_feedback_sentiment(feedback_text: str) -> str:
    """
    Analyze sentiment of feedback text
    Returns: positive, negative, or neutral
    """
    try:
        # Simple rule-based sentiment analysis (fallback)
        positive_words = [
            "excited", "amazing", "great", "awesome", "love", "fantastic", 
            "excellent", "wonderful", "perfect", "brilliant", "outstanding",
            "looking forward", "can't wait", "thrilled", "pumped"
        ]
        
        negative_words = [
            "worried", "concerned", "disappointed", "bad", "terrible", 
            "awful", "hate", "horrible", "poor", "lacking", "insufficient",
            "frustrated", "annoyed", "upset", "anxious"
        ]
        
        text_lower = feedback_text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
            
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        return "neutral"

async def categorize_feedback(feedback_text: str) -> str:
    """
    Categorize feedback into predefined categories
    Returns category string
    """
    try:
        text_lower = feedback_text.lower()
        
        # Category keywords
        category_keywords = {
            "EXPECTATIONS": [
                "expect", "hope", "goal", "want", "wish", "looking for",
                "achieve", "learn", "skill", "experience", "outcome"
            ],
            "LOGISTICS": [
                "venue", "location", "food", "accommodation", "parking",
                "schedule", "timing", "registration", "check-in", "wifi"
            ],
            "TECHNICAL": [
                "api", "tools", "platform", "software", "hardware", 
                "infrastructure", "development", "coding", "programming"
            ],
            "NETWORKING": [
                "network", "meet", "connect", "team", "collaborate",
                "mentorship", "mentor", "partner", "social", "community"
            ],
            "LEARNING": [
                "workshop", "tutorial", "session", "presentation", "talk",
                "education", "training", "skill", "knowledge", "course"
            ]
        }
        
        # Count matches for each category
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            category_scores[category] = score
        
        # Return category with highest score, or GENERAL if no clear match
        if max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
        else:
            return "GENERAL"
            
    except Exception as e:
        print(f"Error in categorization: {e}")
        return "GENERAL"

async def extract_keywords(feedback_text: str) -> List[str]:
    """
    Extract key terms from feedback text
    """
    try:
        # Simple keyword extraction
        import re
        
        # Remove common words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", 
            "for", "of", "with", "by", "is", "are", "was", "were", "be",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "can", "i", "you", "he",
            "she", "it", "we", "they", "this", "that", "these", "those"
        }
        
        # Extract words (alphanumeric, 3+ characters)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', feedback_text.lower())
        
        # Filter out stop words and get unique keywords
        keywords = list(set([word for word in words if word not in stop_words]))
        
        # Return top 10 most relevant keywords
        return keywords[:10]
        
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        return []

async def get_feedback_summary(hackathon_id: str) -> Dict:
    """
    Generate summary statistics for collected feedback
    """
    try:
        # Filter feedback for specific hackathon
        hackathon_feedback = [
            f for f in feedback_storage 
            if f.get("hackathon_id") == hackathon_id
        ]
        
        if not hackathon_feedback:
            return {
                "total_feedback": 0,
                "sentiment_distribution": {},
                "category_distribution": {},
                "recent_feedback": []
            }
        
        # Calculate sentiment distribution
        sentiments = [f.get("analysis", {}).get("sentiment", "neutral") for f in hackathon_feedback]
        sentiment_dist = {
            "positive": sentiments.count("positive"),
            "negative": sentiments.count("negative"),
            "neutral": sentiments.count("neutral")
        }
        
        # Calculate category distribution
        categories = [f.get("analysis", {}).get("category", "GENERAL") for f in hackathon_feedback]
        category_dist = {}
        for category in categories:
            category_dist[category] = category_dist.get(category, 0) + 1
        
        # Get recent feedback (last 5)
        recent = sorted(hackathon_feedback, key=lambda x: x["timestamp"], reverse=True)[:5]
        recent_feedback = [
            {
                "timestamp": f["timestamp"],
                "sentiment": f.get("analysis", {}).get("sentiment", "neutral"),
                "category": f.get("analysis", {}).get("category", "GENERAL"),
                "preview": f["feedback_text"][:100] + "..." if len(f["feedback_text"]) > 100 else f["feedback_text"]
            }
            for f in recent
        ]
        
        return {
            "total_feedback": len(hackathon_feedback),
            "sentiment_distribution": sentiment_dist,
            "category_distribution": category_dist,
            "recent_feedback": recent_feedback,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error generating summary: {e}")
        return {"error": str(e)}

async def get_user_feedback_count(user_identifier: str) -> int:
    """
    Get number of feedback submissions from a specific user
    """
    try:
        user_hash = hashlib.sha256(user_identifier.encode()).hexdigest()[:8].upper()
        count = sum(1 for f in feedback_storage if f.get("user_hash") == user_hash)
        return count
    except Exception as e:
        print(f"Error getting user feedback count: {e}")
        return 0

async def validate_feedback(feedback_text: str) -> Tuple[bool, str]:
    """
    Validate feedback text for quality and appropriateness
    Returns: (is_valid, error_message)
    """
    try:
        if not feedback_text or not feedback_text.strip():
            return False, "Feedback cannot be empty"
        
        if len(feedback_text.strip()) < 10:
            return False, "Feedback is too short. Please provide more detail."
        
        if len(feedback_text) > 2000:
            return False, "Feedback is too long. Please keep it under 2000 characters."
        
        # Check for spam patterns
        spam_patterns = [
            r'(.)\1{10,}',  # Repeated characters
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # URLs
            r'\b(?:spam|test|asdf|qwerty)\b',  # Common spam words
        ]
        
        import re
        for pattern in spam_patterns:
            if re.search(pattern, feedback_text.lower()):
                return False, "Feedback appears to be spam or invalid"
        
        return True, ""
        
    except Exception as e:
        print(f"Error validating feedback: {e}")
        return True, ""  # Default to valid if validation fails

# Analytics functions
async def get_analytics_data(hackathon_id: str) -> Dict:
    """
    Get comprehensive analytics for hackathon feedback
    """
    try:
        summary = await get_feedback_summary(hackathon_id)
        
        # Add more detailed analytics
        hackathon_feedback = [
            f for f in feedback_storage 
            if f.get("hackathon_id") == hackathon_id
        ]
        
        if not hackathon_feedback:
            return summary
        
        # Time-based analysis
        from collections import defaultdict
        hourly_submissions = defaultdict(int)
        
        for feedback in hackathon_feedback:
            try:
                timestamp = datetime.fromisoformat(feedback["timestamp"].replace('Z', '+00:00'))
                hour = timestamp.hour
                hourly_submissions[hour] += 1
            except:
                continue
        
        # Average feedback length
        lengths = [len(f["feedback_text"]) for f in hackathon_feedback]
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        
        # Top keywords across all feedback
        all_keywords = []
        for feedback in hackathon_feedback:
            keywords = await extract_keywords(feedback["feedback_text"])
            all_keywords.extend(keywords)
        
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        summary.update({
            "hourly_distribution": dict(hourly_submissions),
            "average_feedback_length": round(avg_length, 2),
            "top_keywords": top_keywords,
            "analytics_generated": datetime.now().isoformat()
        })
        
        return summary
        
    except Exception as e:
        print(f"Error generating analytics: {e}")
        return {"error": str(e)}

# Testing functions
async def test_feedback_processing():
    """Test function for feedback processing"""
    test_feedback = [
        "I'm really excited about this hackathon! I hope to learn about AI and machine learning, and maybe build something cool with APIs.",
        "I'm worried about the venue logistics. Will there be enough parking? Also, I hope the WiFi is reliable for development work.",
        "Looking forward to the networking opportunities and meeting other developers. I want to find a good team to work with.",
        "The workshop schedule looks great! I'm particularly interested in the blockchain and web3 sessions."
    ]
    
    print("Testing feedback processing...")
    
    for i, feedback in enumerate(test_feedback):
        print(f"\nTest {i+1}: {feedback[:50]}...")
        
        # Test sentiment analysis
        sentiment = await analyze_feedback_sentiment(feedback)
        print(f"Sentiment: {sentiment}")
        
        # Test categorization
        category = await categorize_feedback(feedback)
        print(f"Category: {category}")
        
        # Test keyword extraction
        keywords = await extract_keywords(feedback)
        print(f"Keywords: {keywords[:5]}")
        
        # Test validation
        is_valid, error = await validate_feedback(feedback)
        print(f"Valid: {is_valid}, Error: {error}")

if __name__ == "__main__":
    # Run tests
    asyncio.run(test_feedback_processing())