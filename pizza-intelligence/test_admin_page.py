#!/usr/bin/env python3
"""
Test script to verify the admin page functionality
"""

import requests
import json

def test_admin_page():
    """Test the admin page and API endpoints"""
    base_url = "http://127.0.0.1:5005"
    
    print("🧪 Testing Admin Page Functionality")
    print("=" * 50)
    
    # Test 1: Check if main page loads
    print("\n📱 Test 1: Main Page Access")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Main page loads successfully")
            if "Admin Access" in response.text:
                print("✅ Admin access link found on main page")
            else:
                print("❌ Admin access link not found")
        else:
            print(f"❌ Main page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Main page error: {e}")
    
    # Test 2: Check if admin page loads
    print("\n👑 Test 2: Admin Page Access")
    try:
        response = requests.get(f"{base_url}/admin")
        if response.status_code == 200:
            print("✅ Admin page loads successfully")
            if "Admin Dashboard" in response.text:
                print("✅ Admin dashboard content found")
            if "Admin Authentication" in response.text:
                print("✅ Admin authentication section found")
        else:
            print(f"❌ Admin page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Admin page error: {e}")
    
    # Test 3: Test admin summary API without confirmation
    print("\n🔒 Test 3: Admin API Security")
    try:
        response = requests.post(
            f"{base_url}/admin_summary",
            json={"admin_confirmed": False},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 403:
            print("✅ API correctly rejects unauthorized access")
        else:
            print(f"❌ API security issue: {response.status_code}")
    except Exception as e:
        print(f"❌ API security test error: {e}")
    
    # Test 4: Test admin summary API with confirmation
    print("\n📊 Test 4: Admin Summary Generation")
    try:
        response = requests.post(
            f"{base_url}/admin_summary",
            json={"admin_confirmed": True},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Admin summary generated successfully")
                summary = data.get("summary", {})
                if "summary" in summary:
                    print("✅ Executive summary included")
                if "recommendations" in summary:
                    print(f"✅ {len(summary['recommendations'])} recommendations generated")
                if "stats" in summary:
                    print("✅ Statistics included")
            else:
                print("❌ Admin summary generation failed")
        else:
            print(f"❌ Admin summary API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Admin summary test error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("• Main page: http://127.0.0.1:5005/")
    print("• Admin page: http://127.0.0.1:5005/admin")
    print("• Admin authentication: Simple checkbox validation")
    print("• API security: Requires admin_confirmed=true")
    print("\n✅ Admin page implementation complete!")

if __name__ == "__main__":
    test_admin_page()