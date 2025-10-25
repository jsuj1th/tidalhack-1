# aws_ses.py
"""
AWS SES (Simple Email Service) integration for sending pizza coupons
Replaces Gmail SMTP with AWS SES
"""

import boto3
from botocore.exceptions import ClientError
from typing import Dict, Optional
import re
from aws_config import get_aws_services, SES_FROM_EMAIL, SES_FROM_NAME

class SESEmailManager:
    """AWS SES Email Manager"""
    
    def __init__(self):
        self.aws = get_aws_services()
        self.ses = self.aws.ses
        self.from_email = SES_FROM_EMAIL
        self.from_name = SES_FROM_NAME
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def verify_email_address(self, email: str) -> Dict[str, any]:
        """Verify email address with SES (for development)"""
        try:
            response = self.ses.verify_email_identity(EmailAddress=email)
            return {"success": True, "message": f"Verification email sent to {email}"}
        except ClientError as e:
            return {"success": False, "message": f"Verification failed: {e.response['Error']['Message']}"}
    
    def get_send_quota(self) -> Dict[str, any]:
        """Get SES sending quota and statistics"""
        try:
            quota = self.ses.get_send_quota()
            stats = self.ses.get_send_statistics()
            
            return {
                "max_24_hour": quota.get('Max24HourSend', 0),
                "max_send_rate": quota.get('MaxSendRate', 0),
                "sent_last_24h": quota.get('SentLast24Hours', 0),
                "statistics": stats.get('SendDataPoints', [])
            }
        except ClientError as e:
            return {"error": e.response['Error']['Message']}
    
    def create_coupon_email_html(self, recipient_email: str, coupon_code: str, tier: str, story_rating: int, personalized_message: str = "") -> str:
        """Create HTML email content for pizza coupon"""
        
        return f"""
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
                .aws-badge {{ 
                    background: #FF9900; 
                    color: white; 
                    padding: 4px 8px; 
                    border-radius: 4px; 
                    font-size: 12px; 
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🍕 Your TidalHACKS25 Pizza Coupon! 🎉</h1>
                    <p style="margin: 10px 0 0 0; color: #f8f9fa;">Powered by AWS & Fetch.ai</p>
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
                        <h3 style="margin-top: 0; color: #2196F3;">📱 How to Redeem</h3>
                        <ol>
                            <li>Find any participating food vendor at TidalHACKS25</li>
                            <li>Show them this coupon code: <strong style="color: #d63384;">{coupon_code}</strong></li>
                            <li>Enjoy your delicious {tier.lower()} pizza! 🍕</li>
                        </ol>
                        
                        <p><strong>What you get:</strong></p>
                        <ul>
                            {"<li>🏆 LARGE pizza with premium toppings!</li>" if tier == "PREMIUM" else ""}
                            {"<li>👍 MEDIUM pizza with your choice of toppings!</li>" if tier == "STANDARD" else ""}
                            {"<li>🙂 REGULAR pizza - still delicious!</li>" if tier == "BASIC" else ""}
                        </ul>
                    </div>
                    
                    <p style="text-align: center; color: #6c757d; font-style: italic;">
                        🚀 Powered by <span class="aws-badge">AWS</span> & Fetch.ai - Fueling innovation, one pizza at a time! 🚀
                    </p>
                </div>
                
                <div class="footer">
                    <p>TidalHACKS25 Pizza Agent | Sponsored by Fetch.ai</p>
                    <p>Delivered via AWS SES | Questions? Find us at the Fetch.ai booth!</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def create_coupon_email_text(self, recipient_email: str, coupon_code: str, tier: str, story_rating: int, personalized_message: str = "") -> str:
        """Create plain text email content for pizza coupon"""
        
        return f"""
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

🚀 Powered by AWS & Fetch.ai - Fueling innovation, one pizza at a time! 🚀

TidalHACKS25 Pizza Agent | Sponsored by Fetch.ai
Delivered via AWS SES | Questions? Find us at the Fetch.ai booth!
        """
    
    def send_coupon_email(self, recipient_email: str, coupon_code: str, tier: str, story_rating: int, personalized_message: str = "") -> Dict[str, any]:
        """
        Send coupon via AWS SES
        Returns: {"success": bool, "message": str, "message_id": str}
        """
        
        # Validate inputs
        if not self.validate_email(recipient_email):
            return {"success": False, "message": "Invalid email address format"}
        
        if not self.from_email:
            return {"success": False, "message": "SES sender email not configured. Please set SES_FROM_EMAIL environment variable."}
        
        try:
            # Create email content
            html_content = self.create_coupon_email_html(recipient_email, coupon_code, tier, story_rating, personalized_message)
            text_content = self.create_coupon_email_text(recipient_email, coupon_code, tier, story_rating, personalized_message)
            
            # Send email using SES
            response = self.ses.send_email(
                Source=f"{self.from_name} <{self.from_email}>",
                Destination={
                    'ToAddresses': [recipient_email]
                },
                Message={
                    'Subject': {
                        'Data': f'🍕 Your TidalHACKS25 Pizza Coupon: {coupon_code}',
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': text_content,
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': html_content,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            
            message_id = response.get('MessageId', '')
            
            return {
                "success": True, 
                "message": f"Coupon sent successfully to {recipient_email}",
                "message_id": message_id
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'MessageRejected':
                return {"success": False, "message": f"Email rejected: {error_message}"}
            elif error_code == 'SendingPausedException':
                return {"success": False, "message": "SES sending is paused for your account"}
            elif error_code == 'MailFromDomainNotVerifiedException':
                return {"success": False, "message": "Sender email domain not verified in SES"}
            else:
                return {"success": False, "message": f"SES error ({error_code}): {error_message}"}
                
        except Exception as e:
            return {"success": False, "message": f"Unexpected error: {str(e)}"}
    
    def test_ses_configuration(self) -> Dict[str, any]:
        """Test if SES configuration is working"""
        if not self.from_email:
            return {
                "configured": False, 
                "message": "SES not configured. Set SES_FROM_EMAIL environment variable."
            }
        
        try:
            # Get send quota to test connection
            quota = self.get_send_quota()
            
            if "error" in quota:
                return {"configured": False, "message": f"SES configuration error: {quota['error']}"}
            
            return {
                "configured": True, 
                "message": "SES configuration is working!",
                "quota": quota
            }
            
        except Exception as e:
            return {"configured": False, "message": f"SES configuration error: {str(e)}"}

# Global SES manager instance
ses_manager = None

def get_ses_manager() -> SESEmailManager:
    """Get or create SES manager instance"""
    global ses_manager
    if ses_manager is None:
        ses_manager = SESEmailManager()
    return ses_manager

if __name__ == "__main__":
    print("🚀 Testing AWS SES integration...")
    
    try:
        ses = get_ses_manager()
        
        # Test SES configuration
        result = ses.test_ses_configuration()
        print(f"SES Configuration: {result}")
        
        if result["configured"]:
            print(f"Send Quota: {result.get('quota', {})}")
            
            # Test email sending (uncomment to test with a real email)
            # test_result = ses.send_coupon_email(
            #     "test@example.com", 
            #     "PIZZA-TEST-PREMIUM-ABC123-1234", 
            #     "PREMIUM", 
            #     9, 
            #     "🎉 Amazing story! You've earned a premium pizza!"
            # )
            # print(f"Test Send: {test_result}")
        
        print("✅ SES integration ready!")
        
    except Exception as e:
        print(f"❌ SES test failed: {e}")