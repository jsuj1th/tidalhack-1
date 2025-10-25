#!/usr/bin/env python3
"""
Simple web interface to test the hackathon feedback agent locally
"""
from flask import Flask, render_template, request, jsonify
import asyncio
import json
from datetime import datetime
import os
import sys

# Add the hackathon-feedback-system directory to path
sys.path.append('hackathon-feedback-system')

from functions import (
    store_feedback, 
    analyze_feedback_sentiment, 
    categorize_feedback,
    validate_feedback,
    get_feedback_summary
)
from ai_functions import (
    ai_analyze_feedback,
    ai_generate_response,
    ai_detect_spam
)
from config import HACKATHON_NAME, HACKATHON_ID

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('test_interface.html', hackathon_name=HACKATHON_NAME)

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.json
        feedback_text = data.get('feedback', '').strip()
        user_email = data.get('email', '').strip()
        
        if not feedback_text:
            return jsonify({'error': 'Feedback text is required'}), 400
        
        # Validate feedback
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        is_valid, error_msg = loop.run_until_complete(validate_feedback(feedback_text))
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Analyze feedback
        sentiment = loop.run_until_complete(analyze_feedback_sentiment(feedback_text))
        category = loop.run_until_complete(categorize_feedback(feedback_text))
        
        # AI analysis (if available)
        ai_analysis = {}
        try:
            ai_result = loop.run_until_complete(ai_analyze_feedback(feedback_text))
            ai_analysis = ai_result
        except Exception as e:
            print(f"AI analysis failed: {e}")
        
        # Generate AI response
        ai_response = ""
        try:
            ai_response = loop.run_until_complete(ai_generate_response(feedback_text, ai_analysis))
        except Exception as e:
            print(f"AI response failed: {e}")
            ai_response = f"🎉 Thank you for your feedback about {HACKATHON_NAME}! Your input helps us make the event better."
        
        # Store feedback
        feedback_data = {
            "feedback_id": f"web_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_email": user_email,
            "feedback_text": feedback_text,
            "timestamp": datetime.now().isoformat(),
            "hackathon_id": HACKATHON_ID,
            "analysis": {
                "sentiment": sentiment,
                "category": category,
                **ai_analysis
            },
            "metadata": {
                "source": "web_interface",
                "message_length": len(feedback_text)
            }
        }
        
        loop.run_until_complete(store_feedback(feedback_data))
        
        return jsonify({
            'success': True,
            'message': 'Feedback submitted successfully!',
            'analysis': {
                'sentiment': sentiment,
                'category': category,
                'ai_analysis': ai_analysis
            },
            'ai_response': ai_response
        })
        
    except Exception as e:
        print(f"Error processing feedback: {e}")
        return jsonify({'error': 'Failed to process feedback'}), 500

