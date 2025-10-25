# production_web_app.py
"""
Production-ready Pizza Agent Web Application
Optimized for AWS EC2 deployment with public access
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import asyncio
import json
import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/pizza-agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
USE_GEMINI = os.getenv("USE_GEMINI", "true").lower() == "true"
USE_AWS_SERVICES = os.getenv("USE_AWS_SERVICES", "true").lower() == "true"
USE_DYNAMODB = os.getenv("USE_DYNAMODB", "true").lower() == "true"
USE_SES_EMAIL = os.getenv("USE_SES_EMAIL", "true").lower() == "true"

# Initialize services
dynamodb_manager = None
ses_manager = None

# Try to import and initialize AWS services
if USE_AWS_SERVICES:
    try:
        if USE_DYNAMODB:
            sys.path.append('/home/ec2-user/pizza-agent')
            from aws_dynamodb import get_dynamodb_manager
            dynamodb_manager = get_dynamodb_manager()
            dynamodb_manager.create_tables_if_not_exist()
            logger.info("✅ DynamoDB initialized")
        
        if USE_SES_EMAIL:
            from aws_ses import get_ses_manager
            ses_manager = get_ses_manager()
            logger.info("✅ SES initialized")
            
    except Exception as e:
        logger.warning(f"AWS services initialization failed: {e}")
        USE_AWS_SERVICES = False

# Try to import AI functions
try:
    if USE_GEMINI:
        from ai_functions import ai_evaluate_story, ai_generate_personalized_response
        logger.info("✅ Gemini AI initialized")
except Exception as e:
    logger.warning(f"Gemini AI initialization failed: {e}")
    USE_GEMINI = False

# Fallback functions
def evaluate_story_quality(story):
    """Simple rule-based story evaluation"""
    score = 5  # Base score
    
    # Length bonus
    if len(story) > 100:
        score += 1
    if len(story) > 200:
        score += 1
    
    # Keyword bonuses
    pizza_words = ['pizza', 'cheese', 'pepperoni', 'crust', 'slice', 'topping']
    coding_words = ['code', 'coding', 'programming', 'hackathon', 'debug', 'algorithm']
    emotion_words = ['amazing', 'delicious', 'awesome', 'incredible', 'perfect', 'love']
    
    for word_list in [pizza_words, coding_words, emotion_words]:
        if any(word in story.lower() for word in word_list):
            score += 1
    
    return min(10, max(1, score))

def generate_coupon_code(user_id, rating, use_random=True):
    """Generate coupon code and tier"""
    import hashlib
    import random
    
    # Determine tier based on rating
    if rating >= 8:
        tier = "PREMIUM"
    elif rating >= 6:
        tier = "STANDARD"
    else:
        tier = "BASIC"
    
    # Generate code
    if use_random:
        code = f"TIDALHACKS-{tier}-{random.randint(1000, 9999)}-{random.randint(100, 999)}"
    else:
        hash_obj = hashlib.md5(f"{user_id}{rating}".encode())
        code = f"TIDALHACKS-{tier}-{hash_obj.hexdigest()[:8].upper()}"
    
    return code, tier

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TidalHACKS 2025 Pizza Agent 🍕</title>
    <meta name="description" content="Get free pizza coupons by sharing your epic pizza stories at TidalHACKS 2025!">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container { 
            background: white; 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 700px; 
            width: 100%;
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #FF6B6B, #4ECDC4); 
            color: white; 
            padding: 40px; 
            text-align: center; 
        }
        .header h1 { 
            font-size: 2.8em; 
            margin-bottom: 15px; 
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            animation: bounce 2s infinite;
        }
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-10px); }
            60% { transform: translateY(-5px); }
        }
        .header p { opacity: 0.9; font-size: 1.2em; margin-bottom: 20px; }
        .tech-badges { margin-top: 20px; }
        .tech-badge { 
            display: inline-block;
            background: rgba(255,255,255,0.2); 
            color: white; 
            padding: 6px 12px; 
            border-radius: 20px; 
            font-size: 0.9em; 
            font-weight: bold;
            margin: 5px;
            backdrop-filter: blur(10px);
        }
        .content { padding: 50px; }
        .form-group { margin-bottom: 30px; }
        label { 
            display: block; 
            margin-bottom: 10px; 
            font-weight: 600; 
            color: #333; 
            font-size: 1.1em;
        }
        textarea { 
            width: 100%; 
            padding: 20px; 
            border: 3px solid #e1e5e9; 
            border-radius: 15px; 
            font-size: 16px; 
            resize: vertical;
            min-height: 150px;
            font-family: inherit;
            transition: border-color 0.3s ease;
        }
        textarea:focus { 
            outline: none; 
            border-color: #4ECDC4; 
            box-shadow: 0 0 0 3px rgba(78, 205, 196, 0.1);
        }
        input[type="email"] {
            width: 100%; 
            padding: 20px; 
            border: 3px solid #e1e5e9; 
            border-radius: 15px; 
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        input[type="email"]:focus { 
            outline: none; 
            border-color: #4ECDC4; 
            box-shadow: 0 0 0 3px rgba(78, 205, 196, 0.1);
        }
        .btn { 
            background: linear-gradient(135deg, #FF6B6B, #4ECDC4); 
            color: white; 
            border: none; 
            padding: 20px 40px; 
            border-radius: 15px; 
            font-size: 20px; 
            font-weight: 600;
            cursor: pointer; 
            width: 100%;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .btn:hover { 
            transform: translateY(-3px); 
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }
        .btn:disabled { 
            opacity: 0.6; 
            cursor: not-allowed; 
            transform: none; 
            box-shadow: none;
        }
        .result { 
            margin-top: 40px; 
            padding: 30px; 
            border-radius: 20px; 
            display: none;
            animation: slideIn 0.5s ease;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .result.success { 
            background: linear-gradient(135deg, #d4edda, #c3e6cb); 
            border: 3px solid #28a745; 
            color: #155724; 
        }
        .result.error { 
            background: linear-gradient(135deg, #f8d7da, #f5c6cb); 
            border: 3px solid #dc3545; 
            color: #721c24; 
        }
        .coupon-code { 
            font-family: 'Courier New', monospace; 
            font-size: 28px; 
            font-weight: bold; 
            background: white;
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            text-align: center;
            border: 3px dashed #28a745;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }
            100% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }
        }
        .stats { 
            background: linear-gradient(135deg, #f8f9fa, #e9ecef); 
            padding: 30px; 
            border-radius: 20px; 
            margin-top: 30px;
            text-align: center;
        }
        .stats h3 { color: #333; margin-bottom: 20px; font-size: 1.5em; }
        .stat-item { display: inline-block; margin: 0 20px; }
        .stat-number { 
            font-size: 3em; 
            font-weight: bold; 
            color: #4ECDC4; 
            display: block;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        .stat-label { font-size: 1em; color: #666; margin-top: 5px; }
        .footer-info { 
            background: #2c3e50; 
            color: white; 
            padding: 30px; 
            text-align: center; 
            font-size: 0.9em;
            line-height: 1.6;
        }
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #ffffff;
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        @media (max-width: 768px) {
            .container { margin: 10px; }
            .content { padding: 30px; }
            .header { padding: 30px; }
            .header h1 { font-size: 2.2em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🍕 TidalHACKS 2025 Pizza Agent</h1>
            <p>Share your epic pizza story and get a FREE pizza coupon!</p>
            <div class="tech-badges">
                <span class="tech-badge">🤖 Gemini AI</span>
                <span class="tech-badge">☁️ AWS Cloud</span>
                <span class="tech-badge">🚀 Fetch.ai</span>
            </div>
        </div>
        
        <div class="content">
            <form id="pizzaForm">
                <div class="form-group">
                    <label for="story">🎭 Tell us your most EPIC pizza story!</label>
                    <textarea 
                        id="story" 
                        name="story" 
                        placeholder="Share your legendary pizza moment... Maybe it was that 3am coding session fueled by pizza, the time pizza saved your hackathon project, or your most memorable slice during an intense debugging session! The more creative and detailed, the better your coupon tier! 🚀"
                        required
                    ></textarea>
                </div>
                
                <div class="form-group">
                    <label for="email">📧 Email (optional - for coupon delivery)</label>
                    <input 
                        type="email" 
                        id="email" 
                        name="email" 
                        placeholder="your@email.com (we'll send you a beautiful coupon email!)"
                    >
                </div>
                
                <button type="submit" class="btn" id="submitBtn">
                    🍕 Get My Pizza Coupon!
                </button>
            </form>
            
            <div id="result" class="result"></div>
            
            <div class="stats" id="stats">
                <h3>📊 Live Pizza Stats</h3>
                <div class="stat-item">
                    <span class="stat-number" id="totalCoupons">-</span>
                    <div class="stat-label">Coupons Issued</div>
                </div>
                <div class="stat-item">
                    <span class="stat-number" id="conversionRate">-</span>
                    <div class="stat-label">Success Rate</div>
                </div>
            </div>
        </div>
        
        <div class="footer-info">
            <strong>🏗️ Powered by:</strong> Gemini AI for story evaluation • AWS DynamoDB for data • AWS SES for emails • Deployed on AWS EC2<br>
            <strong>🎯 TidalHACKS 2025:</strong> Building the future, one pizza at a time! 🌟
        </div>
    </div>

    <script>
        document.getElementById('pizzaForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = document.getElementById('submitBtn');
            const result = document.getElementById('result');
            const story = document.getElementById('story').value.trim();
            const email = document.getElementById('email').value.trim();
            
            // Validation
            if (story.length < 10) {
                showResult('Please tell us a more detailed story! At least 10 characters to get your pizza coupon.', 'error');
                return;
            }
            
            // Show loading
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading-spinner"></span> AI is evaluating your story...';
            result.style.display = 'none';
            
            try {
                const response = await fetch('/api/request_pizza', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        story: story,
                        email: email
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    let message = `
                        <h3>🎉 ${data.message}</h3>
                        <div class="coupon-code">${data.coupon_code}</div>
                        <p><strong>🏆 Tier:</strong> ${data.tier}</p>
                        <p><strong>⭐ AI Rating:</strong> ${data.rating}/10</p>
                        <p><strong>🍕 What you get:</strong> ${data.description}</p>
                    `;
                    
                    if (data.email_sent) {
                        message += `<p><strong>📧 Email sent to ${email}!</strong> Check your inbox for a beautiful coupon email.</p>`;
                    }
                    
                    if (data.ai_explanation) {
                        message += `<p><strong>🤖 AI Feedback:</strong> ${data.ai_explanation}</p>`;
                    }
                    
                    message += `
                        <hr style="margin: 20px 0; border: 1px solid #28a745;">
                        <p><strong>📱 How to redeem:</strong></p>
                        <ol>
                            <li>Find any participating food vendor at TidalHACKS 2025</li>
                            <li>Show them your coupon code above</li>
                            <li>Enjoy your delicious pizza! 🍕</li>
                        </ol>
                    `;
                    
                    showResult(message, 'success');
                    
                    // Clear form
                    document.getElementById('story').value = '';
                    document.getElementById('email').value = '';
                    
                    // Confetti effect (simple)
                    setTimeout(() => {
                        document.body.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                    }, 100);
                    
                } else {
                    showResult(`❌ ${data.message}`, 'error');
                }
                
            } catch (error) {
                showResult('❌ Something went wrong. Please try again! Our pizza servers might be busy.', 'error');
                console.error('Error:', error);
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '🍕 Get My Pizza Coupon!';
                loadStats();
            }
        });
        
        function showResult(message, type) {
            const result = document.getElementById('result');
            result.innerHTML = message;
            result.className = `result ${type}`;
            result.style.display = 'block';
            result.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                
                document.getElementById('totalCoupons').textContent = stats.total_coupons_issued || 0;
                document.getElementById('conversionRate').textContent = (stats.conversion_rate || 0).toFixed(1) + '%';
            } catch (error) {
                console.error('Error loading stats:', error);
                document.getElementById('totalCoupons').textContent = '🍕';
                document.getElementById('conversionRate').textContent = '100%';
            }
        }
        
        // Load stats on page load
        loadStats();
        
        // Refresh stats every 30 seconds
        setInterval(loadStats, 30000);
        
        // Add some fun interactions
        document.getElementById('story').addEventListener('input', function() {
            const length = this.value.length;
            if (length > 50) {
                this.style.borderColor = '#28a745';
            } else if (length > 20) {
                this.style.borderColor = '#ffc107';
            } else {
                this.style.borderColor = '#e1e5e9';
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main web interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/request_pizza', methods=['POST'])
def request_pizza():
    """API endpoint for pizza coupon requests"""
    try:
        data = request.get_json()
        story = data.get('story', '').strip()
        email = data.get('email', '').strip()
        
        logger.info(f"Pizza request received: story_length={len(story)}, has_email={bool(email)}")
        
        # Validation
        if len(story) < 10:
            return jsonify({
                'success': False,
                'message': 'Please tell us a more detailed story! At least 10 characters.'
            })
        
        # Generate user ID
        user_id = f"web_user_{hash(story + email + str(datetime.now().timestamp()))}"
        
        # Check if user already got a coupon (simplified for web)
        if USE_DYNAMODB and dynamodb_manager:
            try:
                if dynamodb_manager.has_user_received_coupon(user_id):
                    existing_coupon = dynamodb_manager.get_user_coupon(user_id)
                    return jsonify({
                        'success': False,
                        'message': f'You already received a coupon: {existing_coupon}'
                    })
            except Exception as e:
                logger.warning(f"DynamoDB check failed: {e}")
        
        # Evaluate story
        rating = 5
        explanation = "Story evaluated successfully"
        
        if USE_GEMINI:
            try:
                # Use async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                rating, explanation = loop.run_until_complete(ai_evaluate_story(story))
                loop.close()
                logger.info(f"Gemini evaluation: rating={rating}")
            except Exception as e:
                logger.warning(f"Gemini evaluation failed: {e}")
                rating = evaluate_story_quality(story)
                explanation = "Fallback evaluation used"
        else:
            rating = evaluate_story_quality(story)
            explanation = "Rule-based evaluation"
        
        # Generate coupon
        coupon_code, tier = generate_coupon_code(user_id, rating, True)
        
        # Store in DynamoDB
        if USE_DYNAMODB and dynamodb_manager:
            try:
                dynamodb_manager.mark_coupon_issued(user_id, coupon_code, tier, rating, story)
                dynamodb_manager.record_analytics_event("coupon_issued", user_id, {
                    "tier": tier,
                    "rating": rating,
                    "story_length": len(story),
                    "email": email,
                    "source": "web_production"
                })
                logger.info(f"Stored in DynamoDB: {coupon_code}")
            except Exception as e:
                logger.warning(f"DynamoDB storage failed: {e}")
        
        # Tier descriptions
        tier_descriptions = {
            "PREMIUM": "LARGE pizza with premium toppings! 🏆",
            "STANDARD": "MEDIUM pizza with your choice of toppings! 👍",
            "BASIC": "REGULAR pizza - still delicious! 🙂"
        }
        
        response_data = {
            'success': True,
            'message': 'Congratulations! Your pizza coupon is ready!',
            'coupon_code': coupon_code,
            'tier': tier,
            'rating': rating,
            'description': tier_descriptions.get(tier, "Delicious pizza!"),
            'ai_explanation': explanation[:150] + "..." if len(explanation) > 150 else explanation,
            'email_sent': False
        }
        
        # Send email if provided and SES is enabled
        if email and USE_SES_EMAIL and ses_manager:
            try:
                if ses_manager.validate_email(email):
                    # Generate personalized message
                    personalized_message = f"Thanks for your amazing story! Rating: {rating}/10"
                    
                    if USE_GEMINI:
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            personalized_message = loop.run_until_complete(
                                ai_generate_personalized_response(story, rating, tier, coupon_code)
                            )
                            loop.close()
                        except Exception as e:
                            logger.warning(f"Gemini response generation failed: {e}")
                    
                    email_result = ses_manager.send_coupon_email(
                        email, coupon_code, tier, rating, personalized_message
                    )
                    
                    if email_result['success']:
                        response_data['email_sent'] = True
                        response_data['message'] += f' Email sent to {email}!'
                        logger.info(f"Email sent successfully to {email}")
                    else:
                        logger.warning(f"Email sending failed: {email_result['message']}")
            except Exception as e:
                logger.warning(f"Email processing failed: {e}")
        
        logger.info(f"Pizza coupon issued: {coupon_code} ({tier}) - rating: {rating}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({
            'success': False,
            'message': 'Something went wrong. Please try again!'
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get analytics statistics"""
    try:
        if USE_DYNAMODB and dynamodb_manager:
            stats = dynamodb_manager.get_analytics_summary()
            return jsonify(stats)
        else:
            # Return mock stats if DynamoDB not available
            return jsonify({
                'total_requests': 42,
                'total_coupons_issued': 38,
                'conversion_rate': 90.5,
                'tier_distribution': {
                    'PREMIUM': 12,
                    'STANDARD': 18,
                    'BASIC': 8
                }
            })
    except Exception as e:
        logger.warning(f"Error getting stats: {e}")
        return jsonify({
            'total_requests': 0,
            'total_coupons_issued': 0,
            'conversion_rate': 0,
            'tier_distribution': {}
        })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    status = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0.0',
        'services': {
            'gemini_ai': USE_GEMINI,
            'aws_dynamodb': dynamodb_manager is not None,
            'aws_ses': ses_manager is not None
        },
        'environment': os.getenv('ENVIRONMENT', 'production')
    }
    
    return jsonify(status)

@app.route('/api/info')
def info():
    """System information endpoint"""
    return jsonify({
        'name': 'TidalHACKS 2025 Pizza Agent',
        'description': 'Get free pizza coupons by sharing epic pizza stories!',
        'version': '1.0.0',
        'architecture': 'Hybrid AWS + Gemini',
        'features': [
            'AI-powered story evaluation',
            'Scalable AWS infrastructure',
            'Professional email delivery',
            'Real-time analytics'
        ],
        'endpoints': {
            'main': '/',
            'pizza_request': '/api/request_pizza',
            'stats': '/api/stats',
            'health': '/health'
        }
    })

if __name__ == '__main__':
    logger.info("🚀 Starting TidalHACKS 2025 Pizza Agent (Production)")
    logger.info(f"Services: Gemini={USE_GEMINI}, DynamoDB={bool(dynamodb_manager)}, SES={bool(ses_manager)}")
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)