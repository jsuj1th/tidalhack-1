# ai_functions.py
"""
AI-powered functions for feedback analysis and response generation
Uses Google Gemini API for intelligent processing
"""

import google.generativeai as genai
import json
import asyncio
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

from config import (
    GOOGLE_API_KEY,
    GEMINI_MODEL,
    GEMINI_TEMPERATURE,
    GEMINI_MAX_TOKENS,
    HACKATHON_NAME,
    HACKATHON_ID,
    USE_GEMINI
)

logger = logging.getLogger(__name__)

# Initialize Gemini client
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    logger.info(f"Initialized Gemini model: {GEMINI_MODEL}")
else:
    logger.warning("Google API key not found. AI features will be disabled.")
    model = None

async def ai_analyze_feedback(feedback_text: str) -> Dict:
    """
    Comprehensive AI analysis of feedback text using Gemini
    Returns sentiment, category, keywords, and insights
    """
    try:
        if not GOOGLE_API_KEY or not model:
            raise Exception("Google API key not configured")
        
        prompt = f"""
        Analyze this hackathon participant feedback and provide a structured analysis:
        
        Feedback: "{feedback_text}"
        
        Please analyze and return a JSON response with:
        1. sentiment: "positive", "negative", or "neutral"
        2. category: one of ["EXPECTATIONS", "LOGISTICS", "TECHNICAL", "NETWORKING", "LEARNING", "GENERAL"]
        3. keywords: list of 3-5 key terms from the feedback
        4. confidence: confidence score (0.0-1.0) for the analysis
        5. insights: brief summary of main points
        6. actionable_items: specific suggestions for organizers (if any)
        
        Return only valid JSON without any markdown formatting or code blocks.
        """
        
        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            temperature=GEMINI_TEMPERATURE,
            max_output_tokens=GEMINI_MAX_TOKENS,
        )
        
        # Generate response
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=generation_config
        )
        
        # Parse JSON response
        response_text = response.text.strip()
        # Remove any markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        elif response_text.startswith('```'):
            response_text = response_text.replace('```', '').strip()
        
        result = json.loads(response_text)
        
        # Validate required fields
        required_fields = ["sentiment", "category", "keywords", "confidence"]
        for field in required_fields:
            if field not in result:
                result[field] = "unknown" if field != "confidence" else 0.5
        
        logger.info(f"Gemini analysis completed: {result['sentiment']}, {result['category']}")
        return result
        
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        # Return fallback analysis
        return {
            "sentiment": "neutral",
            "category": "GENERAL",
            "keywords": [],
            "confidence": 0.3,
            "insights": "Analysis unavailable",
            "actionable_items": []
        }

async def ai_generate_response(feedback_text: str, analysis_results: Dict) -> str:
    """
    Generate personalized response to participant feedback using Gemini
    """
    try:
        if not GOOGLE_API_KEY or not model:
            raise Exception("Google API key not configured")
        
        sentiment = analysis_results.get("sentiment", "neutral")
        category = analysis_results.get("category", "GENERAL")
        insights = analysis_results.get("insights", "")
        
        prompt = f"""
        Generate a warm, personalized response to this hackathon participant's feedback.
        
        Hackathon: {HACKATHON_NAME}
        Feedback: "{feedback_text}"
        Analysis: Sentiment={sentiment}, Category={category}
        Insights: {insights}
        
        Guidelines:
        - Be enthusiastic and appreciative
        - Address their specific points when possible
        - Show that their feedback will be used to improve the event
        - Keep it concise but personal (2-3 paragraphs max)
        - Use emojis appropriately
        - End with excitement about the hackathon
        
        Don't mention the analysis details directly.
        Return only the response text without any formatting or prefixes.
        """
        
        # Configure generation for more creative responses
        generation_config = genai.types.GenerationConfig(
            temperature=GEMINI_TEMPERATURE + 0.1,
            max_output_tokens=400,
        )
        
        # Generate response
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=generation_config
        )
        
        generated_response = response.text.strip()
        logger.info("Gemini response generated successfully")
        return generated_response
        
    except Exception as e:
        logger.error(f"Gemini response generation failed: {e}")
        # Return fallback response
        return generate_fallback_response(analysis_results)

