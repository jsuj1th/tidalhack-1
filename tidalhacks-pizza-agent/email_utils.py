# email_utils.py
"""
Email utility functions for sending pizza coupons
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from dotenv import load_dotenv
from typing import Optional
import re

load_dotenv()

# Email configuration from environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "TidalHACKS25 Pizza Agent")

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def create_coupon_email(recipient_email: str, coupon_code: str, tier: str, story_rating: int, personalized_message: str = "") -> MIMEMultipart:
    """Create a formatted email with the pizza coupon"""
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🍕 Your TidalHACKS25 Pizza Coupon: {coupon_code}"
    msg["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_ADDRESS}>"
    msg["To"] = recipient_email
    
    # Create the HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Pizza Coupon</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8f9fa; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
            .header {{ background: linear-gradient(135deg, #FF6B6B, #4ECDC4); padding: 30px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 28px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
            .content {{ padding: 30px; }}
            .coupon-box {{ 
                background: #fff3cd; 
                border: 3px dashed #ffc107; 
                padding: 25px; 
                border-radius: 15px; 
                margin: 20px 0; 
                text-align: center;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
            .coupon-code {{ 
                font-family: 'Courier New', monospace; 
                font-size: 24px; 
                font-weight: bold; 
                color: #d63384;
                background: white;
                padding: 15px;
                border-radius: 8px;
                margin: 10px 0;
                border: 2px solid #ffc107;
            }}
            .tier-badge {{ 
                display: inline-block; 
                padding: 8px 16px; 
                border-radius: 20px; 
                font-weight: bold; 
                text-transform: uppercase; 
                margin: 10px 0;
            }}
            .tier-premium {{ background: #FFD700; color: #8B4513; }}
            .tier-standard {{ background: #C0C0C0; color: #2F4F4F; }}
            .tier-basic {{ background: #CD7F32; color: white; }}
            .rating {{ 
                background: linear-gradient(45deg, #FF6B6B, #4ECDC4); 
                color: white; 
                padding: 8px 16px; 
                border-radius: 20px; 
                font-weight: bold; 
                display: inline-block;
                margin: 10px 0;
            }}
            .message-box {{ 
                background: #e8f5e8; 
                padding: 20px; 
                border-radius: 10px; 
                margin: 20px 0; 
                border-left: 4px solid #4CAF50;
                line-height: 1.6;
            }}
            .instructions {{ 
                background: #e8f4fd; 
                padding: 20px; 
                border-radius: 10px; 
                margin: 20px 0; 
                border-left: 4px solid #2196F3;
            }}
            .footer {{ 
                background: #2c3e50; 
                color: white; 
                padding: 20px; 
                text-align: center; 
                font-size: 14px;
            }}
            .emoji {{ font-size: 1.2em; }}
            .highlight {{ color: #e74c3c; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1><span class="emoji">🍕</span> Your TidalHACKS25 Pizza Coupon! <span class="emoji">🎉</span></h1>
            </div>
            
            <div class="content">
                <div class="coupon-box">
                    <h2 style="margin-top: 0; color: #d63384;">Your Coupon Code</h2>
                    <div class="coupon-code">{coupon_code}</div>
                    <div class="tier-badge tier-{tier.lower()}">{tier} Tier</div>
                    <div class="rating">⭐ Story Rating: {story_rating}/10</div>
                </div>
                
                {f'<div class="message-box">{personalized_message}</div>' if personalized_message else ''}
                
                <div class="instructions">
                    <h3 style="margin-top: 0; color: #2196F3;"><span class="emoji">📱</span> How to Redeem</h3>
                    <ol>
                        <li>Find any participating food vendor at TidalHACKS25</li>
                        <li>Show them this coupon code: <span class="highlight">{coupon_code}</span></li>
                        <li>Enjoy your delicious {tier.lower()} pizza! <span class="emoji">🍕</span></li>
                    </ol>
                    
                    <p><strong>What you get:</strong></p>
                    <ul>
                        {"<li>🏆 LARGE pizza with premium toppings!</li>" if tier == "PREMIUM" else ""}
                        {"<li>👍 MEDIUM pizza with your choice of toppings!</li>" if tier == "STANDARD" else ""}
                        {"<li>🙂 REGULAR pizza - still delicious!</li>" if tier == "BASIC" else ""}
                    </ul>
                </div>
                
                <p style="text-align: center; color: #6c757d; font-style: italic;">
                    <span class="emoji">🚀</span> Powered by Fetch.ai - Fueling innovation, one pizza at a time! <span class="emoji">🚀</span>
                </p>
            </div>
            
            <div class="footer">
                <p>TidalHACKS25 Pizza Agent | Sponsored by Fetch.ai</p>
                <p>Questions? Find us at the Fetch.ai booth!</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create plain text version
    text_content = f"""
🍕 Your TidalHACKS25 Pizza Coupon! 🎉

Your Coupon Code: {coupon_code}
Tier: {tier}
Story Rating: {story_rating}/10

{personalized_message if personalized_message else ''}

How to Redeem:
1. Find any participating food vendor at TidalHACKS25
2. Show them this coupon code: {coupon_code}
3. Enjoy your delicious pizza! 🍕

What you get:
{"- LARGE pizza with premium toppings!" if tier == "PREMIUM" else ""}
{"- MEDIUM pizza with your choice of toppings!" if tier == "STANDARD" else ""}
{"- REGULAR pizza - still delicious!" if tier == "BASIC" else ""}

🚀 Powered by Fetch.ai - Fueling innovation, one pizza at a time! 🚀

TidalHACKS25 Pizza Agent | Sponsored by Fetch.ai
Questions? Find us at the Fetch.ai booth!
    """
    
    # Attach both versions
    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(html_content, "html")
    
    msg.attach(part1)
    msg.attach(part2)
    
    return msg

def send_coupon_email(recipient_email: str, coupon_code: str, tier: str, story_rating: int, personalized_message: str = "") -> dict:
    """
    Send coupon via email
    Returns: {"success": bool, "message": str}
    """
    
    # Validate inputs
    if not validate_email(recipient_email):
        return {"success": False, "message": "Invalid email address format"}
    
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return {"success": False, "message": "Email service not configured. Please set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables."}
    
    try:
        # Create message
        msg = create_coupon_email(recipient_email, coupon_code, tier, story_rating, personalized_message)
        
        # Create secure connection and send
        context = ssl.create_default_context()
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return {"success": True, "message": f"Coupon sent successfully to {recipient_email}"}
        
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Email authentication failed. Please check EMAIL_ADDRESS and EMAIL_PASSWORD."}
    except smtplib.SMTPRecipientsRefused:
        return {"success": False, "message": "Invalid recipient email address."}
    except smtplib.SMTPException as e:
        return {"success": False, "message": f"SMTP error: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}"}

def test_email_configuration() -> dict:
    """Test if email configuration is working"""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return {
            "configured": False, 
            "message": "Email not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables."
        }
    
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        
        return {"configured": True, "message": "Email configuration is working!"}
    except Exception as e:
        return {"configured": False, "message": f"Email configuration error: {str(e)}"}

if __name__ == "__main__":
    # Test email configuration
    result = test_email_configuration()
    print(f"Email Configuration: {result}")
    
    # Test email sending (uncomment to test with a real email)
    # test_result = send_coupon_email(
    #     "test@example.com", 
    #     "PIZZA-TEST-PREMIUM-ABC123-1234", 
    #     "PREMIUM", 
    #     9, 
    #     "🎉 Amazing story! You've earned a premium pizza!"
    # )
    # print(f"Test Send: {test_result}")