# config.py
"""
Configuration file for Hackathon Feedback Collection Agent
AWS-ready production configuration
"""

import os
from datetime import datetime

# Hackathon Event Settings
HACKATHON_ID = "HACK2024"  # Change for different events
HACKATHON_NAME = "TechHack 2024"
HACKATHON_START_DATE = "2024-12-01"  # YYYY-MM-DD format
HACKATHON_END_DATE = "2024-12-03"   # YYYY-MM-DD format

# Agent Settings
AGENT_NAME = "hackathon-feedback"
AGENT_SEED = "hackathon_feedback_agent_seed_2024"
AGENT_DESCRIPTION = "Share your hackathon expectations and help us improve!"

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# DynamoDB Settings
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "hackathon-feedback")
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT")  # For local development

# S3 Settings for data backup
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "hackathon-feedback-data")
S3_BACKUP_PREFIX = "feedback-backups/"

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.7

# Feedback Collection Settings
MIN_FEEDBACK_LENGTH = 20  # Minimum characters for valid feedback
MAX_FEEDBACK_LENGTH = 1000  # Maximum characters
FEEDBACK_TIMEOUT = 30  # Seconds to wait for AI processing

# Rate Limiting Settings
MAX_REQUESTS_PER_USER = 3  # Allow multiple feedback submissions
RATE_LIMIT_WINDOW_HOURS = 24
ENABLE_TIME_RESTRICTIONS = False  # Set to True to only allow during hackathon

# AI Feature Flags
USE_AI_ANALYSIS = True  # Use AI for feedback analysis
USE_AI_RESPONSES = True   # Generate personalized AI responses
USE_AI_SENTIMENT = True  # Analyze sentiment of feedback
USE_AI_CATEGORIZATION = True  # Categorize feedback automatically

# Security Settings
ENABLE_SPAM_PROTECTION = True
BLOCKED_WORDS = ["spam", "test123", "asdf"]
TRUSTED_DOMAINS = []  # Trusted email domains

# Logging and Monitoring
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENABLE_ANALYTICS = True
ANALYTICS_FILE = "hackathon_analytics.json"

# CloudWatch Settings
CLOUDWATCH_LOG_GROUP = "/aws/lambda/hackathon-feedback"
CLOUDWATCH_METRICS_NAMESPACE = "HackathonFeedback"

# Environment-specific overrides
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "development":
    LOG_LEVEL = "DEBUG"
    HACKATHON_ID = "DEV24"
    
elif ENVIRONMENT == "staging":
    HACKATHON_ID = "STAGE24"
    ENABLE_TIME_RESTRICTIONS = False
    
elif ENVIRONMENT == "production":
    LOG_LEVEL = "WARNING"
    ENABLE_TIME_RESTRICTIONS = True

# Feedback Categories
FEEDBACK_CATEGORIES = {
    "EXPECTATIONS": "Event expectations and goals",
    "LOGISTICS": "Venue, food, accommodation feedback", 
    "TECHNICAL": "Technical infrastructure and tools",
    "NETWORKING": "Networking and collaboration opportunities",
    "LEARNING": "Learning and skill development expectations",
    "GENERAL": "General comments and suggestions"
}

# Helper functions
def is_hackathon_active() -> bool:
    """Check if the hackathon is currently active"""
    if not HACKATHON_START_DATE or not HACKATHON_END_DATE:
        return True
    
    try:
        start = datetime.strptime(HACKATHON_START_DATE, "%Y-%m-%d").date()
        end = datetime.strptime(HACKATHON_END_DATE, "%Y-%m-%d").date()
        today = datetime.now().date()
        return start <= today <= end
    except ValueError:
        return True

def get_aws_config() -> dict:
    """Get AWS configuration for services"""
    config = {
        "region_name": AWS_REGION
    }
    
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        config.update({
            "aws_access_key_id": AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": AWS_SECRET_ACCESS_KEY
        })
    
    return config

# Validation
if __name__ == "__main__":
    print(f"Configuration for {HACKATHON_NAME}")
    print(f"Hackathon ID: {HACKATHON_ID}")
    print(f"Environment: {ENVIRONMENT}")
    print(f"AWS Region: {AWS_REGION}")
    print(f"DynamoDB Table: {DYNAMODB_TABLE_NAME}")
    print(f"S3 Bucket: {S3_BUCKET_NAME}")
    print("\nConfiguration loaded successfully! ✅")