async def ai_categorize_feedback(feedback_text: str) -> str:
    """
    Categorize feedback using Gemini
    """
    try:
        if not GOOGLE_API_KEY or not model:
            raise Exception("Google API key not configured")
        
        categories = {
            "EXPECTATIONS": "Goals, hopes, what they want to achieve or learn",
            "LOGISTICS": "Venue, food, accommodation, parking, schedule, registration",
            "TECHNICAL": "APIs, tools, platforms, software, hardware, development infrastructure",
            "NETWORKING": "Meeting people, finding teams, mentorship, collaboration",
            "LEARNING": "Workshops, tutorials, sessions, skill development, education",
            "GENERAL": "Other comments, suggestions, or feedback"
        }
        
        category_list = "\n".join([f"- {k}: {v}" for k, v in categories.items()])
        
        prompt = f"""
        Categorize this hackathon feedback into one of these categories:
        
        {category_list}
        
        Feedback: "{feedback_text}"
        
        Return only the category name (e.g., "EXPECTATIONS"). No explanation needed.
        """
        
        # Configure for consistent categorization
        generation_config = genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=20,
        )
        
        # Generate response
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=generation_config
        )
        
        category = response.text.strip().upper()
        
        # Validate category
        if category in categories:
            return category
        else:
            return "GENERAL"
            
    except Exception as e:
        logger.error(f"Gemini categorization failed: {e}")
        return "GENERAL"

async def ai_detect_spam(feedback_text: str) -> bool:
    """
    Detect if feedback is spam or inappropriate using Gemini
    """
    try:
        if not GOOGLE_API_KEY or not model:
            raise Exception("Google API key not configured")
        
        prompt = f"""
        Analyze if this text is spam, inappropriate, or not genuine feedback for a hackathon:
        
        Text: "{feedback_text}"
        
        Consider it spam/inappropriate if it:
        - Contains promotional content or links
        - Is nonsensical or random characters
        - Is offensive or inappropriate
        - Doesn't relate to hackathon expectations/feedback
        - Appears to be testing the system
        
        Return only "true" if it's spam/inappropriate, "false" if it's legitimate feedback.
        """
        
        # Configure for consistent spam detection
        generation_config = genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=10,
        )
        
        # Generate response
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=generation_config
        )
        
        result = response.text.strip().lower()
        return result == "true"
        
    except Exception as e:
        logger.error(f"Gemini spam detection failed: {e}")
        return False  # Default to not spam if detection fails

async def ai_extract_insights(feedback_list: List[str]) -> Dict:
    """
    Extract insights and trends from multiple feedback submissions using Gemini
    """
    try:
        if not GOOGLE_API_KEY or not model or not feedback_list:
            raise Exception("Google API key not configured or no feedback provided")
        
        # Combine feedback (limit to prevent token overflow)
        combined_feedback = "\n\n".join(feedback_list[:15])  # Limit to 15 pieces for Gemini
        
        prompt = f"""
        Analyze these hackathon participant feedback submissions and extract key insights:
        
        Feedback Collection:
        {combined_feedback}
        
        Provide a JSON response with:
        1. common_themes: list of 3-5 most common themes/topics
        2. sentiment_summary: overall sentiment trend
        3. top_expectations: most mentioned expectations or goals
        4. concerns: any common concerns or issues raised
        5. suggestions: actionable suggestions for organizers
        6. participant_types: types of participants based on feedback (e.g., "beginners", "experienced developers")
        
        Return only valid JSON without any markdown formatting or code blocks.
        """
        
        # Configure generation
        generation_config = genai.types.GenerationConfig(
            temperature=0.3,
            max_output_tokens=1000,
        )
        
        # Generate response
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=generation_config
        )
        
        # Parse JSON response
        response_text = response.text.strip()
        # Remove any markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        elif response_text.startswith('```'):
            response_text = response_text.replace('```', '').strip()
        
        insights = json.loads(response_text)
        logger.info("Gemini insights extraction completed")
        return insights
        
    except Exception as e:
        logger.error(f"Gemini insights extraction failed: {e}")
        return {
            "common_themes": [],
            "sentiment_summary": "mixed",
            "top_expectations": [],
            "concerns": [],
            "suggestions": [],
            "participant_types": []
        }

