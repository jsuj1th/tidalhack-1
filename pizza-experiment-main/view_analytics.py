#!/usr/bin/env python3
"""
Analytics Viewer for Pizza Coupon Agent
Run this to see collected analytics data
"""

import json
import csv
from utils import PizzaAgentAnalytics
from config import ANALYTICS_FILE
from collections import Counter

def main():
    print("🍕 Pizza Agent Analytics Dashboard")
    print("=" * 50)
    
    try:
        analytics = PizzaAgentAnalytics(ANALYTICS_FILE)
        stats = analytics.get_summary_stats()
        
        print(f"📊 Total Requests: {stats['total_requests']}")
        print(f"🎫 Total Coupons Issued: {stats['total_coupons_issued']}")
        print(f"📈 Conversion Rate: {stats['conversion_rate']:.2%}")
        print(f"👥 Unique Users: {stats['unique_users']}")
        print(f"⭐ Average Story Rating: {stats['average_story_rating']:.1f}/10")
        print(f"📝 Average Story Length: {stats['average_story_length']:.0f} characters")
        
        print("\n🏆 Coupons by Tier:")
        for tier, count in stats['coupons_by_tier'].items():
            print(f"  {tier}: {count}")
        
        print("\n🕐 Top Active Hours:")
        for hour, requests in stats['top_hours'][:3]:
            print(f"  {hour}: {requests} requests")
        
        # Email analytics
        if 'user_emails' in analytics.data and analytics.data['user_emails']:
            print("\n📧 Email Analytics:")
            emails = analytics.data['user_emails']
            print(f"  Users with emails: {len(emails)}")
            
            # Show all collected emails
            print("  Collected email addresses:")
            for user_hash, data in emails.items():
                email = data.get('email', 'N/A')
                tier = data.get('coupon_tier', 'N/A')
                rating = data.get('story_rating', 'N/A')
                timestamp = data.get('timestamp', 'N/A')[:19]  # Remove microseconds
                print(f"    {email} - {tier} coupon (rating: {rating}) - {timestamp}")
            
            # Domain analysis
            domains = [data['domain'] for data in emails.values()]
            domain_counts = Counter(domains)
            print("\n  Top email domains:")
            for domain, count in domain_counts.most_common(5):
                print(f"    {domain}: {count} users")
            
            # Tier distribution for email users
            email_tiers = [data['coupon_tier'] for data in emails.values()]
            tier_counts = Counter(email_tiers)
            print("  Coupon tiers for email users:")
            for tier, count in tier_counts.items():
                print(f"    {tier}: {count}")
        
        # Recent activity
        if analytics.data.get('daily_stats'):
            print("\n📅 Recent Daily Activity:")
            recent_days = sorted(analytics.data['daily_stats'].items())[-7:]
            for day, requests in recent_days:
                print(f"  {day}: {requests} requests")
        
        # Export option
        if 'user_emails' in analytics.data and analytics.data['user_emails']:
            export_emails(analytics.data['user_emails'])
        
    except FileNotFoundError:
        print("❌ No analytics data found. Run the agent first to collect data.")
    except Exception as e:
        print(f"❌ Error reading analytics: {e}")

def export_emails(email_data):
    """Export email data to CSV"""
    try:
        filename = "pizza_agent_emails.csv"
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['email', 'domain', 'coupon_tier', 'story_rating', 'timestamp', 'user_hash']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for user_hash, data in email_data.items():
                writer.writerow({
                    'email': data.get('email', ''),
                    'domain': data.get('domain', ''),
                    'coupon_tier': data.get('coupon_tier', ''),
                    'story_rating': data.get('story_rating', ''),
                    'timestamp': data.get('timestamp', ''),
                    'user_hash': user_hash
                })
        
        print(f"\n💾 Email data exported to {filename}")
    except Exception as e:
        print(f"❌ Error exporting emails: {e}")

if __name__ == "__main__":
    main()
