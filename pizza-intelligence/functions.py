# functions.py
from uagents import Model
from datetime import datetime
import hashlib
import random
from typing import Tuple

class PizzaRequest(Model):
    story_rating: int  # 1-10 rating of the story quality

class PizzaResponse(Model):
    coupon_code: str
    coupon_tier: str
    message: str

# Coupon tiers based on story rating
COUPON_TIERS = {
    "PREMIUM": {"min_rating": 8, "size": "LARGE", "prefix": "PREMIUM"},
    "STANDARD": {"min_rating": 6, "size": "MEDIUM", "prefix": "STANDARD"}, 
    "BASIC": {"min_rating": 1, "size": "REGULAR", "prefix": "BASIC"}
}

# Conference identifier - change this for different events
CONFERENCE_ID = "CONF24"

def generate_coupon_code(user_identifier: str, story_rating: int, use_random: bool = False) -> Tuple[str, str]:
    """
    Generate a unique coupon code based on user and story rating
    Returns: (coupon_code, coupon_tier)
    
    Args:
        user_identifier: User's wallet address or identifier
        story_rating: Rating of the user's story (1-10)
        use_random: If True, use random code. If False, use deterministic hash
    """
    # Determine tier based on rating
    if story_rating >= 8:
        tier = "PREMIUM"
    elif story_rating >= 6:
        tier = "STANDARD"
    else:
        tier = "BASIC"
    
    if use_random:
        # Option 1: Completely Random
        import secrets
        random_part = secrets.token_hex(4).upper()  # 8 random characters
        timestamp = datetime.now().strftime("%H%M")
        coupon_code = f"PIZZA-{CONFERENCE_ID}-{tier}-{random_part}-{timestamp}"
    else:
        # Option 2: Deterministic (current approach)
        user_hash = hashlib.sha256(user_identifier.encode()).hexdigest()[:6].upper()
        timestamp = datetime.now().strftime("%H%M")
        coupon_code = f"PIZZA-{CONFERENCE_ID}-{tier}-{user_hash}-{timestamp}"
    
    return coupon_code, tier

def evaluate_story_quality(story: str) -> int:
    """
    Evaluate story quality on a scale of 1-10
    This is a fallback function in case AI evaluation fails
    """
    if not story or len(story.strip()) < 10:
        return 1
    
    story_lower = story.lower()
    score = 3  # Base score
    
    # Length bonus
    if len(story) > 100:
        score += 1
    if len(story) > 200:
        score += 1
        
    # Creativity indicators
    pizza_words = ["pizza", "cheese", "pepperoni", "crust", "slice", "topping", "sauce"]
    creative_words = ["amazing", "incredible", "adventure", "story", "funny", "crazy", "epic"]
    emotion_words = ["love", "hate", "happy", "sad", "excited", "disappointed", "surprised"]
    
    # Pizza relevance
    pizza_mentions = sum(1 for word in pizza_words if word in story_lower)
    if pizza_mentions >= 2:
        score += 1
    if pizza_mentions >= 4:
        score += 1
        
    # Creativity bonus
    creative_mentions = sum(1 for word in creative_words if word in story_lower)
    if creative_mentions >= 1:
        score += 1
    if creative_mentions >= 3:
        score += 1
        
    # Emotion bonus
    emotion_mentions = sum(1 for word in emotion_words if word in story_lower)
    if emotion_mentions >= 1:
        score += 1
        
    # Sentence structure bonus (multiple sentences)
    sentences = story.count('.') + story.count('!') + story.count('?')
    if sentences >= 2:
        score += 1
        
    # Cap the score
    return min(10, max(1, score))

def get_coupon_description(tier: str) -> str:
    """Get human-readable description of coupon tier"""
    descriptions = {
        "PREMIUM": "🍕 LARGE pizza with premium toppings",
        "STANDARD": "🍕 MEDIUM pizza with your choice of toppings", 
        "BASIC": "🍕 REGULAR pizza - still delicious!"
    }
    return descriptions.get(tier, "🍕 Pizza!")

def validate_coupon_format(coupon_code: str) -> bool:
    """
    Validate that a coupon code follows the expected format
    Format: PIZZA-CONF24-TIER-HASH-TIME
    """
    if not coupon_code:
        return False
        
    parts = coupon_code.split('-')
    if len(parts) != 5:
        return False
        
    prefix, conf_id, tier, user_hash, timestamp = parts
    
    return (
        prefix == "PIZZA" and
        conf_id == CONFERENCE_ID and
        tier in ["PREMIUM", "STANDARD", "BASIC"] and
        len(user_hash) == 6 and
        user_hash.isalnum() and
        len(timestamp) == 4 and
        timestamp.isdigit()
    )

# Vendor helper functions
def extract_coupon_info(coupon_code: str) -> dict:
    """
    Extract information from coupon code for vendors
    Returns dict with tier, user_hash, timestamp
    """
    if not validate_coupon_format(coupon_code):
        return {"valid": False, "error": "Invalid coupon format"}
    
    parts = coupon_code.split('-')
    _, conf_id, tier, user_hash, timestamp = parts
    
    # Convert timestamp to readable time
    try:
        hour = int(timestamp[:2])
        minute = int(timestamp[2:])
        time_issued = f"{hour:02d}:{minute:02d}"
    except:
        time_issued = "Unknown"
    
    return {
        "valid": True,
        "tier": tier,
        "conference": conf_id,
        "user_hash": user_hash,
        "time_issued": time_issued,
        "pizza_size": COUPON_TIERS[tier]["size"],
        "description": get_coupon_description(tier)
    }

# Analytics and reporting functions
def get_coupon_stats() -> dict:
    """Return coupon generation statistics (for admin use)"""
    # In a real implementation, this would query a database
    # For now, return placeholder data
    return {
        "total_issued": 0,
        "by_tier": {"PREMIUM": 0, "STANDARD": 0, "BASIC": 0},
        "by_hour": {},
        "redemption_rate": 0.0
    }

def is_business_hours() -> bool:
    """Check if it's during conference hours (optional restriction)"""
    current_hour = datetime.now().hour
    # Conference runs 9 AM to 6 PM
    return 9 <= current_hour <= 18

# Example usage and testing functions
def test_coupon_generation():
    """Test function to verify coupon generation works"""
    test_users = ["user1", "user2@example.com", "wallet0x123"]
    test_ratings = [3, 7, 9]
    
    print("Testing coupon generation:")
    for user in test_users:
        for rating in test_ratings:
            code, tier = generate_coupon_code(user, rating)
            info = extract_coupon_info(code)
            print(f"User: {user[:10]}, Rating: {rating}, Code: {code}, Tier: {tier}")
            print(f"  Valid: {info['valid']}, Size: {info.get('pizza_size', 'N/A')}")
            print()

if __name__ == "__main__":
    # Run tests when script is executed directly
    test_coupon_generation()
    
    # Test story evaluation
    test_stories = [
        "pizza",
        "I love pizza so much! It's the best food ever created.",
        "Once upon a time, I was walking down the street feeling really hungry. Then I saw this amazing pizza place with the most incredible smell wafting out. I went in and ordered the most epic pepperoni pizza with extra cheese. It was a life-changing experience that made me believe in the power of melted cheese and perfectly crispy crust!"
    ]
    
    print("Testing story evaluation:")
    for i, story in enumerate(test_stories):
        rating = evaluate_story_quality(story)
        print(f"Story {i+1} (length: {len(story)}): Rating {rating}/10")
        print(f"  Preview: {story[:50]}...")
        print()