async def ai_generate_summary_report(hackathon_id: str, feedback_data: List[Dict]) -> str:
    """
    Generate a comprehensive summary report of all feedback using Gemini
    """
    try:
        if not GOOGLE_API_KEY or not model or not feedback_data:
            raise Exception("Google API key not configured or no feedback data")
        
        # Prepare summary statistics
        total_feedback = len(feedback_data)
        sentiments = [f.get("analysis", {}).get("sentiment", "neutral") for f in feedback_data]
        categories = [f.get("analysis", {}).get("category", "GENERAL") for f in feedback_data]
        
        sentiment_counts = {
            "positive": sentiments.count("positive"),
            "negative": sentiments.count("negative"),
            "neutral": sentiments.count("neutral")
        }
        
        category_counts = {}
        for cat in categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Sample feedback texts
        sample_feedback = [f["feedback_text"] for f in feedback_data[:8]]  # Reduced for Gemini
        
        prompt = f"""
        Generate a comprehensive feedback summary report for {HACKATHON_NAME} (ID: {hackathon_id}).
        
        Statistics:
        - Total feedback submissions: {total_feedback}
        - Sentiment distribution: {sentiment_counts}
        - Category distribution: {category_counts}
        
        Sample feedback:
        {chr(10).join(sample_feedback)}
        
        Create a professional report including:
        1. Executive Summary
        2. Key Findings
        3. Participant Expectations
        4. Areas of Concern
        5. Recommendations for Organizers
        6. Conclusion
        
        Format as markdown with clear sections and bullet points.
        """
        
        # Configure generation
        generation_config = genai.types.GenerationConfig(
            temperature=0.4,
            max_output_tokens=2000,
        )
        
        # Generate response
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=generation_config
        )
        
        report = response.text
        logger.info("Gemini summary report generated")
        return report
        
    except Exception as e:
        logger.error(f"Gemini summary report generation failed: {e}")
        return generate_fallback_report(hackathon_id, len(feedback_data) if feedback_data else 0)

def generate_fallback_response(analysis_results: Dict) -> str:
    """Generate fallback response when AI is unavailable"""
    sentiment = analysis_results.get("sentiment", "neutral")
    
    if sentiment == "positive":
        return (
            f"🎉 Thank you for your enthusiastic feedback about {HACKATHON_NAME}! "
            f"Your excitement is contagious and helps us create an amazing event. "
            f"We're working hard to make sure all your expectations are met. "
            f"Can't wait to see what you'll build! 🚀"
        )
    elif sentiment == "negative":
        return (
            f"🤔 Thank you for your honest feedback about {HACKATHON_NAME}. "
            f"Your concerns are important to us and will help us improve the event. "
            f"We're committed to addressing these issues and creating a great experience for everyone. "
            f"Looking forward to exceeding your expectations! 💪"
        )
    else:
        return (
            f"💭 Thanks for sharing your thoughts about {HACKATHON_NAME}! "
            f"Your input is valuable and helps us understand what participants are looking for. "
            f"We're excited to create an event that meets everyone's needs. "
            f"See you at the hackathon! ✨"
        )

def generate_fallback_report(hackathon_id: str, feedback_count: int) -> str:
    """Generate fallback report when AI is unavailable"""
    return f"""
# {HACKATHON_NAME} Feedback Summary Report

## Executive Summary
This report summarizes {feedback_count} feedback submissions collected for {HACKATHON_NAME} (ID: {hackathon_id}).

## Key Statistics
- Total feedback submissions: {feedback_count}
- Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Status
Detailed AI analysis is currently unavailable. Please review individual feedback submissions for specific insights.

## Next Steps
1. Review individual feedback entries
2. Identify common themes manually
3. Address any urgent concerns raised by participants
4. Use insights to improve the hackathon experience

---
*Report generated by Hackathon Feedback System*
"""

# Testing functions
async def test_ai_functions():
    """Test AI functions with sample data"""
    if not GOOGLE_API_KEY:
        print("❌ Google API key not configured - skipping AI tests")
        return
    
    sample_feedback = "I'm really excited about this hackathon! I hope to learn about machine learning and build something with APIs. I'm a bit worried about finding a good team though."
    
    print("Testing Gemini AI functions...")
    
    # Test analysis
    try:
        analysis = await ai_analyze_feedback(sample_feedback)
        print(f"✅ Analysis: {analysis}")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
    
    # Test response generation
    try:
        response = await ai_generate_response(sample_feedback, {"sentiment": "positive", "category": "EXPECTATIONS"})
        print(f"✅ Response: {response[:100]}...")
    except Exception as e:
        print(f"❌ Response generation failed: {e}")
    
    # Test categorization
    try:
        category = await ai_categorize_feedback(sample_feedback)
        print(f"✅ Category: {category}")
    except Exception as e:
        print(f"❌ Categorization failed: {e}")
    
    # Test spam detection
    try:
        is_spam = await ai_detect_spam("spam test asdf qwerty")
        print(f"✅ Spam Detection: {'Spam detected' if is_spam else 'Not spam'}")
    except Exception as e:
        print(f"❌ Spam detection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai_functions())