# utils.py
"""
Utility functions for the Pizza Coupon Agent
Includes testing, monitoring, and vendor tools
"""

import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib
import re
from functions import validate_coupon_format, extract_coupon_info
from config import CONFERENCE_ID, COUPON_TIERS

class PizzaAgentAnalytics:
    """Analytics tracker for the pizza agent"""
    
    def __init__(self, analytics_file: str = "pizza_analytics.json"):
        self.analytics_file = analytics_file
        self.data = self.load_analytics()
    
    def load_analytics(self) -> dict:
        """Load existing analytics data"""
        try:
            with open(self.analytics_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "total_requests": 0,
                "total_coupons_issued": 0,
                "coupons_by_tier": {"BASIC": 0, "STANDARD": 0, "PREMIUM": 0},
                "hourly_stats": {},
                "daily_stats": {},
                "average_story_length": 0,
                "story_ratings": [],
                "user_interactions": {},
                "start_time": datetime.now().isoformat()
            }
    
    def save_analytics(self):
        """Save analytics data to file"""
        try:
            with open(self.analytics_file, 'w') as f:
                json.dump(self.data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving analytics: {e}")
    
    def record_request(self, user_id: str):
        """Record a new request from user"""
        self.data["total_requests"] += 1
        hour_key = datetime.now().strftime("%Y-%m-%d %H:00")
        day_key = datetime.now().strftime("%Y-%m-%d")
        
        self.data["hourly_stats"][hour_key] = self.data["hourly_stats"].get(hour_key, 0) + 1
        self.data["daily_stats"][day_key] = self.data["daily_stats"].get(day_key, 0) + 1
        
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
        self.data["user_interactions"][user_hash] = self.data["user_interactions"].get(user_hash, 0) + 1
        
        self.save_analytics()
    
    def record_coupon_issued(self, user_id: str, tier: str, story_rating: int, story_length: int, user_email: str = ""):
        """Record a coupon being issued"""
        self.data["total_coupons_issued"] += 1
        self.data["coupons_by_tier"][tier] += 1
        self.data["story_ratings"].append(story_rating)
        
        # Update average story length
        current_avg = self.data.get("average_story_length", 0)
        total_stories = len(self.data["story_ratings"])
        self.data["average_story_length"] = ((current_avg * (total_stories - 1)) + story_length) / total_stories
        
        # Store email data (full email addresses)
        if user_email:
            if "user_emails" not in self.data:
                self.data["user_emails"] = {}
            user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
            # Store full email address and domain for analytics
            email_domain = user_email.split('@')[1] if '@' in user_email else "unknown"
            self.data["user_emails"][user_hash] = {
                "email": user_email,  # Full email address
                "domain": email_domain,
                "coupon_tier": tier,
                "story_rating": story_rating,
                "timestamp": datetime.now().isoformat()
            }
        
        self.save_analytics()
    
    def get_summary_stats(self) -> dict:
        """Get summary statistics"""
        story_ratings = self.data["story_ratings"]
        return {
            "total_requests": self.data["total_requests"],
            "total_coupons_issued": self.data["total_coupons_issued"],
            "conversion_rate": self.data["total_coupons_issued"] / max(1, self.data["total_requests"]),
            "coupons_by_tier": self.data["coupons_by_tier"],
            "average_story_rating": sum(story_ratings) / len(story_ratings) if story_ratings else 0,
            "average_story_length": self.data["average_story_length"],
            "unique_users": len(self.data["user_interactions"]),
            "top_hours": sorted(self.data["hourly_stats"].items(), key=lambda x: x[1], reverse=True)[:5]
        }

class VendorTools:
    """Tools for pizza vendors to validate and manage coupons"""
    
    def __init__(self):
        self.redeemed_coupons = set()
        self.redemption_log = []
    
    def validate_coupon(self, coupon_code: str) -> dict:
        """Validate a coupon code for vendors"""
        # Basic format validation
        if not validate_coupon_format(coupon_code):
            return {
                "valid": False,
                "reason": "Invalid coupon format",
                "action": "Reject - not a valid pizza coupon"
            }
        
        # Check if already redeemed
        if coupon_code in self.redeemed_coupons:
            return {
                "valid": False, 
                "reason": "Coupon already redeemed",
                "action": "Reject - this coupon has been used"
            }
        
        # Extract coupon info
        info = extract_coupon_info(coupon_code)
        if not info["valid"]:
            return {
                "valid": False,
                "reason": info.get("error", "Unknown error"),
                "action": "Reject - coupon error"
            }
        
        # All checks passed
        return {
            "valid": True,
            "tier": info["tier"],
            "pizza_size": info["pizza_size"],
            "description": info["description"],
            "issued_time": info["time_issued"],
            "action": f"Accept - Provide {info['pizza_size']} pizza"
        }
    
    def redeem_coupon(self, coupon_code: str, vendor_id: str = "unknown") -> bool:
        """Mark a coupon as redeemed"""
        validation = self.validate_coupon(coupon_code)
        if not validation["valid"]:
            return False
        
        self.redeemed_coupons.add(coupon_code)
        self.redemption_log.append({
            "coupon_code": coupon_code,
            "redeemed_at": datetime.now().isoformat(),
            "vendor_id": vendor_id,
            "tier": validation["tier"]
        })
        return True
    
    def get_redemption_stats(self) -> dict:
        """Get redemption statistics for vendors"""
        total_redeemed = len(self.redemption_log)
        tier_counts = {}
        for redemption in self.redemption_log:
            tier = redemption["tier"]
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        return {
            "total_redeemed": total_redeemed,
            "redeemed_by_tier": tier_counts,
            "redemption_rate": f"{total_redeemed} coupons redeemed",
            "last_redemption": self.redemption_log[-1]["redeemed_at"] if self.redemption_log else None
        }
    
    def export_redemption_log(self, filename: str = "redemptions.csv"):
        """Export redemption log to CSV"""
        if not self.redemption_log:
            print("No redemptions to export")
            return
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ["coupon_code", "redeemed_at", "vendor_id", "tier"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.redemption_log)
        print(f"Exported {len(self.redemption_log)} redemptions to {filename}")

class AgentTester:
    """Testing utilities for the pizza agent"""
    
    @staticmethod
    def generate_test_stories() -> List[dict]:
        """Generate test stories with expected ratings"""
        return [
            {
                "story": "pizza",
                "expected_rating_range": (1, 3),
                "description": "Minimal story"
            },
            {
                "story": "I like pizza. It's good.",
                "expected_rating_range": (2, 4),
                "description": "Short story"
            },
            {
                "story": "Once I ordered pizza and it was really good! The cheese was melted perfectly and the crust was crispy. I was very happy with my meal.",
                "expected_rating_range": (4, 7),
                "description": "Medium quality story"
            },
            {
                "story": "Last summer, I was on a road trip with my friends when we got lost in the middle of nowhere. We were starving and hadn't seen any restaurants for miles. Just when we were about to give up hope, we spotted this tiny, family-owned pizza place that looked like it was straight out of the 1950s. The owner, an elderly Italian man named Giuseppe, welcomed us with open arms and told us he'd make us something special. He disappeared into the kitchen and came back with the most incredible pizza I've ever tasted - homemade dough, fresh mozzarella that he made that morning, tomatoes from his garden, and basil that smelled like heaven. That pizza didn't just feed our bodies, it fed our souls and reminded us why food brings people together. To this day, whenever I taste pizza, I think of Giuseppe and that magical moment when we were lost but found exactly what we needed.",
                "expected_rating_range": (8, 10),
                "description": "High quality, detailed story with emotion"
            }
        ]
    
    @staticmethod
    def test_story_evaluation():
        """Test the story evaluation function"""
        from functions import evaluate_story_quality
        
        test_stories = AgentTester.generate_test_stories()
        print("Testing Story Evaluation:")
        print("=" * 50)
        
        for i, test_case in enumerate(test_stories):
            story = test_case["story"]
            expected_min, expected_max = test_case["expected_rating_range"]
            actual_rating = evaluate_story_quality(story)
            
            print(f"\nTest Case {i+1}: {test_case['description']}")
            print(f"Story length: {len(story)} characters")
            print(f"Story preview: {story[:100]}...")
            print(f"Expected rating: {expected_min}-{expected_max}")
            print(f"Actual rating: {actual_rating}")
            print(f"✅ Pass" if expected_min <= actual_rating <= expected_max else f"❌ Fail")
    
    @staticmethod
    def test_coupon_generation():
        """Test coupon code generation"""
        from functions import generate_coupon_code
        
        test_users = ["user1", "user2@test.com", "0x123abc"]
        test_ratings = [2, 6, 9]
        
        print("Testing Coupon Generation:")
        print("=" * 50)
        
        for user in test_users:
            for rating in test_ratings:
                coupon_code, tier = generate_coupon_code(user, rating)
                info = extract_coupon_info(coupon_code)
                
                print(f"\nUser: {user}")
                print(f"Rating: {rating}")
                print(f"Generated: {coupon_code}")
                print(f"Tier: {tier}")
                print(f"Valid: {info['valid']}")
                print(f"Pizza Size: {info.get('pizza_size', 'N/A')}")

def run_comprehensive_test():
    """Run all tests"""
    print("🍕 Pizza Agent Comprehensive Test Suite")
    print("=" * 60)
    
    # Test story evaluation
    AgentTester.test_story_evaluation()
    
    print("\n" + "=" * 60)
    
    # Test coupon generation  
    AgentTester.test_coupon_generation()
    
    print("\n" + "=" * 60)
    
    # Test vendor tools
    print("Testing Vendor Tools:")
    vendor = VendorTools()
    
    # Generate a test coupon
    from functions import generate_coupon_code
    test_coupon, _ = generate_coupon_code("testuser", 7)
    
    # Validate it
    validation = vendor.validate_coupon(test_coupon)
    print(f"Coupon validation: {validation}")
    
    # Redeem it
    redemption = vendor.redeem_coupon(test_coupon, "vendor_1")
    print(f"Redemption successful: {redemption}")
    
    # Try to redeem again (should fail)
    redemption2 = vendor.redeem_coupon(test_coupon, "vendor_1")
    print(f"Second redemption (should fail): {redemption2}")
    
    # Get stats
    stats = vendor.get_redemption_stats()
    print(f"Redemption stats: {stats}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    run_comprehensive_test()