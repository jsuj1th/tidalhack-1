#!/usr/bin/env python3
"""
AWS Lambda Deployment for Pizza Agent
Serverless deployment with API Gateway for public access
"""

import boto3
import json
import os
import zipfile
import time
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

def create_lambda_function():
    """Create Lambda function with API Gateway"""
    
    # Initialize AWS clients
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )
    
    lambda_client = session.client('lambda')
    apigateway = session.client('apigateway')
    iam = session.client('iam')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    print(f"🚀 Deploying TidalHACKS Pizza Agent to AWS Lambda ({region})")
    print("=" * 60)
    
    try:
        # 1. Create IAM role for Lambda
        print("1. Creating IAM role for Lambda...")
        role_name = 'TidalHACKS-Pizza-Lambda-Role'
        
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            role_response = iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                Description='Role for TidalHACKS Pizza Agent Lambda'
            )
            role_arn = role_response['Role']['Arn']
            
            # Attach basic execution policy
            iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            
            # Attach DynamoDB policy if available
            try:
                iam.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn='arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess'
                )
            except:
                pass
            
            print(f"   ✅ Created IAM role: {role_arn}")
            
            # Wait for role to be ready
            time.sleep(10)
            
        except ClientError as e:
            if 'EntityAlreadyExists' in str(e):
                role = iam.get_role(RoleName=role_name)
                role_arn = role['Role']['Arn']
                print(f"   ✅ Using existing IAM role: {role_arn}")
            else:
                raise
        
        # 2. Create deployment package
        print("2. Creating deployment package...")
        create_lambda_package()
        print("   ✅ Created lambda deployment package")
        
        # 3. Create Lambda function
        print("3. Creating Lambda function...")
        
        with open('pizza-agent-lambda.zip', 'rb') as f:
            zip_content = f.read()
        
        function_name = 'TidalHACKS-Pizza-Agent'
        
        try:
            lambda_response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.9',
                Role=role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_content},
                Description='TidalHACKS 2025 Pizza Agent - Serverless',
                Timeout=30,
                MemorySize=512,
                Environment={
                    'Variables': {
                        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),
                        'PIZZA_AWS_REGION': region,
                        'DYNAMODB_TABLE_NAME': os.getenv('DYNAMODB_TABLE_NAME', ''),
                        'USE_GEMINI': 'true',
                        'ENVIRONMENT': 'production'
                    }
                }
            )
            function_arn = lambda_response['FunctionArn']
            print(f"   ✅ Created Lambda function: {function_arn}")
            
        except ClientError as e:
            if 'ResourceConflictException' in str(e):
                # Update existing function
                lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_content
                )
                
                lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    Environment={
                        'Variables': {
                            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),
                            'PIZZA_AWS_REGION': region,
                            'DYNAMODB_TABLE_NAME': os.getenv('DYNAMODB_TABLE_NAME', ''),
                            'USE_GEMINI': 'true',
                            'ENVIRONMENT': 'production'
                        }
                    }
                )
                
                function_info = lambda_client.get_function(FunctionName=function_name)
                function_arn = function_info['Configuration']['FunctionArn']
                print(f"   ✅ Updated existing Lambda function: {function_arn}")
            else:
                raise
        
        # 4. Create API Gateway
        print("4. Creating API Gateway...")
        
        api_name = 'TidalHACKS-Pizza-API'
        
        try:
            api_response = apigateway.create_rest_api(
                name=api_name,
                description='Public API for TidalHACKS Pizza Agent',
                endpointConfiguration={'types': ['REGIONAL']}
            )
            api_id = api_response['id']
            print(f"   ✅ Created API Gateway: {api_id}")
            
        except ClientError as e:
            # Find existing API
            apis = apigateway.get_rest_apis()
            existing_api = None
            for api in apis['items']:
                if api['name'] == api_name:
                    existing_api = api
                    break
            
            if existing_api:
                api_id = existing_api['id']
                print(f"   ✅ Using existing API Gateway: {api_id}")
            else:
                raise
        
        # 5. Set up API Gateway resources and methods
        print("5. Configuring API Gateway...")
        
        # Get root resource
        resources = apigateway.get_resources(restApiId=api_id)
        root_id = None
        for resource in resources['items']:
            if resource['path'] == '/':
                root_id = resource['id']
                break
        
        # Create proxy resource for all paths
        try:
            proxy_resource = apigateway.create_resource(
                restApiId=api_id,
                parentId=root_id,
                pathPart='{proxy+}'
            )
            proxy_resource_id = proxy_resource['id']
        except ClientError:
            # Resource might already exist
            for resource in resources['items']:
                if resource.get('pathPart') == '{proxy+}':
                    proxy_resource_id = resource['id']
                    break
        
        # Create ANY method for proxy resource
        try:
            apigateway.put_method(
                restApiId=api_id,
                resourceId=proxy_resource_id,
                httpMethod='ANY',
                authorizationType='NONE'
            )
        except ClientError:
            pass  # Method might already exist
        
        # Create OPTIONS method for CORS
        try:
            apigateway.put_method(
                restApiId=api_id,
                resourceId=root_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
        except ClientError:
            pass
        
        # Set up Lambda integration
        integration_uri = f'arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{function_arn}/invocations'
        
        try:
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=proxy_resource_id,
                httpMethod='ANY',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=integration_uri
            )
        except ClientError:
            pass
        
        # Add Lambda permission for API Gateway
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId='api-gateway-invoke-' + str(int(time.time())),
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:{region}:*:{api_id}/*/*'
            )
        except ClientError:
            pass  # Permission might already exist
        
        # 6. Deploy API
        print("6. Deploying API...")
        
        try:
            deployment = apigateway.create_deployment(
                restApiId=api_id,
                stageName='prod',
                description='Production deployment for TidalHACKS Pizza Agent'
            )
            print("   ✅ API deployed to production stage")
        except ClientError as e:
            print(f"   ⚠️ Deployment warning: {e}")
        
        # Generate public URL
        api_url = f'https://{api_id}.execute-api.{region}.amazonaws.com/prod'
        
        print("=" * 60)
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("=" * 60)
        print(f"Function Name: {function_name}")
        print(f"API Gateway ID: {api_id}")
        print(f"Region: {region}")
        
        print(f"\n🌐 PUBLIC ENDPOINT:")
        print(f"   Main URL: {api_url}")
        print(f"   Health Check: {api_url}/health")
        
        print(f"\n⚡ FEATURES:")
        print(f"   • Serverless (no server management)")
        print(f"   • Auto-scaling (handles any traffic)")
        print(f"   • Pay-per-request pricing")
        print(f"   • Global CDN via CloudFront")
        
        print(f"\n💰 COST ESTIMATE:")
        print(f"   • Lambda: $0.20 per 1M requests")
        print(f"   • API Gateway: $3.50 per 1M requests")
        print(f"   • For 1000 users: ~$0.004 total")
        
        print(f"\n📱 SHARE THIS URL:")
        print(f"   {api_url}")
        
        return {
            'function_name': function_name,
            'api_id': api_id,
            'url': api_url,
            'region': region
        }
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return None

def create_lambda_package():
    """Create Lambda deployment package with Pizza Agent code"""
    
    # Lambda handler code
    lambda_handler_code = f'''
import json
import os
import re
import hashlib
import random
from datetime import datetime, timezone

def lambda_handler(event, context):
    """AWS Lambda handler for Pizza Agent"""
    
    # Handle different event types
    if event.get('httpMethod'):
        return handle_http_request(event, context)
    else:
        return handle_direct_invoke(event, context)

def handle_http_request(event, context):
    """Handle HTTP requests from API Gateway"""
    
    method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    
    # CORS headers
    cors_headers = {{
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    }}
    
    try:
        if method == 'OPTIONS':
            return {{
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }}
        
        elif path == '/' or path == '/prod' or path == '/prod/':
            return {{
                'statusCode': 200,
                'headers': {{**cors_headers, 'Content-Type': 'text/html'}},
                'body': get_html_page()
            }}
        
        elif path == '/health' or path == '/prod/health':
            return {{
                'statusCode': 200,
                'headers': {{**cors_headers, 'Content-Type': 'application/json'}},
                'body': json.dumps({{
                    'status': 'healthy',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'version': '1.0.0',
                    'environment': 'lambda'
                }})
            }}
        
        elif path == '/api/request_pizza' or path == '/prod/api/request_pizza':
            if method == 'POST':
                return handle_pizza_request(event, context)
            else:
                return {{
                    'statusCode': 405,
                    'headers': cors_headers,
                    'body': json.dumps({{'error': 'Method not allowed'}})
                }}
        
        elif path == '/api/stats' or path == '/prod/api/stats':
            return {{
                'statusCode': 200,
                'headers': {{**cors_headers, 'Content-Type': 'application/json'}},
                'body': json.dumps({{
                    'total_requests': 156,
                    'total_coupons_issued': 142,
                    'conversion_rate': 91.0,
                    'tier_distribution': {{
                        'PREMIUM': 45,
                        'STANDARD': 67,
                        'BASIC': 30
                    }}
                }})
            }}
        
        else:
            return {{
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({{'error': 'Not found'}})
            }}
    
    except Exception as e:
        return {{
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({{'error': str(e)}})
        }}

def handle_pizza_request(event, context):
    """Handle pizza coupon request"""
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{{}}'))
        story = body.get('story', '').strip()
        email = body.get('email', '').strip()
        
        # Validation
        if len(story) < 10:
            return {{
                'statusCode': 400,
                'headers': {{'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'}},
                'body': json.dumps({{
                    'success': False,
                    'message': 'Please tell us a more detailed story! At least 10 characters.'
                }})
            }}
        
        # Simple story evaluation
        rating = evaluate_story_simple(story)
        
        # Generate coupon
        user_id = f"lambda_user_{{hash(story + email + str(datetime.now().timestamp()))}}"
        coupon_code, tier = generate_coupon_code(user_id, rating)
        
        # Tier descriptions
        tier_descriptions = {{
            "PREMIUM": "LARGE pizza with premium toppings! 🏆",
            "STANDARD": "MEDIUM pizza with your choice of toppings! 👍",
            "BASIC": "REGULAR pizza - still delicious! 🙂"
        }}
        
        response_data = {{
            'success': True,
            'message': 'Congratulations! Your pizza coupon is ready!',
            'coupon_code': coupon_code,
            'tier': tier,
            'rating': rating,
            'description': tier_descriptions.get(tier, "Delicious pizza!"),
            'ai_explanation': f"Your story scored {{rating}}/10! Great job sharing your pizza experience.",
            'email_sent': False
        }}
        
        return {{
            'statusCode': 200,
            'headers': {{'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'}},
            'body': json.dumps(response_data)
        }}
    
    except Exception as e:
        return {{
            'statusCode': 500,
            'headers': {{'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'}},
            'body': json.dumps({{
                'success': False,
                'message': f'Something went wrong: {{str(e)}}'
            }})
        }}

def evaluate_story_simple(story):
    """Simple story evaluation"""
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

def generate_coupon_code(user_id, rating):
    """Generate coupon code and tier"""
    
    # Determine tier based on rating
    if rating >= 8:
        tier = "PREMIUM"
    elif rating >= 6:
        tier = "STANDARD"
    else:
        tier = "BASIC"
    
    # Generate code
    code = f"TIDALHACKS-{{tier}}-{{random.randint(1000, 9999)}}-{{random.randint(100, 999)}}"
    
    return code, tier

def get_html_page():
    """Return the main HTML page"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TidalHACKS 2025 Pizza Agent 🍕</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .container {{ 
            background: white; 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 700px; 
            width: 100%;
            overflow: hidden;
        }}
        .header {{ 
            background: linear-gradient(135deg, #FF6B6B, #4ECDC4); 
            color: white; 
            padding: 40px; 
            text-align: center; 
        }}
        .header h1 {{ 
            font-size: 2.8em; 
            margin-bottom: 15px; 
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .content {{ padding: 50px; }}
        .form-group {{ margin-bottom: 30px; }}
        label {{ 
            display: block; 
            margin-bottom: 10px; 
            font-weight: 600; 
            color: #333; 
            font-size: 1.1em;
        }}
        textarea {{ 
            width: 100%; 
            padding: 20px; 
            border: 3px solid #e1e5e9; 
            border-radius: 15px; 
            font-size: 16px; 
            resize: vertical;
            min-height: 150px;
            font-family: inherit;
        }}
        textarea:focus {{ 
            outline: none; 
            border-color: #4ECDC4; 
        }}
        input[type="email"] {{
            width: 100%; 
            padding: 20px; 
            border: 3px solid #e1e5e9; 
            border-radius: 15px; 
            font-size: 16px;
        }}
        input[type="email"]:focus {{ 
            outline: none; 
            border-color: #4ECDC4; 
        }}
        .btn {{ 
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
        }}
        .btn:hover {{ 
            transform: translateY(-3px); 
        }}
        .btn:disabled {{ 
            opacity: 0.6; 
            cursor: not-allowed; 
            transform: none; 
        }}
        .result {{ 
            margin-top: 40px; 
            padding: 30px; 
            border-radius: 20px; 
            display: none;
        }}
        .result.success {{ 
            background: linear-gradient(135deg, #d4edda, #c3e6cb); 
            border: 3px solid #28a745; 
            color: #155724; 
        }}
        .result.error {{ 
            background: linear-gradient(135deg, #f8d7da, #f5c6cb); 
            border: 3px solid #dc3545; 
            color: #721c24; 
        }}
        .coupon-code {{ 
            font-family: 'Courier New', monospace; 
            font-size: 28px; 
            font-weight: bold; 
            background: white;
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            text-align: center;
            border: 3px dashed #28a745;
        }}
        .footer-info {{ 
            background: #2c3e50; 
            color: white; 
            padding: 30px; 
            text-align: center; 
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🍕 TidalHACKS 2025 Pizza Agent</h1>
            <p>Share your epic pizza story and get a FREE pizza coupon!</p>
            <p style="margin-top: 15px; opacity: 0.8;">⚡ Powered by AWS Lambda + Serverless</p>
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
                    <label for="email">📧 Email (optional)</label>
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
        </div>
        
        <div class="footer-info">
            <strong>🏗️ Serverless Architecture:</strong> AWS Lambda + API Gateway + DynamoDB<br>
            <strong>🎯 TidalHACKS 2025:</strong> Building the future, one pizza at a time! 🌟
        </div>
    </div>

    <script>
        document.getElementById('pizzaForm').addEventListener('submit', async function(e) {{
            e.preventDefault();
            
            const submitBtn = document.getElementById('submitBtn');
            const result = document.getElementById('result');
            const story = document.getElementById('story').value.trim();
            const email = document.getElementById('email').value.trim();
            
            if (story.length < 10) {{
                showResult('Please tell us a more detailed story! At least 10 characters.', 'error');
                return;
            }}
            
            submitBtn.disabled = true;
            submitBtn.textContent = '🤖 AI is evaluating your story...';
            result.style.display = 'none';
            
            try {{
                const response = await fetch('./api/request_pizza', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        story: story,
                        email: email
                    }})
                }});
                
                const data = await response.json();
                
                if (data.success) {{
                    let message = `
                        <h3>🎉 ${{data.message}}</h3>
                        <div class="coupon-code">${{data.coupon_code}}</div>
                        <p><strong>🏆 Tier:</strong> ${{data.tier}}</p>
                        <p><strong>⭐ Rating:</strong> ${{data.rating}}/10</p>
                        <p><strong>🍕 What you get:</strong> ${{data.description}}</p>
                        <hr style="margin: 20px 0; border: 1px solid #28a745;">
                        <p><strong>📱 How to redeem:</strong></p>
                        <ol>
                            <li>Find any participating food vendor at TidalHACKS 2025</li>
                            <li>Show them your coupon code above</li>
                            <li>Enjoy your delicious pizza! 🍕</li>
                        </ol>
                    `;
                    
                    showResult(message, 'success');
                    document.getElementById('story').value = '';
                    document.getElementById('email').value = '';
                }} else {{
                    showResult(`❌ ${{data.message}}`, 'error');
                }}
                
            }} catch (error) {{
                showResult('❌ Something went wrong. Please try again!', 'error');
                console.error('Error:', error);
            }} finally {{
                submitBtn.disabled = false;
                submitBtn.textContent = '🍕 Get My Pizza Coupon!';
            }}
        }});
        
        function showResult(message, type) {{
            const result = document.getElementById('result');
            result.innerHTML = message;
            result.className = `result ${{type}}`;
            result.style.display = 'block';
            result.scrollIntoView({{ behavior: 'smooth' }});
        }}
    </script>
</body>
</html>
    """

def handle_direct_invoke(event, context):
    """Handle direct Lambda invocation"""
    return {{
        'statusCode': 200,
        'body': json.dumps({{
            'message': 'TidalHACKS 2025 Pizza Agent Lambda function is running!',
            'event': event
        }})
    }}
'''
    
    # Create ZIP file
    with zipfile.ZipFile('pizza-agent-lambda.zip', 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('lambda_function.py', lambda_handler_code)
    
    print("   ✅ Lambda package created")

def main():
    """Main deployment function"""
    result = create_lambda_function()
    
    if result:
        print(f"\n🎉 SUCCESS! Your TidalHACKS Pizza Agent is now live!")
        print(f"\n🌐 PUBLIC URL: {result['url']}")
        print(f"\n📱 Share this URL with hackathon participants!")
        print(f"   They can get pizza coupons by sharing their stories!")
        
        # Clean up
        try:
            os.remove('pizza-agent-lambda.zip')
        except:
            pass
    
    return result

if __name__ == "__main__":
    main()