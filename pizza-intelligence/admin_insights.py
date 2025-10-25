#!/usr/bin/env python3
"""
Pizza Intelligence Admin Insights - Command Line Version
Quick insights and filtering for pizza agent responses
"""

import json
import argparse
from datetime import datetime
from collections import Counter
from config import ANALYTICS_FILE

def load_data():
    """Load analytics data"""
    try:
        with open(ANALYTICS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ No analytics data found. Run the agent first to collect data.")
        return None
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None

def filter_stories(stories, min_rating=None, max_rating=None, tier=None, min_length=None):
    """Filter stories based on criteria"""
    filtered = stories
    
    if min_rating is not None:
        filtered = [s for s in filtered if s.get('rating', 0) >= min_rating]
    
    if max_rating is not None:
        filtered = [s for s in filtered if s.get('rating', 0) <= max_rating]
    
    if tier:
        filtered = [s for s in filtered if s.get('tier', '').upper() == tier.upper()]
    
    if min_length is not None:
        filtered = [s for s in filtered if s.get('story_length', 0) >= min_length]
    
    return filtered

def show_summary(data, stories):
    """Show summary statistics"""
    print("🍕 Pizza Intelligence Summary")
    print("=" * 50)
    print(f"📊 Total Requests: {data.get('total_requests', 0)}")
    print(f"🎫 Total Coupons: {data.get('total_coupons_issued', 0)}")
    print(f"📝 Total Stories: {len(stories)}")
    
    if stories:
        ratings = [s.get('rating', 0) for s in stories]
        avg_rating = sum(ratings) / len(ratings)
        print(f"⭐ Average Rating: {avg_rating:.1f}/10")
        
        lengths = [s.get('story_length', 0) for s in stories]
        avg_length = sum(lengths) / len(lengths)
        print(f"📏 Average Length: {avg_length:.0f} characters")
        
        # Tier distribution
        tiers = [s.get('tier', 'UNKNOWN') for s in stories]
        tier_counts = Counter(tiers)
        print(f"\n🎫 Coupon Tiers:")
        for tier, count in tier_counts.items():
            print(f"  {tier}: {count}")
        
        # Rating distribution
        rating_counts = Counter(ratings)
        print(f"\n⭐ Rating Distribution:")
        for rating in sorted(rating_counts.keys()):
            count = rating_counts[rating]
            bar = "█" * (count * 20 // max(rating_counts.values()))
            print(f"  {rating}: {count:2d} {bar}")

def show_insights(stories):
    """Show detailed insights"""
    if not stories:
        print("No stories to analyze.")
        return
    
    print("\n💡 Insights")
    print("=" * 30)
    
    # High vs low rated stories
    high_rated = [s for s in stories if s.get('rating', 0) >= 8]
    low_rated = [s for s in stories if s.get('rating', 0) <= 3]
    
    print(f"🔥 High Rated (8-10): {len(high_rated)} stories")
    print(f"❄️  Low Rated (1-3): {len(low_rated)} stories")
    
    # Length analysis
    if high_rated and low_rated:
        high_avg_length = sum(s.get('story_length', 0) for s in high_rated) / len(high_rated)
        low_avg_length = sum(s.get('story_length', 0) for s in low_rated) / len(low_rated)
        
        print(f"\n📏 Length Analysis:")
        print(f"  High rated avg length: {high_avg_length:.0f} chars")
        print(f"  Low rated avg length: {low_avg_length:.0f} chars")
        
        if high_avg_length > low_avg_length * 1.5:
            print("  💡 Insight: Longer stories tend to get higher ratings")
        elif low_avg_length > high_avg_length * 1.5:
            print("  💡 Insight: Shorter stories tend to get higher ratings")
    
    # Common words in high-rated stories
    if high_rated:
        all_text = ' '.join([s.get('story', '') for s in high_rated]).lower()
        words = all_text.split()
        # Filter common words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
        filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
        word_counts = Counter(filtered_words)
        
        print(f"\n🔍 Top words in high-rated stories:")
        for word, count in word_counts.most_common(5):
            print(f"  {word}: {count}")

def show_stories(stories, limit=None):
    """Show individual stories"""
    if not stories:
        print("No stories match the criteria.")
        return
    
    print(f"\n📚 Stories ({len(stories)} total)")
    print("=" * 50)
    
    display_stories = stories[:limit] if limit else stories
    
    for i, story in enumerate(display_stories, 1):
        rating = story.get('rating', 0)
        tier = story.get('tier', 'UNKNOWN')
        length = story.get('story_length', 0)
        timestamp = story.get('timestamp', '')[:19]  # Remove microseconds
        
        print(f"\n📖 Story #{i}")
        print(f"⭐ Rating: {rating}/10 | 🎫 Tier: {tier} | 📏 Length: {length} chars | 🕐 {timestamp}")
        print("-" * 40)
        print(story.get('story', 'No story text'))
        print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description='Pizza Intelligence Admin Insights')
    parser.add_argument('--min-rating', type=int, help='Minimum rating filter (1-10)')
    parser.add_argument('--max-rating', type=int, help='Maximum rating filter (1-10)')
    parser.add_argument('--tier', choices=['BASIC', 'STANDARD', 'PREMIUM'], help='Filter by coupon tier')
    parser.add_argument('--min-length', type=int, help='Minimum story length in characters')
    parser.add_argument('--show-stories', action='store_true', help='Show individual stories')
    parser.add_argument('--limit', type=int, default=10, help='Limit number of stories to show')
    parser.add_argument('--insights', action='store_true', help='Show detailed insights')
    
    args = parser.parse_args()
    
    # Load data
    data = load_data()
    if not data:
        return
    
    # Get stories
    stories = data.get('stories', [])
    
    # Apply filters
    filtered_stories = filter_stories(
        stories,
        min_rating=args.min_rating,
        max_rating=args.max_rating,
        tier=args.tier,
        min_length=args.min_length
    )
    
    # Show results
    show_summary(data, filtered_stories)
    
    if args.insights:
        show_insights(filtered_stories)
    
    if args.show_stories:
        show_stories(filtered_stories, limit=args.limit)
    
    # Show filter info if any filters applied
    if any([args.min_rating, args.max_rating, args.tier, args.min_length]):
        print(f"\n🔍 Filters applied: {len(filtered_stories)}/{len(stories)} stories shown")

if __name__ == "__main__":
    main()