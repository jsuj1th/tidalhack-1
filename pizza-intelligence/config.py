# config.py
"""
Configuration file for Pizza Intelligence
Modify these settings for different conferences or deployments
"""

import os
from datetime import datetime

# Conference Settings
CONFERENCE_ID = "TamuHacks12"  # Change for different events
CONFERENCE_NAME = "TamuHacks 12.0"
CONFERENCE_START_DATE = "2025-10-24"  # YYYY-MM-DD format
CONFERENCE_END_DATE = "2025-10-26"   # YYYY-MM-DD format

# Agent Settings
AGENT_NAME = "fetch-pizza"
AGENT_SEED = "pizza_coupon_agent_seed_2024_v2"  # Change to reset agent identity
AGENT_DESCRIPTION = "Intelligent pizza distribution system - get your free pizza coupon by sharing a pizza story!"

# AI Agent Configuration (for story evaluation)
AI_AGENT_ADDRESS = "agent1qtlpfshtlcxekgrfcpmv7m9zpajuwu7d5jfyachvpa4u3dkt6k0uwwp2lct"

# Coupon Settings
COUPON_TIERS = {
    "PREMIUM": {
        "min_rating": 8,
        "size": "LARGE",
        "description": "🍕 LARGE pizza with premium toppings",
        "emoji": "🏆"
    },
    "STANDARD": {
        "min_rating": 6,
        "size": "MEDIUM", 
        "description": "🍕 MEDIUM pizza with your choice of toppings",
        "emoji": "👍"
    },
    "BASIC": {
        "min_rating": 1,
        "size": "REGULAR",
        "description": "🍕 REGULAR pizza - still delicious!",
        "emoji": "🙂"
    }
}

# Rate Limiting Settings
MAX_REQUESTS_PER_USER = 1  # One coupon per user
RATE_LIMIT_WINDOW_HOURS = 24
ENABLE_TIME_RESTRICTIONS = False  # Set to True to only allow during conference hours
CONFERENCE_START_HOUR = 9  # 9 AM
CONFERENCE_END_HOUR = 18   # 6 PM

# Story Evaluation Settings
MIN_STORY_LENGTH = 10  # Minimum characters for a valid story
STORY_EVALUATION_TIMEOUT = 30  # Seconds to wait for AI evaluation
FALLBACK_TO_RULE_BASED = True  # Use rule-based evaluation if AI fails

# Vendor Integration Settings
VENDOR_VALIDATION_URL = None  # URL for vendors to validate coupons (optional)
ENABLE_REDEMPTION_TRACKING = False  # Track when coupons are redeemed
REDEMPTION_WEBHOOK_URL = None  # Webhook to call when coupon is redeemed

# Logging and Monitoring
LOG_LEVEL = "INFO"
LOG_USER_STORIES = False  # Set to True to log stories for analysis (privacy consideration)
ENABLE_ANALYTICS = True
ANALYTICS_FILE = "pizza_agent_analytics.json"

# AI Feature Flags
USE_RANDOM_CODES = True  # Use random codes for truly unique coupons every time
USE_AI_EVALUATION = True  # Use AI for story evaluation
USE_AI_RESPONSES = True   # Generate personalized AI responses
USE_AI_MODERATION = True  # Use AI for spam/abuse detection
USE_AI_PROMPTS = True     # Generate dynamic prompts with AI

# LLM Provider Selection
USE_GEMINI = True          # Use Gemini for intent detection and unique messages
USE_ASI1 = False           # Use ASI1 for story evaluation (disabled in favor of Gemini)
GEMINI_MODEL = "models/gemini-2.5-flash"  # Gemini model to use (most efficient)
GEMINI_TEMPERATURE = 0.9   # Creativity level (0.0-2.0, higher = more creative)

# Security Settings
ENABLE_SPAM_PROTECTION = True
MAX_MESSAGE_LENGTH = 1000  # Characters
BLOCKED_WORDS = []  # Add words to block if needed
TRUSTED_DOMAINS = []  # Trusted email domains (if collecting emails)

# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "development":
    LOG_LEVEL = "DEBUG"
    LOG_USER_STORIES = True
    CONFERENCE_ID = "DEV24"
    
elif os.getenv("ENVIRONMENT") == "staging":
    CONFERENCE_ID = "STAGE24"
    ENABLE_TIME_RESTRICTIONS = False
    
elif os.getenv("ENVIRONMENT") == "production":
    LOG_LEVEL = "WARNING"
    LOG_USER_STORIES = False
    ENABLE_TIME_RESTRICTIONS = True

# Helper functions
def is_conference_active() -> bool:
    """Check if the conference is currently active"""
    if not CONFERENCE_START_DATE or not CONFERENCE_END_DATE:
        return True
    
    try:
        start = datetime.strptime(CONFERENCE_START_DATE, "%Y-%m-%d").date()
        end = datetime.strptime(CONFERENCE_END_DATE, "%Y-%m-%d").date()
        today = datetime.now().date()
        return start <= today <= end
    except ValueError:
        return True

def is_conference_hours() -> bool:
    """Check if it's during conference hours"""
    if not ENABLE_TIME_RESTRICTIONS:
        return True
    
    current_hour = datetime.now().hour
    return CONFERENCE_START_HOUR <= current_hour <= CONFERENCE_END_HOUR

def get_conference_status() -> str:
    """Get human-readable conference status"""
    if not is_conference_active():
        return "Conference is not currently active"
    elif not is_conference_hours():
        return f"Conference hours are {CONFERENCE_START_HOUR}:00 - {CONFERENCE_END_HOUR}:00"
    else:
        return "Conference is active"

# Validation
if __name__ == "__main__":
    print(f"Configuration for {CONFERENCE_NAME}")
    print(f"Conference ID: {CONFERENCE_ID}")
    print(f"Agent Name: {AGENT_NAME}")
    print(f"Conference Status: {get_conference_status()}")
    print(f"Time Restrictions Enabled: {ENABLE_TIME_RESTRICTIONS}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'default')}")
    
    # Validate coupon tiers
    for tier, config in COUPON_TIERS.items():
        print(f"Tier {tier}: {config['description']}")
        
    print("\nConfiguration loaded successfully! ✅")