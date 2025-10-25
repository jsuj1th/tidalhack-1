#!/usr/bin/env python3
"""
Bedrock Access Fix Script
Helps diagnose and resolve Bedrock access issues
"""

import boto3
import json
import os
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

load_dotenv()

def check_aws_credentials():
    """Check AWS credentials and permissions"""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        
        print("✅ AWS Credentials:")
        print(f"   Account: {identity.get('Account')}")
        print(f"   User ARN: {identity.get('Arn')}")
        print(f"   User ID: {identity.get('UserId')}")
        
        return True
    except Exception as e:
        print(f"❌ AWS credentials error: {e}")
        return False

def check_bedrock_regions():
    """Check Bedrock availability in different regions"""
    bedrock_regions = [
        'us-east-1',
        'us-west-2', 
        'eu-west-1',
        'ap-southeast-1',
        'ap-northeast-1'
    ]
    
    print("\n🌍 Checking Bedrock availability by region:")
    
    available_regions = []
    
    for region in bedrock_regions:
        try:
            bedrock = boto3.client('bedrock', region_name=region)
            models = bedrock.list_foundation_models()
            print(f"   {region}: ✅ Available ({len(models.get('modelSummaries', []))} models)")
            available_regions.append(region)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                print(f"   {region}: ❌ Access Denied")
            elif error_code == 'UnauthorizedOperation':
                print(f"   {region}: ❌ Unauthorized")
            else:
                print(f"   {region}: ❌ {error_code}")
        except Exception as e:
            print(f"   {region}: ❌ Not available")
    
    return available_regions

def check_iam_permissions():
    """Check IAM permissions for Bedrock"""
    try:
        iam = boto3.client('iam')
        sts = boto3.client('sts')
        
        # Get current user
        identity = sts.get_caller_identity()
        user_arn = identity.get('Arn', '')
        
        print(f"\n🔐 Checking IAM permissions for: {user_arn}")
        
        if ':user/' in user_arn:
            # It's an IAM user
            username = user_arn.split('/')[-1]
            
            # Get user policies
            try:
                user_policies = iam.list_attached_user_policies(UserName=username)
                inline_policies = iam.list_user_policies(UserName=username)
                
                print(f"   Attached policies: {len(user_policies.get('AttachedPolicies', []))}")
                print(f"   Inline policies: {len(inline_policies.get('PolicyNames', []))}")
                
                # Check for Bedrock permissions
                has_bedrock_access = False
                
                for policy in user_policies.get('AttachedPolicies', []):
                    if 'bedrock' in policy['PolicyName'].lower() or 'admin' in policy['PolicyName'].lower():
                        has_bedrock_access = True
                        print(f"   ✅ Found Bedrock policy: {policy['PolicyName']}")
                
                if not has_bedrock_access:
                    print("   ⚠️ No explicit Bedrock policies found")
                    
            except Exception as e:
                print(f"   ❌ Cannot check user policies: {e}")
        
        elif ':role/' in user_arn:
            print("   ℹ️ Using IAM role - check role policies in AWS console")
        
        return True
        
    except Exception as e:
        print(f"❌ IAM check failed: {e}")
        return False

def create_bedrock_policy():
    """Create a Bedrock IAM policy JSON"""
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "BedrockFullAccess",
                "Effect": "Allow",
                "Action": [
                    "bedrock:*"
                ],
                "Resource": "*"
            },
            {
                "Sid": "BedrockRuntimeAccess",
                "Effect": "Allow",
                "Action": [
                    "bedrock-runtime:*"
                ],
                "Resource": "*"
            }
        ]
    }
    
    with open('bedrock-full-access-policy.json', 'w') as f:
        json.dump(policy, f, indent=2)
    
    print("✅ Created bedrock-full-access-policy.json")
    print("\nTo apply this policy:")
    print("1. Go to AWS IAM Console")
    print("2. Find your user/role")
    print("3. Attach this policy")
    print("4. Or use AWS CLI:")
    print("   aws iam put-user-policy --user-name YOUR_USERNAME --policy-name BedrockAccess --policy-document file://bedrock-full-access-policy.json")

def test_bedrock_models():
    """Test access to specific models"""
    regions_to_test = ['us-east-1', 'us-west-2']
    models_to_test = [
        'google.gemini-1.5-pro-v1:0',
        'google.gemini-1.5-flash-v1:0', 
        'anthropic.claude-3-sonnet-20240229-v1:0',
        'anthropic.claude-3-haiku-20240307-v1:0'
    ]
    
    print("\n🤖 Testing specific model access:")
    
    working_combinations = []
    
    for region in regions_to_test:
        print(f"\n   Region: {region}")
        
        try:
            bedrock = boto3.client('bedrock', region_name=region)
            available_models = bedrock.list_foundation_models()
            model_ids = [m['modelId'] for m in available_models.get('modelSummaries', [])]
            
            for model in models_to_test:
                if model in model_ids:
                    print(f"      ✅ {model}")
                    working_combinations.append((region, model))
                else:
                    print(f"      ❌ {model} (not available)")
                    
        except Exception as e:
            print(f"      ❌ Cannot access region: {e}")
    
    return working_combinations

