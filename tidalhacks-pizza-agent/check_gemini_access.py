#!/usr/bin/env python3
"""
Check Gemini Model Access Across AWS Regions
"""

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

def check_gemini_in_regions():
    """Check Gemini model availability across AWS regions"""
    
    # Regions where Bedrock is available
    bedrock_regions = [
        'us-east-1',
        'us-west-2',
        'eu-west-1',
        'eu-central-1',
        'ap-southeast-1',
        'ap-northeast-1',
        'ap-southeast-2'
    ]
    
    gemini_models = [
        'google.gemini-1.5-pro-v1:0',
        'google.gemini-1.5-flash-v1:0',
        'google.gemini-pro-v1:0'  # Alternative model ID
    ]
    
    print("🔍 Checking Gemini Model Availability Across Regions")
    print("=" * 60)
    
    found_gemini = []
    
    for region in bedrock_regions:
        print(f"\n📍 Region: {region}")
        
        try:
            bedrock = boto3.client('bedrock', region_name=region)
            response = bedrock.list_foundation_models()
            
            available_models = [model['modelId'] for model in response.get('modelSummaries', [])]
            
            # Check for Gemini models
            gemini_found = []
            for model in gemini_models:
                if model in available_models:
                    gemini_found.append(model)
                    found_gemini.append((region, model))
            
            if gemini_found:
                print(f"   ✅ Gemini models available:")
                for model in gemini_found:
                    print(f"      - {model}")
            else:
                print(f"   ❌ No Gemini models found")
                
                # Show what Google models are available
                google_models = [m for m in available_models if 'google' in m.lower()]
                if google_models:
                    print(f"   ℹ️  Other Google models:")
                    for model in google_models[:3]:
                        print(f"      - {model}")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                print(f"   ❌ Access denied - check permissions")
            else:
                print(f"   ❌ Error: {error_code}")
        except Exception as e:
            print(f"   ❌ Region not available: {str(e)[:50]}...")
    
    return found_gemini

def request_model_access_instructions():
    """Provide instructions for requesting model access"""
    print("\n" + "=" * 60)
    print("🚀 HOW TO REQUEST GEMINI MODEL ACCESS")
    print("=" * 60)
    
    print("\n1. Go to AWS Bedrock Console:")
    print("   https://console.aws.amazon.com/bedrock/")
    
    print("\n2. Select the correct region:")
    print("   - Try us-west-2 first (most likely to have Gemini)")
    print("   - Then try us-east-1")
    print("   - Finally try eu-west-1")
    
    print("\n3. Click 'Model access' in left sidebar")
    
    print("\n4. Look for 'Google' provider section")
    
    print("\n5. Enable these models:")
    print("   ✅ google.gemini-1.5-pro-v1:0")
    print("   ✅ google.gemini-1.5-flash-v1:0")
    print("   ✅ Any other Google/Gemini models you see")
    
    print("\n6. Click 'Save changes' or 'Submit request'")
    
    print("\n7. Wait 1-5 minutes for approval")
    
    print("\n8. Run this script again to verify")

def update_env_with_working_region(working_combinations):
    """Update .env file with working region and model"""
    if working_combinations:
        region, model = working_combinations[0]
        
        print(f"\n✅ RECOMMENDED CONFIGURATION:")
        print(f"   BEDROCK_REGION={region}")
        print(f"   BEDROCK_MODEL_ID={model}")
        
        # Ask if user wants to update .env
        try:
            update = input(f"\nUpdate .env file with {region} and {model}? (y/n): ").lower().strip()
            if update == 'y':
                # Read current .env
                with open('.env', 'r') as f:
                    content = f.read()
                
                # Update region and model
                lines = content.split('\n')
                updated_lines = []
                
                for line in lines:
                    if line.startswith('BEDROCK_REGION='):
                        updated_lines.append(f'BEDROCK_REGION={region}')
                    elif line.startswith('BEDROCK_MODEL_ID=') and not line.startswith('#'):
                        updated_lines.append(f'BEDROCK_MODEL_ID={model}')
                    else:
                        updated_lines.append(line)
                
                # Write back
                with open('.env', 'w') as f:
                    f.write('\n'.join(updated_lines))
                
                print("✅ Updated .env file!")
                print("Now run: python setup_aws.py")
        except KeyboardInterrupt:
            print("\nSkipped .env update")

def main():
    """Main function"""
    print("🤖 Gemini Model Access Checker for AWS Bedrock")
    
    # Check current credentials
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Account: {identity.get('Account')}")
        print(f"✅ User: {identity.get('Arn', '').split('/')[-1]}")
    except Exception as e:
        print(f"❌ AWS credentials error: {e}")
        return
    
    # Check Gemini availability
    working_combinations = check_gemini_in_regions()
    
    if working_combinations:
        print(f"\n🎉 SUCCESS! Found {len(working_combinations)} working Gemini configurations:")
        for region, model in working_combinations:
            print(f"   ✅ {region}: {model}")
        
        update_env_with_working_region(working_combinations)
        
    else:
        print("\n❌ No Gemini models found in any region")
        print("\nPossible reasons:")
        print("1. Gemini models not yet available in your AWS account")
        print("2. Need to request access in Bedrock console")
        print("3. Gemini not available in your AWS region")
        
        request_model_access_instructions()
        
        print("\n🔄 ALTERNATIVE OPTIONS:")
        print("1. Wait for Gemini availability (Google is rolling out gradually)")
        print("2. Use Claude models (excellent alternative)")
        print("3. Use original Gemini API (outside AWS)")

if __name__ == "__main__":
    main()