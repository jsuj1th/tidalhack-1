# hybrid_web_interface.py
"""
Web interface for Hybrid AWS + Gemini Pizza Agent
Uses AWS services (DynamoDB, S3, SES) with original Gemini API
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import asyncio
import json
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import services
from ai_functions import ai_evaluate_story, ai_generate_personalized_response, ai_generate_dynamic_prompts
from functions import generate_coupon_code, evaluate_story_quality

app = Flask(__name__)
CORS(app)

# Configuration
USE_AWS_SERVICES = os.getenv("USE_AWS_SERVICES", "true").lower() == "true"
USE_DYNAMODB = os.getenv("USE_DYNAMODB", "true").lower() == "true"
USE_SES_EMAIL = os.getenv("USE_SES_EMAIL", "true").lower() == "true"
USE_GEMINI = os.getenv("USE_GEMINI", "true").lower() == "true"

# Initialize AWS services
dynamodb_manager = None
s3_manager = None
ses_manager = None

if USE_AWS_SERVICES:
    try:
        if USE_DYNAMODB:
            from aws_dynamodb import get_dynamodb_manager
            dynamodb_manager = get_dynamodb_manager()
            dynamodb_manager.create_tables_if_not_exist()
        if USE_SES_EMAIL:
            from aws_ses import get_ses_manager
            ses_manager = get_ses_manager()
        print("✅ AWS services initialized for web interface")
    except Exception as e:
        print(f"❌ AWS services initialization failed: {e}")

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TidalHACKS 2025 Pizza Agent - Hybrid AWS + Gemini</title>
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
            max-width: 600px; 
            width: 100%;
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #FF6B6B, #4ECDC4); 
            color: white; 
            padding: 30px; 
            text-align: center; 
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { opacity: 0.9; font-size: 1.1em; }
        .tech-badges { margin-top: 15px; }
        .tech-badge { 
            display: inline-block;
            background: rgba(255,255,255,0.2); 
            color: white; 
            padding: 4px 8px; 
            border-radius: 4px; 
            font-size: 0.8em; 
            font-weight: bold;
            margin: 0 3px;
        }
        .gemini-badge { background: #4285f4; }
        .aws-badge { background: #FF9900; }
        .content { padding: 40px; }
        .form-group { margin-bottom: 25px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #333; }
        textarea { 
            width: 100%; 
            padding: 15px; 
            border: 2px solid #e1e5e9; 
            border-radius: 10px; 
            font-size: 16px; 
            resize: vertical;
            min-height: 120px;
            font-family: inherit;
        }
        textarea:focus { outline: none; border-color: #4ECDC4; }
        input[type="email"] {
            width: 100%; 
            padding: 15px; 
            border: 2px solid #e1e5e9; 
            border-radius: 10px; 
            font-size: 16px;
        }
        input[type="email"]:focus { outline: none; border-color: #4ECDC4; }
        .btn { 
            background: linear-gradient(135deg, #FF6B6B, #4ECDC4); 
            color: white; 
            border: none; 
            padding: 15px 30px; 
            border-radius: 10px; 
            font-size: 18px; 
            font-weight: 600;
            cursor: pointer; 
            width: 100%;
            transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .result { 
            margin-top: 30px; 
            padding: 25px; 
            border-radius: 15px; 
            display: none;
        }
        .result.success { background: #d4edda; border: 2px solid #c3e6cb; color: #155724; }
        .result.error { background: #f8d7da; border: 2px solid #f5c6cb; color: #721c24; }
        .coupon-code { 
            font-family: 'Courier New', monospace; 
            font-size: 24px; 
            font-weight: bold; 
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            text-align: center;
            border: 2px dashed #28a745;
        }
        .loading { text-align: center; color: #666; }
        .stats { 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 10px; 
            margin-top: 20px;
            text-align: center;
        }
        .stats h3 { color: #333; margin-bottom: 15px; }
        .stat-item { display: inline-block; margin: 0 15px; }
        .stat-number { font-size: 2em; font-weight: bold; color: #4ECDC4; }
        .stat-label { font-size: 0.9em; color: #666; }
        .architecture { 
            background: #e8f4fd; 
            padding: 15px; 
            border-radius: 10px; 
            margin-top: 20px;
            font-size: 0.9em;
            color: #2c3e50;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🍕 TidalHACKS 2025 Pizza Agent</h1>
            <p>Hybrid Architecture: Best of Both Worlds</p>
            <div class="tech-badges">
                <span class="tech-badge gemini-badge">Gemini AI</span>
                <span class="tech-badge aws-badge">AWS DynamoDB</span>
                <span class="tech-badge aws-badge">AWS S3</span>
                <span class="tech-badge aws-badge">AWS SES</span>
                <span class="tech-badge">Fetch.ai</span>
            </div>
        </div>
        
        <div class="content">
            <form id="pizzaForm">
                <div class="form-group">
                    <label for="story">Tell us your epic pizza story! 🎭</label>
                    <textarea 
                        id="story" 
                        name="story" 
                        placeholder="Share your most legendary pizza moment... Maybe it was that 3am coding session fueled by pizza, or the time pizza saved your hackathon project! The more creative and detailed, the better your coupon tier! 🚀"
                        required
                    ></textarea>
                </div>
                
                <div class="form-group">
                    <label for="email">Email (optional - for coupon delivery via AWS SES) 📧</label>
                    <input 
                        type="email" 
                        id="email" 
                        name="email" 
                        placeholder="your@email.com"
                    >
                </div>
                
                <button type="submit" class="btn" id="submitBtn">
                    🍕 Get My Pizza Coupon!
                </button>
            </form>
            
            <div id="result" class="result"></div>
            
            <div class="stats" id="stats">
                <h3>📊 Live Stats</h3>
                <div class="stat-item">
                    <div class="stat-number" id="totalCoupons">-</div>
                    <div class="stat-label">Coupons Issued</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" id="conversionRate">-</div>
                    <div class="stat-label">Success Rate</div>
                </div>
            </div>
            
            <div class="architecture">
                <strong>🏗️ Architecture:</strong> This system uses Google's Gemini API for AI story evaluation and response generation, while leveraging AWS DynamoDB for scalable data storage, S3 for analytics backups, and SES for professional email delivery. Best of both worlds! 🌟
            </div>
        </div>
    </div>

    <script>
        document.getElementById('pizzaForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = document.getElementById('submitBtn');
            const result = document.getElementById('result');
            const story = document.getElementById('story').value;
            const email = document.getElementById('email').value;
            
            // Validation
            if (story.length < 10) {
                showResult('Please tell us a more detailed story! At least 10 characters.', 'error');
                return;
            }
            
            // Show loading
            submitBtn.disabled = true;
            submitBtn.textContent = '🤖 Gemini AI is evaluating your story...';
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
                        <p><strong>Tier:</strong> ${data.tier}</p>
                        <p><strong>Gemini Rating:</strong> ${data.rating}/10</p>
                        <p><strong>What you get:</strong> ${data.description}</p>
                    `;
                    
                    if (data.email_sent) {
                        message += `<p>📧 <strong>Email sent to ${email} via AWS SES!</strong></p>`;
                    }
                    
                    if (data.ai_explanation) {
                        message += `<p><strong>AI Feedback:</strong> ${data.ai_explanation}</p>`;
                    }
                    
                    message += `<p>📱 Show this code to any food vendor at TidalHACKS 2025!</p>`;
                    
                    showResult(message, 'success');
                    
                    // Clear form
                    document.getElementById('story').value = '';
                    document.getElementById('email').value = '';
                } else {
                    showResult(`❌ ${data.message}`, 'error');
                }
                
            } catch (error) {
                showResult('❌ Something went wrong. Please try again!', 'error');
                console.error('Error:', error);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = '🍕 Get My Pizza Coupon!';
                loadStats();
            }
        });
        
        function showResult(message, type) {
            const result = document.getElementById('result');
            result.innerHTML = message;
            result.className = `result ${type}`;
            result.style.display = 'block';
            result.scrollIntoView({ behavior: 'smooth' });
        }
        
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                
                document.getElementById('totalCoupons').textContent = stats.total_coupons_issued || 0;
                document.getElementById('conversionRate').textContent = (stats.conversion_rate || 0).toFixed(1) + '%';
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
        
        // Load stats on page load
        loadStats();
        
        // Refresh stats every 30 seconds
        setInterval(loadStats, 30000);
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
            if dynamodb_manager.has_user_received_coupon(user_id):
                existing_coupon = dynamodb_manager.get_user_coupon(user_id)
                return jsonify({
                    'success': False,
                    'message': f'You already received a coupon: {existing_coupon}'
                })
        
        # Evaluate story using Gemini API
        rating = 5
        explanation = "Story evaluated"
        
        if USE_GEMINI:
            try:
                # Use async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                rating, explanation = loop.run_until_complete(ai_evaluate_story(story))
                loop.close()
            except Exception as e:
                print(f"Gemini evaluation failed: {e}")
                rating = evaluate_story_quality(story)
                explanation = "Fallback evaluation used"
        else:
            rating = evaluate_story_quality(story)
            explanation = "Rule-based evaluation"
        
        # Generate coupon
        coupon_code, tier = generate_coupon_code(user_id, rating, True)
        
        # Store in DynamoDB
        if USE_DYNAMODB and dynamodb_manager:
            dynamodb_manager.mark_coupon_issued(user_id, coupon_code, tier, rating, story)
            dynamodb_manager.record_analytics_event("coupon_issued", user_id, {
                "tier": tier,
                "rating": rating,
                "story_length": len(story),
                "email": email,
                "source": "web_hybrid"
            })
        
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
            'ai_explanation': explanation[:100] + "..." if len(explanation) > 100 else explanation,
            'email_sent': False
        }
        
        # Send email if provided and SES is enabled
        if email and USE_SES_EMAIL and ses_manager:
            try:
                if ses_manager.validate_email(email):
                    # Generate personalized message using Gemini
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
                            print(f"Gemini response generation failed: {e}")
                    
                    email_result = ses_manager.send_coupon_email(
                        email, coupon_code, tier, rating, personalized_message
                    )
                    
                    if email_result['success']:
                        response_data['email_sent'] = True
                        response_data['message'] += f' Email sent to {email}!'
            except Exception as e:
                print(f"Email sending failed: {e}")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error processing request: {e}")
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
            return jsonify({
                'total_requests': 0,
                'total_coupons_issued': 0,
                'conversion_rate': 0,
                'tier_distribution': {}
            })
    except Exception as e:
        print(f"Error getting stats: {e}")
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
        'architecture': 'hybrid',
        'services': {
            'gemini_api': USE_GEMINI,
            'aws_dynamodb': dynamodb_manager is not None,
            'aws_ses': ses_manager is not None
        }
    }
    
    return jsonify(status)

if __name__ == '__main__':
    print("🚀 Starting Hybrid AWS + Gemini Pizza Agent Web Interface...")
    print("🌐 Access the web interface at: http://localhost:5000")
    
    print("🔧 Services Status:")
    print(f"  Gemini API: {'✅' if USE_GEMINI else '❌'}")
    print(f"  AWS DynamoDB: {'✅' if dynamodb_manager else '❌'}")
    print(f"  AWS SES: {'✅' if ses_manager else '❌'}")
    
    print("\n🎯 Architecture: Hybrid AWS + Gemini")
    print("  • Gemini API for AI (always available)")
    print("  • AWS DynamoDB for scalable storage")
    print("  • AWS SES for professional emails")
    print("  • Best of both worlds! 🌟")
    
    app.run(host='0.0.0.0', port=5000, debug=False)