@app.route('/analytics')
def analytics():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        summary = loop.run_until_complete(get_feedback_summary(HACKATHON_ID))
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/feedback_data')
def feedback_data():
    try:
        if os.path.exists('hackathon-feedback-system/feedback_data.json'):
            with open('hackathon-feedback-system/feedback_data.json', 'r') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory
    os.makedirs('templates', exist_ok=True)
    
    # Create the HTML template
    html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ hackathon_name }} - Feedback Test Interface</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
        }
        input, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        textarea {
            height: 120px;
            resize: vertical;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .response {
            margin-top: 20px;
            padding: 20px;
            border-radius: 8px;
            display: none;
        }
        .success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .analysis {
            background: #e2e3e5;
            border: 1px solid #d6d8db;
            color: #383d41;
            margin-top: 10px;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #e1e5e9;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.3s;
        }
        .tab.active {
            border-bottom-color: #667eea;
            color: #667eea;
            font-weight: 600;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .analytics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .metric-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .metric-label {
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 {{ hackathon_name }}</h1>
        <p class="subtitle">Feedback Collection Test Interface</p>
        
        <div class="tabs">
            <div class="tab active" onclick="showTab('feedback')">Submit Feedback</div>
            <div class="tab" onclick="showTab('analytics')">Analytics</div>
            <div class="tab" onclick="showTab('data')">Raw Data</div>
        </div>
        
        <div id="feedback-tab" class="tab-content active">
            <form id="feedbackForm">
                <div class="form-group">
                    <label for="email">Email (Optional):</label>
                    <input type="email" id="email" placeholder="your.email@example.com">
                </div>
                
                <div class="form-group">
                    <label for="feedback">Your Feedback:</label>
                    <textarea id="feedback" placeholder="Share your thoughts about the hackathon - what are you hoping to learn, what excites you, any suggestions..." required></textarea>
                </div>
                
                <button type="submit" id="submitBtn">Submit Feedback</button>
            </form>
            
            <div id="response" class="response"></div>
        </div>
        
        <div id="analytics-tab" class="tab-content">
            <h3>📊 Feedback Analytics</h3>
            <button onclick="loadAnalytics()">Refresh Analytics</button>
            <div id="analytics-content"></div>
        </div>
        
        <div id="data-tab" class="tab-content">
            <h3>📋 Raw Feedback Data</h3>
            <button onclick="loadRawData()">Refresh Data</button>
            <div id="raw-data-content"></div>
        </div>
    </div>

    <script>
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
        }
        
        document.getElementById('feedbackForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = document.getElementById('submitBtn');
            const responseDiv = document.getElementById('response');
            
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';
            
            const formData = {
                feedback: document.getElementById('feedback').value,
                email: document.getElementById('email').value
            };
            
            try {
                const response = await fetch('/submit_feedback', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    responseDiv.className = 'response success';
                    responseDiv.innerHTML = `
                        <h4>✅ ${result.message}</h4>
                        <div class="analysis">
                            <strong>Analysis:</strong><br>
                            Sentiment: ${result.analysis.sentiment}<br>
                            Category: ${result.analysis.category}
                        </div>
                        <div class="analysis">
                            <strong>AI Response:</strong><br>
                            ${result.ai_response}
                        </div>
                    `;
                    document.getElementById('feedback').value = '';
                    document.getElementById('email').value = '';
                } else {
                    responseDiv.className = 'response error';
                    responseDiv.innerHTML = `<h4>❌ Error: ${result.error}</h4>`;
                }
                
                responseDiv.style.display = 'block';
                
            } catch (error) {
                responseDiv.className = 'response error';
                responseDiv.innerHTML = `<h4>❌ Network Error: ${error.message}</h4>`;
                responseDiv.style.display = 'block';
            }
            
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Feedback';
        });
        
        async function loadAnalytics() {
            try {
                const response = await fetch('/analytics');
                const data = await response.json();
                
                const content = document.getElementById('analytics-content');
                
                if (data.error) {
                    content.innerHTML = `<p>Error: ${data.error}</p>`;
                    return;
                }
                
                content.innerHTML = `
                    <div class="analytics-grid">
                        <div class="metric-card">
                            <div class="metric-value">${data.total_feedback || 0}</div>
                            <div class="metric-label">Total Feedback</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${data.sentiment_distribution?.positive || 0}</div>
                            <div class="metric-label">Positive</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${data.sentiment_distribution?.negative || 0}</div>
                            <div class="metric-label">Negative</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${data.sentiment_distribution?.neutral || 0}</div>
                            <div class="metric-label">Neutral</div>
                        </div>
                    </div>
                    <h4>Category Distribution:</h4>
                    <pre>${JSON.stringify(data.category_distribution || {}, null, 2)}</pre>
                `;
            } catch (error) {
                document.getElementById('analytics-content').innerHTML = `<p>Error loading analytics: ${error.message}</p>`;
            }
        }
        
        async function loadRawData() {
            try {
                const response = await fetch('/feedback_data');
                const data = await response.json();
                
                document.getElementById('raw-data-content').innerHTML = `
                    <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;">${JSON.stringify(data, null, 2)}</pre>
                `;
            } catch (error) {
                document.getElementById('raw-data-content').innerHTML = `<p>Error loading data: ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
    '''
    
    with open('templates/test_interface.html', 'w') as f:
        f.write(html_template)
    
    print("🚀 Starting Web Test Interface...")
    print("📱 Open your browser and go to: http://localhost:5001")
    print("🔧 This interface will test your feedback system locally")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5001)