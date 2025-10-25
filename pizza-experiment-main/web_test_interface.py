#!/usr/bin/env python3
"""
Simple web interface to test Pizza Agent functionality
This bypasses the uAgents framework and tests the core functions directly
"""

from flask import Flask, render_template_string, request, jsonify
import asyncio
from functions import generate_coupon_code, evaluate_story_quality
from ai_functions import ai_evaluate_story, ai_generate_personalized_response, ai_generate_dynamic_prompts
from gemini_functions import gemini_evaluate_story, gemini_generate_response_message, gemini_generate_unique_prompt
from config import USE_GEMINI, USE_AI_EVALUATION, USE_AI_RESPONSES, USE_AI_PROMPTS
from email_utils import send_coupon_email, test_email_configuration, validate_email
from user_config import get_user_email, get_test_config
import json

app = Flask(__name__)

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🍕 Pizza Agent Test Interface</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f8f9fa; }
        .container { background: #ffffff; padding: 25px; border-radius: 12px; margin: 15px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .response { background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 15px 0; border-left: 4px solid #4CAF50; }
        .error { background: #ffe8e8; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #f44336; }
        .status { background: #e8f4fd; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #2196F3; }
        
        textarea { width: 100%; height: 120px; padding: 12px; border-radius: 8px; border: 2px solid #ddd; font-family: inherit; resize: vertical; }
        textarea:focus { border-color: #4CAF50; outline: none; }
        
        button { background: #4CAF50; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; margin: 8px 5px; font-size: 14px; font-weight: 500; transition: all 0.3s; }
        button:hover { background: #45a049; transform: translateY(-1px); }
        button.secondary { background: #2196F3; }
        button.secondary:hover { background: #1976D2; }
        
        .copy-button { background: #FF9800; padding: 8px 16px; font-size: 12px; margin-left: 10px; }
        .copy-button:hover { background: #F57C00; }
        .copy-button.copied { background: #4CAF50; }
        
        .coupon-code { 
            background: #fff3cd; 
            border: 2px dashed #ffc107; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 10px 0; 
            font-family: 'Courier New', monospace; 
            font-size: 18px; 
            font-weight: bold; 
            text-align: center;
            position: relative;
        }
        
        .email-section {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
        }
        
        .email-input {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            margin: 8px 0;
        }
        
        .email-input:focus {
            border-color: #4CAF50;
            outline: none;
        }
        
        .email-buttons {
            display: flex;
            gap: 10px;
            margin-top: 10px;
            flex-wrap: wrap;
        }
        
        .email-status {
            margin-top: 10px;
            padding: 10px;
            border-radius: 6px;
            font-size: 14px;
        }
        
        .email-status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .email-status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .email-status.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .markdown-content {
            line-height: 1.6;
            color: #333;
        }
        .markdown-content h1, .markdown-content h2, .markdown-content h3, .markdown-content h4 {
            color: #2c3e50;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .markdown-content p { margin: 10px 0; }
        .markdown-content strong { color: #e74c3c; font-weight: 600; }
        .markdown-content em { color: #8e44ad; font-style: italic; }
        .markdown-content ul, .markdown-content ol { margin: 10px 0; padding-left: 25px; }
        .markdown-content li { margin: 5px 0; }
        .markdown-content code { 
            background: #f8f9fa; 
            padding: 2px 6px; 
            border-radius: 4px; 
            font-family: 'Courier New', monospace; 
            color: #e74c3c;
        }
        .markdown-content blockquote {
            border-left: 4px solid #3498db;
            margin: 15px 0;
            padding: 10px 20px;
            background: #f8f9fa;
            font-style: italic;
        }
        
        .rating-display {
            display: inline-block;
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            margin: 5px;
        }
        
        .tier-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 15px;
            font-weight: bold;
            font-size: 12px;
            text-transform: uppercase;
            margin: 5px;
        }
        .tier-premium { background: #FFD700; color: #8B4513; }
        .tier-standard { background: #C0C0C0; color: #2F4F4F; }
        .tier-basic { background: #CD7F32; color: white; }
        
        .loading { 
            display: inline-block; 
            width: 20px; 
            height: 20px; 
            border: 3px solid #f3f3f3; 
            border-top: 3px solid #3498db; 
            border-radius: 50%; 
            animation: spin 1s linear infinite; 
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .toast.show { opacity: 1; }
    </style>
</head>
<body>
    <h1>🍕 Pizza Agent Test Interface</h1>
    
    <div class="status">
        <h3>🔧 Configuration Status</h3>
        <p><strong>USE_GEMINI:</strong> {{ config.USE_GEMINI }}</p>
        <p><strong>USE_AI_EVALUATION:</strong> {{ config.USE_AI_EVALUATION }}</p>
        <p><strong>USE_AI_RESPONSES:</strong> {{ config.USE_AI_RESPONSES }}</p>
        <p><strong>USE_AI_PROMPTS:</strong> {{ config.USE_AI_PROMPTS }}</p>
        <p><strong>EMAIL_CONFIGURED:</strong> <span id="emailStatus">Checking...</span></p>
    </div>
    
    <div class="container">
        <h3>🍕 How It Works</h3>
        <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #4CAF50;">
            <p><strong>🎯 Share your pizza story → Get AI rating → Receive coupon → Redeem at CalHacks!</strong></p>
            <ul style="margin: 10px 0;">
                <li><strong>Better stories = Better coupons!</strong> (Premium/Standard/Basic tiers)</li>
                <li><strong>Show your coupon code</strong> to any food vendor at the conference</li>
                <li><strong>Get it via email</strong> for easy access on your phone</li>
            </ul>
        </div>
    </div>
    
    <div class="container">
        <h3>📖 Test Story Evaluation</h3>
        <p>Enter your pizza story below and test how the AI evaluates it:</p>
        <textarea id="story" placeholder="Enter your pizza story here...">I had the most amazing pizza during my last hackathon! I was coding until 3am and getting really tired. Then my teammate ordered this incredible pepperoni pizza with extra cheese. The moment I took a bite, I got a burst of energy and solved the bug I'd been working on for hours! That pizza literally saved our project and we ended up winning second place. Best pizza ever! 🍕</textarea>
        <br>
        <button onclick="evaluateStory()">📊 Evaluate Story</button>
        <button class="secondary" onclick="generateCoupon()">🎫 Generate Full Coupon Response</button>
        <div id="storyResult"></div>
    </div>
    
    <div class="container">
        <h3>✨ Test Dynamic Prompt Generation</h3>
        <p>Generate creative, AI-powered prompts for pizza stories:</p>
        <button onclick="generatePrompt()">🎭 Generate New Prompt</button>
        <div id="promptResult"></div>
    </div>
    
    <div class="container">
        <h3>🎯 Test Complete Workflow</h3>
        <p>Test the entire pizza agent process from prompt to coupon:</p>
        <button onclick="testFullWorkflow()">🚀 Test Full Pizza Agent Workflow</button>
        <div id="workflowResult"></div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
        // Toast notification function
        function showToast(message, type = 'success') {
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => toast.classList.add('show'), 100);
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => document.body.removeChild(toast), 300);
            }, 3000);
        }
        
        // Copy to clipboard function
        function copyToClipboard(text, buttonElement) {
            navigator.clipboard.writeText(text).then(() => {
                const originalText = buttonElement.textContent;
                buttonElement.textContent = '✅ Copied!';
                buttonElement.classList.add('copied');
                showToast('Coupon code copied to clipboard!');
                
                setTimeout(() => {
                    buttonElement.textContent = originalText;
                    buttonElement.classList.remove('copied');
                }, 2000);
            }).catch(() => {
                showToast('Failed to copy to clipboard', 'error');
            });
        }
        
        // Markdown rendering function
        function renderMarkdown(text) {
            // Configure marked for better rendering
            marked.setOptions({
                breaks: true,
                gfm: true
            });
            return marked.parse(text);
        }
        
        // Format rating display
        function formatRating(rating) {
            return `<span class="rating-display">⭐ ${rating}/10</span>`;
        }
        
        // Format tier badge
        function formatTier(tier) {
            const tierClass = tier.toLowerCase().replace(/[^a-z]/g, '');
            return `<span class="tier-badge tier-${tierClass}">${tier}</span>`;
        }
        
        async function evaluateStory() {
            const button = event.target;
            const originalText = button.textContent;
            button.innerHTML = '<span class="loading"></span> Evaluating...';
            button.disabled = true;
            
            try {
                const story = document.getElementById('story').value;
                const response = await fetch('/evaluate_story', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({story: story})
                });
                const result = await response.json();
                
                document.getElementById('storyResult').innerHTML = 
                    `<div class="response">
                        <h4>📊 Story Evaluation Result</h4>
                        <p><strong>Rating:</strong> ${formatRating(result.rating)}</p>
                        <div class="markdown-content">
                            <p><strong>Explanation:</strong> ${result.explanation}</p>
                        </div>
                        <p><strong>Method:</strong> <code>${result.method}</code></p>
                        
                        <div style="background: #fff3cd; border: 2px dashed #ffc107; padding: 15px; border-radius: 8px; margin: 15px 0; text-align: center;">
                            <p style="margin: 5px 0;"><strong>💡 Want a coupon?</strong></p>
                            <p style="margin: 5px 0;">Click "Generate Full Coupon Response" above to get your pizza coupon with redemption instructions!</p>
                        </div>
                    </div>`;
            } finally {
                button.textContent = originalText;
                button.disabled = false;
            }
        }
        
        async function generateCoupon() {
            const button = event.target;
            const originalText = button.textContent;
            button.innerHTML = '<span class="loading"></span> Generating...';
            button.disabled = true;
            
            try {
                const story = document.getElementById('story').value;
                const response = await fetch('/generate_coupon', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({story: story})
                });
                const result = await response.json();
                
                document.getElementById('storyResult').innerHTML = 
                    `<div class="response">
                        <h4>🎫 Complete Coupon Response</h4>
                        
                        <div class="coupon-code">
                            ${result.coupon_code}
                            <button class="copy-button" onclick="copyToClipboard('${result.coupon_code}', this)">
                                📋 Copy Code
                            </button>
                        </div>
                        
                        <p><strong>Tier:</strong> ${formatTier(result.tier)}</p>
                        <p><strong>Rating:</strong> ${formatRating(result.rating)}</p>
                        
                        <div class="instructions" style="background: #e8f4fd; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #2196F3;">
                            <h5 style="margin-top: 0; color: #2196F3;"><span style="font-size: 1.2em;">📱</span> How to Redeem Your Coupon</h5>
                            <ol style="margin: 10px 0; padding-left: 25px;">
                                <li>Find any participating food vendor at CalHacks 12.0</li>
                                <li>Show them this coupon code: <strong style="color: #e74c3c;">${result.coupon_code}</strong></li>
                                <li>Enjoy your delicious ${result.tier.toLowerCase()} pizza! <span style="font-size: 1.2em;">🍕</span></li>
                            </ol>
                            
                            <p><strong>What you get:</strong></p>
                            <ul style="margin: 10px 0; padding-left: 25px;">
                                ${result.tier === "PREMIUM" ? "<li>🏆 LARGE pizza with premium toppings!</li>" : ""}
                                ${result.tier === "STANDARD" ? "<li>👍 MEDIUM pizza with your choice of toppings!</li>" : ""}
                                ${result.tier === "BASIC" ? "<li>🙂 REGULAR pizza - still delicious!</li>" : ""}
                            </ul>
                        </div>
                        
                        <div class="email-section">
                            <h5>📧 Email Coupon Option</h5>
                            <p>Want to receive this coupon via email? Enter your email address:</p>
                            <input type="email" class="email-input" id="emailInput-${Date.now()}" placeholder="your.email@example.com" value="{{ default_email }}">
                            <div class="email-buttons">
                                <button class="secondary" onclick="sendCouponEmail('${result.coupon_code}', '${result.tier}', ${result.rating}, \`${result.response.replace(/`/g, '\\\\`')}\`, this)">
                                    📧 Send via Email
                                </button>
                            </div>
                            <div id="emailResult-${Date.now()}" class="email-status" style="display: none;"></div>
                        </div>
                        
                        <h5>🤖 Agent Response:</h5>
                        <div class="markdown-content" style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50;">
                            ${renderMarkdown(result.response)}
                        </div>
                    </div>`;
            } finally {
                button.textContent = originalText;
                button.disabled = false;
            }
        }
        
        async function generatePrompt() {
            const button = event.target;
            const originalText = button.textContent;
            button.innerHTML = '<span class="loading"></span> Generating...';
            button.disabled = true;
            
            try {
                const response = await fetch('/generate_prompt');
                const result = await response.json();
                
                document.getElementById('promptResult').innerHTML = 
                    `<div class="response">
                        <h4>🎭 Generated Prompt</h4>
                        <div class="markdown-content" style="background: white; padding: 15px; border-radius: 8px;">
                            ${renderMarkdown(result.prompt)}
                        </div>
                        <p><strong>Method:</strong> <code>${result.method}</code></p>
                    </div>`;
            } finally {
                button.textContent = originalText;
                button.disabled = false;
            }
        }
        
        async function testFullWorkflow() {
            const button = event.target;
            const originalText = button.textContent;
            button.innerHTML = '<span class="loading"></span> Testing...';
            button.disabled = true;
            
            document.getElementById('workflowResult').innerHTML = '<p><span class="loading"></span> Testing full workflow...</p>';
            
            try {
                const response = await fetch('/test_workflow');
                const result = await response.json();
                
                let html = '<div class="response"><h4>🚀 Full Workflow Test</h4>';
                result.steps.forEach((step, index) => {
                    html += `<div style="margin: 15px 0; padding: 15px; background: white; border-radius: 8px; border-left: 4px solid #2196F3;">
                        <h5>Step ${index + 1}: ${step.name}</h5>
                        <div class="markdown-content">
                            ${renderMarkdown(step.result)}
                        </div>
                    </div>`;
                });
                html += '</div>';
                
                document.getElementById('workflowResult').innerHTML = html;
            } finally {
                button.textContent = originalText;
                button.disabled = false;
            }
        }
        
        // Send coupon via email
        async function sendCouponEmail(couponCode, tier, rating, response, buttonElement) {
            const emailInput = buttonElement.parentElement.parentElement.querySelector('.email-input');
            const emailResult = buttonElement.parentElement.parentElement.querySelector('.email-status');
            const email = emailInput.value.trim();
            
            if (!email) {
                emailResult.textContent = 'Please enter an email address';
                emailResult.className = 'email-status error';
                emailResult.style.display = 'block';
                return;
            }
            
            // Basic email validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                emailResult.textContent = 'Please enter a valid email address';
                emailResult.className = 'email-status error';
                emailResult.style.display = 'block';
                return;
            }
            
            const originalText = buttonElement.textContent;
            buttonElement.innerHTML = '<span class="loading"></span> Sending...';
            buttonElement.disabled = true;
            
            try {
                const emailResponse = await fetch('/send_coupon_email', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        email: email,
                        coupon_code: couponCode,
                        tier: tier,
                        rating: rating,
                        personalized_message: response
                    })
                });
                
                const result = await emailResponse.json();
                
                if (result.success) {
                    emailResult.textContent = `✅ ${result.message}`;
                    emailResult.className = 'email-status success';
                    showToast('Coupon sent via email successfully!');
                    emailInput.value = ''; // Clear the input
                } else {
                    emailResult.textContent = `❌ ${result.message}`;
                    emailResult.className = 'email-status error';
                    showToast('Failed to send email', 'error');
                }
                
                emailResult.style.display = 'block';
                
            } catch (error) {
                emailResult.textContent = `❌ Error: ${error.message}`;
                emailResult.className = 'email-status error';
                emailResult.style.display = 'block';
                showToast('Failed to send email', 'error');
            } finally {
                buttonElement.textContent = originalText;
                buttonElement.disabled = false;
            }
        }
        
        // Check email configuration on page load
        async function checkEmailConfiguration() {
            try {
                const response = await fetch('/check_email_config');
                const result = await response.json();
                const statusElement = document.getElementById('emailStatus');
                
                if (result.configured) {
                    statusElement.textContent = '✅ Configured';
                    statusElement.style.color = '#28a745';
                } else {
                    statusElement.textContent = '❌ Not Configured';
                    statusElement.style.color = '#dc3545';
                    statusElement.title = result.message;
                }
            } catch (error) {
                document.getElementById('emailStatus').textContent = '❓ Unknown';
            }
        }
        
        // Auto-resize textarea
        document.addEventListener('DOMContentLoaded', function() {
            const textarea = document.getElementById('story');
            if (textarea) {
                textarea.addEventListener('input', function() {
                    this.style.height = 'auto';
                    this.style.height = Math.max(120, this.scrollHeight) + 'px';
                });
            }
            
            // Check email configuration
            checkEmailConfiguration();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page"""
    config_info = {
        'USE_GEMINI': USE_GEMINI,
        'USE_AI_EVALUATION': USE_AI_EVALUATION,
        'USE_AI_RESPONSES': USE_AI_RESPONSES,
        'USE_AI_PROMPTS': USE_AI_PROMPTS
    }
    default_email = get_user_email()
    return render_template_string(HTML_TEMPLATE, config=config_info, default_email=default_email)

@app.route('/evaluate_story', methods=['POST'])
def evaluate_story():
    """Evaluate a pizza story"""
    data = request.json
    story = data.get('story', '')
    
    try:
        if USE_AI_EVALUATION and USE_GEMINI:
            # Try Gemini evaluation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            rating, explanation = loop.run_until_complete(gemini_evaluate_story(story))
            method = "Gemini AI"
        else:
            # Fallback to rule-based
            rating = evaluate_story_quality(story)
            explanation = "Rule-based evaluation completed"
            method = "Rule-based fallback"
        
        return jsonify({
            'rating': rating,
            'explanation': explanation,
            'method': method
        })
    except Exception as e:
        return jsonify({
            'rating': 5,
            'explanation': f"Error occurred: {str(e)}",
            'method': "Error fallback"
        })

@app.route('/generate_coupon', methods=['POST'])
def generate_coupon():
    """Generate a complete coupon response"""
    data = request.json
    story = data.get('story', '')
    
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
        coupon_code, tier = generate_coupon_code("test_user", rating, True)
        
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
                response = f"🎉 Amazing story! Your coupon: **{coupon_code}** - Gets you a LARGE premium pizza! 🏆"
            elif rating >= 6:
                response = f"😊 Great story! Your coupon: **{coupon_code}** - Gets you a MEDIUM pizza! 👍"
            else:
                response = f"🍕 Thanks for sharing! Your coupon: **{coupon_code}** - Gets you a tasty pizza! 🙂"
        
        return jsonify({
            'coupon_code': coupon_code,
            'tier': tier,
            'rating': rating,
            'response': response
        })
    except Exception as e:
        return jsonify({
            'coupon_code': 'ERROR-CODE',
            'tier': 'BASIC',
            'rating': 5,
            'response': f"Error generating coupon: {str(e)}"
        })

@app.route('/generate_prompt')
def generate_prompt():
    """Generate a dynamic prompt"""
    try:
        if USE_AI_PROMPTS and USE_GEMINI:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            prompt = loop.run_until_complete(gemini_generate_unique_prompt())
            method = "Gemini AI"
        else:
            # Fallback prompt
            import random
            fallback_prompts = [
                "🍕💻 Hey CalHacks 12.0 hacker! Your code is compiling, time for a pizza break! ✨\n\nTell me YOUR pizza story!",
                "🧙‍♂️🍕 Greetings, CalHacks 12.0 code wizard! The Pizza Genie has materialized! ✨\n\nShare YOUR greatest pizza tale!",
                "🚨💻 ALERT: Pizza.js has detected a hacker in need at CalHacks 12.0! 🍕\n\nGit commit YOUR pizza story now!"
            ]
            prompt = random.choice(fallback_prompts)
            method = "Static fallback"
        
        return jsonify({
            'prompt': prompt,
            'method': method
        })
    except Exception as e:
        return jsonify({
            'prompt': f"Error generating prompt: {str(e)}",
            'method': "Error fallback"
        })

@app.route('/send_coupon_email', methods=['POST'])
def send_coupon_email_route():
    """Send coupon via email"""
    data = request.json
    email = data.get('email', '').strip()
    coupon_code = data.get('coupon_code', '')
    tier = data.get('tier', '')
    rating = data.get('rating', 5)
    personalized_message = data.get('personalized_message', '')
    
    if not email:
        return jsonify({"success": False, "message": "Email address is required"})
    
    if not validate_email(email):
        return jsonify({"success": False, "message": "Invalid email address format"})
    
    if not coupon_code:
        return jsonify({"success": False, "message": "Coupon code is required"})
    
    # Send the email
    result = send_coupon_email(email, coupon_code, tier, rating, personalized_message)
    return jsonify(result)

@app.route('/check_email_config')
def check_email_config():
    """Check if email is configured"""
    result = test_email_configuration()
    return jsonify(result)

@app.route('/test_workflow')
def test_workflow():
    """Test the complete pizza agent workflow"""
    test_story = "I had the most amazing pizza during my last hackathon! I was coding until 3am and getting really tired. Then my teammate ordered this incredible pepperoni pizza with extra cheese. The moment I took a bite, I got a burst of energy and solved the bug I'd been working on for hours! That pizza literally saved our project and we ended up winning second place. Best pizza ever! 🍕"
    
    steps = []
    
    try:
        # Step 1: Generate prompt
        if USE_AI_PROMPTS and USE_GEMINI:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            prompt = loop.run_until_complete(gemini_generate_unique_prompt())
            steps.append({"name": "Generate Prompt (Gemini)", "result": prompt[:200] + "..."})
        else:
            steps.append({"name": "Generate Prompt (Fallback)", "result": "Using static prompt template"})
        
        # Step 2: Evaluate story
        if USE_AI_EVALUATION and USE_GEMINI:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            rating, explanation = loop.run_until_complete(gemini_evaluate_story(test_story))
            steps.append({"name": "Evaluate Story (Gemini)", "result": f"Rating: {rating}/10 - {explanation}"})
        else:
            rating = evaluate_story_quality(test_story)
            steps.append({"name": "Evaluate Story (Fallback)", "result": f"Rating: {rating}/10 - Rule-based evaluation"})
        
        # Step 3: Generate coupon
        coupon_code, tier = generate_coupon_code("test_user", rating, True)
        steps.append({"name": "Generate Coupon", "result": f"Code: {coupon_code}, Tier: {tier}"})
        
        # Step 4: Generate response
        if USE_AI_RESPONSES and USE_GEMINI:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(
                gemini_generate_response_message(test_story, rating, tier, coupon_code)
            )
            steps.append({"name": "Generate Response (Gemini)", "result": response})
        else:
            response = f"Great story! Your coupon: {coupon_code} - Gets you a {tier} pizza!"
            steps.append({"name": "Generate Response (Fallback)", "result": response})
        
        return jsonify({"steps": steps})
        
    except Exception as e:
        steps.append({"name": "Error", "result": f"Workflow failed: {str(e)}"})
        return jsonify({"steps": steps})

if __name__ == '__main__':
    print("🍕 Starting Pizza Agent Web Test Interface")
    print("📱 Open your browser to: http://127.0.0.1:5003")
    print("🔧 This interface tests the pizza agent functionality directly")
    print()
    app.run(debug=True, host='127.0.0.1', port=5003)