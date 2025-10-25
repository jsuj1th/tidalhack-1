#!/usr/bin/env python3
"""
Pizza Intelligence - User Interface
Clean, production-ready interface for users to get pizza coupons
"""

from flask import Flask, render_template_string, request, jsonify
import asyncio
from functions import generate_coupon_code, evaluate_story_quality
from ai_functions import ai_evaluate_story, ai_generate_personalized_response, ai_generate_dynamic_prompts
from gemini_functions import gemini_evaluate_story, gemini_generate_response_message, gemini_generate_unique_prompt
from config import USE_GEMINI, USE_AI_EVALUATION, USE_AI_RESPONSES, USE_AI_PROMPTS
from email_utils import send_coupon_email, test_email_configuration, validate_email
import json

app = Flask(__name__)

# Main user interface template
USER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🍕 Pizza Intelligence - Get Your Free Pizza Coupon!</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { box-sizing: border-box; }
        
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 0; 
            background: linear-gradient(135deg, #FF6B6B, #4ECDC4, #45B7D1);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .main-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            backdrop-filter: blur(10px);
            text-align: center;
        }
        
        .header {
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin: 0 0 10px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        
        .header p {
            color: #7f8c8d;
            font-size: 1.2em;
            margin: 0;
        }
        
        .story-section {
            margin: 30px 0;
            text-align: left;
        }
        
        .story-section label {
            display: block;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        .story-textarea {
            width: 100%;
            min-height: 120px;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 12px;
            font-family: inherit;
            font-size: 16px;
            resize: vertical;
            transition: border-color 0.3s;
        }
        
        .story-textarea:focus {
            outline: none;
            border-color: #4ECDC4;
            box-shadow: 0 0 0 3px rgba(78, 205, 196, 0.2);
        }
        
        .email-section {
            margin: 20px 0;
            text-align: left;
        }
        
        .email-section label {
            display: block;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        .email-input {
            width: 100%;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 12px;
            font-family: inherit;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        .email-input:focus {
            outline: none;
            border-color: #4ECDC4;
            box-shadow: 0 0 0 3px rgba(78, 205, 196, 0.2);
        }
        
        .submit-button {
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            color: white;
            border: none;
            padding: 18px 40px;
            font-size: 1.2em;
            font-weight: bold;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .submit-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }
        
        .submit-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .result-section {
            margin-top: 30px;
            display: none;
        }
        
        .coupon-display {
            background: #fff3cd;
            border: 3px dashed #ffc107;
            padding: 25px;
            border-radius: 15px;
            margin: 20px 0;
            position: relative;
        }
        
        .coupon-code {
            font-family: 'Courier New', monospace;
            font-size: 1.8em;
            font-weight: bold;
            color: #d63384;
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border: 2px solid #ffc107;
            word-break: break-all;
        }
        
        .tier-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            text-transform: uppercase;
            margin: 10px 5px;
            font-size: 0.9em;
        }
        
        .tier-premium { background: #FFD700; color: #8B4513; }
        .tier-standard { background: #C0C0C0; color: #2F4F4F; }
        .tier-basic { background: #CD7F32; color: white; }
        
        .rating-display {
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            display: inline-block;
            margin: 10px 5px;
        }
        
        .instructions {
            background: #e8f4fd;
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
            border-left: 4px solid #2196F3;
            text-align: left;
        }
        
        .instructions h3 {
            color: #2196F3;
            margin-top: 0;
        }
        
        .instructions ol, .instructions ul {
            margin: 10px 0;
            padding-left: 25px;
        }
        
        .instructions li {
            margin: 8px 0;
            line-height: 1.5;
        }
        
        .email-status {
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            font-weight: bold;
        }
        
        .email-success {
            background: #d4edda;
            color: #155724;
            border-left: 4px solid #28a745;
        }
        
        .email-error {
            background: #f8d7da;
            color: #721c24;
            border-left: 4px solid #dc3545;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #4ECDC4;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .copy-button {
            background: #FF9800;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9em;
            margin-left: 10px;
            transition: background 0.3s;
        }
        
        .copy-button:hover {
            background: #F57C00;
        }
        
        .copy-button.copied {
            background: #4CAF50;
        }
        
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #7f8c8d;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .main-container {
                padding: 20px;
                margin: 20px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .coupon-code {
                font-size: 1.4em;
            }
        }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="header">
            <h1>🍕 Pizza Intelligence</h1>
            <p>Share your pizza story and get a delicious reward!</p>
        </div>
        
        <div class="instructions">
            <h3>🍕 To get your special pizza coupon, share your most unforgettable pizza story!</h3>
            <p><strong>You could talk about:</strong></p>
            <ul>
                <li>🎢 The wildest pizza experience you've ever had</li>
                <li>🌟 Your ultimate dream pizza mix</li>
                <li>☀️ A moment when pizza brightened your day</li>
                <li>📚 Or any memorable pizza tale!</li>
            </ul>
            <p><em>The more creative and entertaining your story, the better the pizza reward you'll receive!</em></p>
        </div>
        
        <form id="pizzaForm">
            <div class="story-section">
                <label for="story">📖 Tell us your pizza story:</label>
                <textarea 
                    id="story" 
                    class="story-textarea" 
                    placeholder="Share your most unforgettable pizza story here! Think about the wildest pizza experience you've had, your dream pizza combination, or a moment when pizza made your day special. Be creative and entertaining - the better your story, the better your reward!"
                    required
                ></textarea>
            </div>
            
            <div class="email-section">
                <label for="email">📧 Email address (optional):</label>
                <input 
                    type="email" 
                    id="email" 
                    class="email-input" 
                    placeholder="your.email@example.com"
                >
                <small style="color: #7f8c8d; font-style: italic;">
                    Enter your email to receive a beautifully formatted coupon in your inbox!
                </small>
            </div>
            
            <button type="submit" class="submit-button" id="submitBtn">
                🎫 Get My Pizza Coupon!
            </button>
        </form>
        
        <div id="result" class="result-section">
            <!-- Results will be displayed here -->
        </div>
        
        <div class="footer">
            <p>🍕 Enjoy your delicious pizza! | Share great stories, get great rewards!</p>
        </div>
    </div>

    <script>
        // Copy to clipboard function
        function copyToClipboard(text, buttonElement) {
            navigator.clipboard.writeText(text).then(() => {
                const originalText = buttonElement.textContent;
                buttonElement.textContent = '✅ Copied!';
                buttonElement.classList.add('copied');
                
                setTimeout(() => {
                    buttonElement.textContent = originalText;
                    buttonElement.classList.remove('copied');
                }, 2000);
            }).catch(() => {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                const originalText = buttonElement.textContent;
                buttonElement.textContent = '✅ Copied!';
                buttonElement.classList.add('copied');
                
                setTimeout(() => {
                    buttonElement.textContent = originalText;
                    buttonElement.classList.remove('copied');
                }, 2000);
            });
        }
        
        // Format tier badge
        function formatTier(tier) {
            const tierClass = tier.toLowerCase().replace(/[^a-z]/g, '');
            return `<span class="tier-badge tier-${tierClass}">${tier}</span>`;
        }
        
        // Format rating display
        function formatRating(rating) {
            return `<span class="rating-display">⭐ ${rating}/10</span>`;
        }
        
        // Handle form submission
        document.getElementById('pizzaForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = document.getElementById('submitBtn');
            const resultDiv = document.getElementById('result');
            const story = document.getElementById('story').value.trim();
            const email = document.getElementById('email').value.trim();
            
            if (!story) {
                alert('Please share your pizza story!');
                return;
            }
            
            // Show loading state
            submitBtn.innerHTML = '<span class="loading"></span>Generating your coupon...';
            submitBtn.disabled = true;
            resultDiv.style.display = 'none';
            
            try {
                const endpoint = email ? '/generate_coupon_with_email' : '/generate_coupon';
                const payload = email ? { story, email } : { story };
                
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                const result = await response.json();
                
                if (result.error) {
                    throw new Error(result.error);
                }
                
                // Display results
                let emailStatusHtml = '';
                if (email) {
                    if (result.email_sent) {
                        emailStatusHtml = `
                            <div class="email-status email-success">
                                📧 ✅ Coupon sent successfully to ${email}!<br>
                                <small>${result.email_message}</small>
                            </div>
                        `;
                    } else {
                        emailStatusHtml = `
                            <div class="email-status email-error">
                                📧 ❌ Failed to send email to ${email}<br>
                                <small>${result.email_message}</small><br>
                                <em>Don't worry! Your coupon code below still works perfectly.</em>
                            </div>
                        `;
                    }
                }
                
                resultDiv.innerHTML = `
                    <div class="coupon-display">
                        <h2 style="color: #2c3e50; margin-top: 0;">🎉 Your Pizza Coupon!</h2>
                        
                        <div class="coupon-code">
                            ${result.coupon_code}
                            <button class="copy-button" onclick="copyToClipboard('${result.coupon_code}', this)">
                                📋 Copy
                            </button>
                        </div>
                        
                        <div style="margin: 15px 0;">
                            ${formatTier(result.tier)}
                            ${formatRating(result.rating)}
                        </div>
                        
                        ${emailStatusHtml}
                    </div>
                    
                    <div class="instructions">
                        <h3>📱 How to Use Your Coupon</h3>
                        <ol>
                            <li>Find any participating food vendor at the event</li>
                            <li>Show them your coupon code: <strong>${result.coupon_code}</strong></li>
                            <li>Enjoy your delicious ${result.tier.toLowerCase()} pizza! 🍕</li>
                        </ol>
                        
                        <h4>What you get:</h4>
                        <ul>
                            ${result.tier === "PREMIUM" ? "<li>🏆 LARGE pizza with premium toppings!</li>" : ""}
                            ${result.tier === "STANDARD" ? "<li>👍 MEDIUM pizza with your choice of toppings!</li>" : ""}
                            ${result.tier === "BASIC" ? "<li>🙂 REGULAR pizza - still delicious!</li>" : ""}
                        </ul>
                    </div>
                `;
                
                resultDiv.style.display = 'block';
                
                // Scroll to results
                resultDiv.scrollIntoView({ behavior: 'smooth' });
                
            } catch (error) {
                resultDiv.innerHTML = `
                    <div class="email-status email-error">
                        ❌ Something went wrong: ${error.message}<br>
                        Please try again or contact support.
                    </div>
                `;
                resultDiv.style.display = 'block';
            } finally {
                submitBtn.innerHTML = '🎫 Get My Pizza Coupon!';
                submitBtn.disabled = false;
            }
        });
        
        // Auto-resize textarea
        document.getElementById('story').addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.max(120, this.scrollHeight) + 'px';
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main user interface"""
    return render_template_string(USER_TEMPLATE)

@app.route('/generate_coupon', methods=['POST'])
def generate_coupon():
    """Generate a coupon without email"""
    data = request.json
    story = data.get('story', '').strip()
    
    if not story:
        return jsonify({'error': 'Story is required'})
    
    if len(story) < 10:
        return jsonify({'error': 'Please write a longer story (at least 10 characters)'})
    
    try:
        # Evaluate story
        if USE_AI_EVALUATION and USE_GEMINI:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            rating, explanation = loop.run_until_complete(gemini_evaluate_story(story))
        else:
            rating = evaluate_story_quality(story)
            explanation = "Rule-based evaluation"
        
        # Generate coupon
        coupon_code, tier = generate_coupon_code("user", rating, True)
        
        # Generate response
        if USE_AI_RESPONSES and USE_GEMINI:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(
                gemini_generate_response_message(story, rating, tier, coupon_code)
            )
        else:
            # Fallback response
            if rating >= 8:
                response = f"🎉 Amazing story! Your coupon gets you a LARGE premium pizza! 🏆"
            elif rating >= 6:
                response = f"😊 Great story! Your coupon gets you a MEDIUM pizza! 👍"
            else:
                response = f"🍕 Thanks for sharing! Your coupon gets you a tasty pizza! 🙂"
        
        return jsonify({
            'coupon_code': coupon_code,
            'tier': tier,
            'rating': rating,
            'response': response
        })
        
    except Exception as e:
        return jsonify({
            'error': f"Sorry, something went wrong: {str(e)}"
        })

@app.route('/generate_coupon_with_email', methods=['POST'])
def generate_coupon_with_email():
    """Generate a coupon and send via email"""
    data = request.json
    story = data.get('story', '').strip()
    email = data.get('email', '').strip()
    
    if not story:
        return jsonify({'error': 'Story is required'})
    
    if not email:
        return jsonify({'error': 'Email address is required'})
    
    if len(story) < 10:
        return jsonify({'error': 'Please write a longer story (at least 10 characters)'})
    
    if not validate_email(email):
        return jsonify({'error': 'Please enter a valid email address'})
    
    try:
        # Evaluate story
        if USE_AI_EVALUATION and USE_GEMINI:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            rating, explanation = loop.run_until_complete(gemini_evaluate_story(story))
        else:
            rating = evaluate_story_quality(story)
            explanation = "Rule-based evaluation"
        
        # Generate coupon
        coupon_code, tier = generate_coupon_code("user", rating, True)
        
        # Generate response
        if USE_AI_RESPONSES and USE_GEMINI:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(
                gemini_generate_response_message(story, rating, tier, coupon_code)
            )
        else:
            # Fallback response
            if rating >= 8:
                response = f"🎉 Amazing story! Your coupon gets you a LARGE premium pizza! 🏆"
            elif rating >= 6:
                response = f"😊 Great story! Your coupon gets you a MEDIUM pizza! 👍"
            else:
                response = f"🍕 Thanks for sharing! Your coupon gets you a tasty pizza! 🙂"
        
        # Send email
        email_result = send_coupon_email(email, coupon_code, tier, rating, response)
        
        return jsonify({
            'coupon_code': coupon_code,
            'tier': tier,
            'rating': rating,
            'response': response,
            'email_sent': email_result['success'],
            'email_message': email_result['message']
        })
        
    except Exception as e:
        return jsonify({
            'error': f"Sorry, something went wrong: {str(e)}"
        })

if __name__ == '__main__':
    print("🍕 Starting Pizza Intelligence")
    print("📱 Open your browser to: http://127.0.0.1:5002")
    print("🎯 Clean user interface - ready for production!")
    print()
    app.run(debug=True, host='127.0.0.1', port=5002)