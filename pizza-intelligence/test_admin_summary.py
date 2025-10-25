#!/usr/bin/env python3
"""
Test script for the admin summary functionality
"""

import json
from utils import PizzaAgentAnalytics

def test_admin_summary():
    """Test the admin summary generation"""
    print("🧪 Testing Admin Summary Generation")
    print("=" * 50)
    
    # Load existing analytics
    analytics = PizzaAgentAnalytics("pizza_agent_analytics.json")
    
    # Add some test stories if none exist
    if not analytics.data.get("stories"):
        print("📝 Adding test stories for demonstration...")
        
        test_stories = [
            {
                "story": "I had the most amazing pizza during my last hackathon! I was coding until 3am and getting really tired. Then my teammate ordered this incredible pepperoni pizza with extra cheese. The moment I took a bite, I got a burst of energy and solved the bug I'd been working on for hours! That pizza literally saved our project and we ended up winning second place. Best pizza ever! 🍕",
                "rating": 9,
                "tier": "PREMIUM",
                "user_id": "test_user_1"
            },
            {
                "story": "Pizza is good. I like cheese pizza.",
                "rating": 3,
                "tier": "BASIC", 
                "user_id": "test_user_2"
            },
            {
                "story": "During our late-night coding session, we ordered pizza to keep us going. The combination of melted cheese and crispy crust was perfect fuel for debugging. It really helped our team stay focused and productive throughout the hackathon.",
                "rating": 7,
                "tier": "STANDARD",
                "user_id": "test_user_3"
            }
        ]
        
        for story_data in test_stories:
            analytics.record_coupon_issued(
                story_data["user_id"],
                story_data["tier"], 
                story_data["rating"],
                len(story_data["story"]),
                "",  # no email
                story_data["story"]
            )
    
    # Generate summary
    print("\n📊 Generating Event Summary...")
    summary_data = analytics.generate_event_summary()
    
    print("\n" + "="*60)
    print("📋 ADMIN SUMMARY REPORT")
    print("="*60)
    
    print("\n📖 SUMMARY:")
    print(summary_data["summary"])
    
    print("\n💡 RECOMMENDATIONS:")
    for i, rec in enumerate(summary_data["recommendations"], 1):
        print(f"{i}. {rec}")
    
    print("\n📈 STATISTICS:")
    stats = summary_data["stats"]
    print(f"• Total Requests: {stats['total_requests']}")
    print(f"• Total Coupons: {stats['total_coupons_issued']}")
    print(f"• Conversion Rate: {stats['conversion_rate']:.1%}")
    print(f"• Average Rating: {stats['average_story_rating']:.1f}/10")
    print(f"• Unique Users: {stats['unique_users']}")
    
    if summary_data.get("theme_analysis"):
        print("\n🎭 THEME ANALYSIS:")
        for theme, count in summary_data["theme_analysis"].items():
            print(f"• {theme.replace('_', ' ').title()}: {count} mentions")
    
    print("\n✅ Admin summary generation completed!")
    print(f"📁 Data saved to: {analytics.analytics_file}")
    
    return summary_data

if __name__ == "__main__":
    test_admin_summary()