def suggest_fixes():
    """Suggest fixes for common Bedrock issues"""
    print("\n🔧 SUGGESTED FIXES:")
    print("=" * 50)
    
    print("\n1. REQUEST MODEL ACCESS:")
    print("   • Go to AWS Bedrock Console")
    print("   • Navigate to 'Model access' in left sidebar")
    print("   • Click 'Request model access'")
    print("   • Enable Google Gemini models")
    print("   • Enable Anthropic Claude models (backup)")
    print("   • Submit request (usually approved instantly)")
    
    print("\n2. UPDATE IAM PERMISSIONS:")
    print("   • Attach 'AmazonBedrockFullAccess' policy to your user")
    print("   • Or create custom policy with bedrock:* permissions")
    print("   • Use the generated bedrock-full-access-policy.json")
    
    print("\n3. TRY DIFFERENT REGION:")
    print("   • Bedrock is not available in all regions")
    print("   • Try us-east-1, us-west-2, or eu-west-1")
    print("   • Update BEDROCK_REGION in .env file")
    
    print("\n4. FALLBACK TO ORIGINAL GEMINI API:")
    print("   • If Bedrock access is blocked, use original system")
    print("   • Set USE_AWS_SERVICES=false in .env")
    print("   • Add GEMINI_API_KEY to .env")
    print("   • Run: python agent.py (original version)")

def create_fallback_config():
    """Create fallback configuration without Bedrock"""
    fallback_env = """# Fallback Configuration - No Bedrock Required
# Use this if Bedrock access is not available

# Disable AWS services
USE_AWS_SERVICES=false
USE_BEDROCK_AI=false
USE_DYNAMODB=false
USE_S3_STORAGE=false
USE_SES_EMAIL=false

# Use original Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_TIMEOUT=10.0
GEMINI_RETRY_COUNT=2

# Use original email (optional)
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM_NAME=TidalHacks Pizza Agent
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Agent Configuration
USE_GEMINI=true
USE_AI_EVALUATION=true
USE_AI_RESPONSES=true
USE_AI_PROMPTS=true
USE_AI_MODERATION=false
USE_RANDOM_CODES=true
ENABLE_ANALYTICS=true

# Conference Settings
CONFERENCE_ID=TidalHACKS25
"""
    
    with open('.env.fallback', 'w') as f:
        f.write(fallback_env)
    
    print("✅ Created .env.fallback configuration")
    print("   Use this if Bedrock access cannot be resolved:")
    print("   cp .env.fallback .env")

def main():
    """Main diagnostic function"""
    print("🔍 AWS Bedrock Access Diagnostic Tool")
    print("=" * 50)
    
    # Step 1: Check credentials
    print("\n1. Checking AWS credentials...")
    if not check_aws_credentials():
        print("❌ Fix AWS credentials first")
        return
    
    # Step 2: Check regions
    print("\n2. Checking Bedrock regions...")
    available_regions = check_bedrock_regions()
    
    # Step 3: Check permissions
    print("\n3. Checking IAM permissions...")
    check_iam_permissions()
    
    # Step 4: Test models
    if available_regions:
        print("\n4. Testing model access...")
        working_combinations = test_bedrock_models()
        
        if working_combinations:
            print(f"\n✅ Found {len(working_combinations)} working model combinations!")
            print("Recommended configuration:")
            region, model = working_combinations[0]
            print(f"   BEDROCK_REGION={region}")
            print(f"   BEDROCK_MODEL_ID={model}")
        else:
            print("\n❌ No working model combinations found")
    
    # Step 5: Create policy
    print("\n5. Creating IAM policy...")
    create_bedrock_policy()
    
    # Step 6: Create fallback
    print("\n6. Creating fallback configuration...")
    create_fallback_config()
    
    # Step 7: Suggestions
    suggest_fixes()
    
    print("\n" + "=" * 50)
    print("🎯 NEXT STEPS:")
    print("1. Follow the suggested fixes above")
    print("2. Wait 5-10 minutes after requesting model access")
    print("3. Run this script again to verify")
    print("4. Or use fallback: cp .env.fallback .env")

if __name__ == "__main__":
    main()