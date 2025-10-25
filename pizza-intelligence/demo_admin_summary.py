#!/usr/bin/env python3
"""
Demo script showing the complete admin summary functionality
"""

import json
import requests
import time
from utils import PizzaAgentAnalytics

def demo_admin_summary():
    """Demonstrate the admin summary feature"""
    print("🍕 Pizza Agent Admin Summary Demo")
    print("=" * 60)
    
    # 1. Show current analytics state
    print("\n📊 Step 1: Current Analytics State")
    analytics = PizzaAgentAnalytics("pizza_agent_analytics.json")
    current_stats = analytics.get_summary_stats()
    
    print(f"• Total Requests: {current_stats['total_requests']}")
    print(f"• Total Coupons: {current_stats['total_coupons_issued']}")
    print(f"• Stories Collected: {len(analytics.data.get('stories', []))}")
    
    # 2. Add some demo stories if needed
    if len(analytics.data.get('stories', [])) < 5:
        print("\n📝 Step 2: Adding Demo Stories for Better Analysis")
        
        demo_stories = [
            {
                "story": "Last night during our hackathon, I was debugging a really tricky algorithm when my teammate surprised me with a slice of pepperoni pizza. The moment I took that first bite, something clicked in my brain and I finally saw the solution! That pizza literally powered my breakthrough moment. We ended up winning the competition thanks to that late-night pizza fuel! 🍕💻",
                "rating": 9,
                "tier": "PREMIUM",
                "user_id": "demo_hacker_1"
            },
            {
                "story": "Pizza is okay I guess. Had some yesterday.",
                "rating": 2,
                "tier": "BASIC",
                "user_id": "demo_user_2"
            },
            {
                "story": "Our team ordered pizza at 2am during the hackathon and it was amazing! The cheese was perfectly melted and the crust was crispy. It gave us the energy to keep coding through the night. Pizza + coding = perfect combination for innovation!",
                "rating": 8,
                "tier": "PREMIUM", 
                "user_id": "demo_team_3"
            },
            {
                "story": "I love trying weird pizza combinations during hackathons. Last time I had pineapple and jalapeño pizza while working on my machine learning project. The sweet and spicy combo somehow helped me think more creatively about my neural network architecture. Food really does fuel innovation!",
                "rating": 7,
                "tier": "STANDARD",
                "user_id": "demo_creative_4"
            },
            {
                "story": "Pizza delivery saved our hackathon team when we were stuck on a bug for 6 hours straight. The moment we took a break to eat, we realized our mistake and fixed it in 5 minutes. Sometimes you just need pizza to clear your head and see the solution!",
                "rating": 8,
                "tier": "PREMIUM",
                "user_id": "demo_debugger_5"
            }
        ]
        
        for story_data in demo_stories:
            analytics.record_coupon_issued(
                story_data["user_id"],
                story_data["tier"],
                story_data["rating"], 
                len(story_data["story"]),
                "",  # no email for demo
                story_data["story"]
            )
            print(f"  ✅ Added {story_data['tier']} story (rating: {story_data['rating']}/10)")
    
    # 3. Generate comprehensive summary
    print("\n🔍 Step 3: Generating Comprehensive Event Summary")
    summary_data = analytics.generate_event_summary()
    
    print("\n" + "="*80)
    print("📋 ADMIN SUMMARY REPORT - PIZZA AGENT EVENT ANALYSIS")
    print("="*80)
    
    # Display summary
    print("\n📖 EXECUTIVE SUMMARY:")
    print("-" * 40)
    print(summary_data["summary"])
    
    # Display recommendations
    print("\n💡 ACTIONABLE RECOMMENDATIONS:")
    print("-" * 40)
    for i, rec in enumerate(summary_data["recommendations"], 1):
        print(f"{i:2d}. {rec}")
    
    # Display key metrics
    print("\n📊 KEY PERFORMANCE INDICATORS:")
    print("-" * 40)
    stats = summary_data["stats"]
    print(f"{'Total Event Requests:':<25} {stats['total_requests']:>8}")
    print(f"{'Coupons Issued:':<25} {stats['total_coupons_issued']:>8}")
    print(f"{'Conversion Rate:':<25} {stats['conversion_rate']:>7.1%}")
    print(f"{'Average Story Rating:':<25} {stats['average_story_rating']:>6.1f}/10")
    print(f"{'Unique Participants:':<25} {stats['unique_users']:>8}")
    print(f"{'Average Story Length:':<25} {stats['average_story_length']:>6.0f} chars")
    
    # Display coupon distribution
    print(f"\n🎫 COUPON TIER DISTRIBUTION:")
    print("-" * 40)
    tier_stats = stats['coupons_by_tier']
    total_coupons = sum(tier_stats.values())
    for tier, count in tier_stats.items():
        percentage = (count / total_coupons * 100) if total_coupons > 0 else 0
        print(f"{'  ' + tier + ' Tier:':<25} {count:>4} ({percentage:>5.1f}%)")
    
    # Display theme analysis
    if summary_data.get("theme_analysis"):
        print(f"\n🎭 PARTICIPANT ENGAGEMENT THEMES:")
        print("-" * 40)
        for theme, count in sorted(summary_data["theme_analysis"].items(), 
                                 key=lambda x: x[1], reverse=True):
            theme_name = theme.replace('_', ' ').title()
            print(f"{'  ' + theme_name + ':':<25} {count:>4} mentions")
    
    # Show story quality insights
    story_dist = summary_data.get("story_distribution", {})
    if story_dist:
        print(f"\n📈 STORY QUALITY INSIGHTS:")
        print("-" * 40)
        total_stories = sum(story_dist.values())
        print(f"{'  High Quality (8-10):':<25} {story_dist.get('high_quality', 0):>4} stories")
        print(f"{'  Medium Quality (5-7):':<25} {story_dist.get('medium_quality', 0):>4} stories")
        print(f"{'  Basic Quality (1-4):':<25} {story_dist.get('low_quality', 0):>4} stories")
        
        if story_dist.get('high_quality', 0) > story_dist.get('low_quality', 0):
            print("\n  ✅ Positive Indicator: More high-quality than low-quality stories")
        
        engagement_score = (story_dist.get('high_quality', 0) * 3 + 
                          story_dist.get('medium_quality', 0) * 2 + 
                          story_dist.get('low_quality', 0)) / (total_stories * 3) * 100
        print(f"  📊 Overall Engagement Score: {engagement_score:.1f}%")
    
    # 4. Show web interface access
    print(f"\n🌐 Step 4: Web Interface Access")
    print("-" * 40)
    print("To access this summary via web interface:")
    print("1. Run: python web_test_interface.py")
    print("2. Open: http://127.0.0.1:5005")
    print("3. Click 'Go to Admin Dashboard' or visit /admin")
    print("4. Check 'Yes, I am an authorized event administrator'")
    print("5. Click 'Generate Complete Event Analysis'")
    
    # 5. Data export info
    print(f"\n💾 Step 5: Data Export Information")
    print("-" * 40)
    print(f"Analytics data saved to: {analytics.analytics_file}")
    print(f"Total data size: {len(json.dumps(analytics.data, indent=2))} characters")
    print("Data includes: stories, ratings, timestamps, user interactions")
    
    print(f"\n✅ Demo completed successfully!")
    print("🔒 Remember: This admin feature should only be used by authorized event organizers")
    
    return summary_data

if __name__ == "__main__":
    demo_admin_summary()