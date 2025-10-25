#!/usr/bin/env python3
"""
AWS Setup Script for Pizza Agent
Automates the setup of AWS services
"""

import boto3
import json
import os
import sys
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials configured for: {identity.get('Arn', 'Unknown')}")
        return True
    except NoCredentialsError:
        print("❌ AWS credentials not found!")
        print("Please configure AWS credentials using one of these methods:")
        print("1. AWS CLI: aws configure")
        print("2. Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        print("3. IAM role (if running on EC2)")
        return False
    except Exception as e:
        print(f"❌ Error checking AWS credentials: {e}")
        return False

def check_bedrock_access():
    """Check Bedrock model access"""
    try:
        bedrock = boto3.client('bedrock', region_name=os.getenv('BEDROCK_REGION', 'us-east-1'))
        
        # Try to list foundation models
        response = bedrock.list_foundation_models()
        
        # Check for Gemini models
        gemini_models = [model for model in response.get('modelSummaries', []) 
                        if 'gemini' in model.get('modelId', '').lower()]
        
        if gemini_models:
            print("✅ Bedrock access confirmed - Gemini models available")
            for model in gemini_models[:3]:  # Show first 3
                print(f"   - {model.get('modelId')}")
            return True
        else:
            print("⚠️ Bedrock access found but no Gemini models available")
            print("Please request access to Gemini models in the Bedrock console")
            
            # Also check for Claude models as fallback
            claude_models = [model for model in response.get('modelSummaries', []) 
                            if 'claude' in model.get('modelId', '').lower()]
            if claude_models:
                print("ℹ️ Claude models are available as alternative:")
                for model in claude_models[:2]:
                    print(f"   - {model.get('modelId')}")
                print("You can use Claude by updating BEDROCK_MODEL_ID in .env")
            
            return False
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print("❌ Bedrock access denied")
            print("Please ensure your IAM user/role has bedrock:ListFoundationModels permission")
        else:
            print(f"❌ Bedrock error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking Bedrock: {e}")
        return False

def setup_dynamodb_tables():
    """Create DynamoDB tables if they don't exist"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        
        table_name = os.getenv('DYNAMODB_TABLE_NAME', 'pizza-agent-data')
        analytics_table_name = os.getenv('DYNAMODB_ANALYTICS_TABLE', 'pizza-agent-analytics')
        
        # Create main data table
        try:
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'user_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'user_id',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            print(f"⏳ Creating DynamoDB table: {table_name}")
            table.wait_until_exists()
            print(f"✅ Created DynamoDB table: {table_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"✅ DynamoDB table already exists: {table_name}")
            else:
                raise
        
        # Create analytics table
        try:
            analytics_table = dynamodb.create_table(
                TableName=analytics_table_name,
                KeySchema=[
                    {
                        'AttributeName': 'event_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'event_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'timestamp-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'timestamp',
                                'KeyType': 'HASH'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            print(f"⏳ Creating DynamoDB analytics table: {analytics_table_name}")
            analytics_table.wait_until_exists()
            print(f"✅ Created DynamoDB analytics table: {analytics_table_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"✅ DynamoDB analytics table already exists: {analytics_table_name}")
            else:
                raise
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up DynamoDB tables: {e}")
        return False

def setup_s3_bucket():
    """Create S3 bucket if it doesn't exist"""
    try:
        s3 = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        bucket_name = os.getenv('S3_BUCKET_NAME', 'pizza-agent-storage')
        region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Check if bucket exists
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"✅ S3 bucket already exists: {bucket_name}")
            return True
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code != 404:
                raise
        
        # Create bucket
        try:
            if region == 'us-east-1':
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            
            print(f"✅ Created S3 bucket: {bucket_name}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyExists':
                print(f"❌ S3 bucket name '{bucket_name}' is already taken globally")
                print("Please choose a different bucket name in your .env file")
                return False
            else:
                raise
        
    except Exception as e:
        print(f"❌ Error setting up S3 bucket: {e}")
        return False

def check_ses_configuration():
    """Check SES configuration"""
    try:
        ses = boto3.client('ses', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        from_email = os.getenv('SES_FROM_EMAIL')
        
        if not from_email:
            print("⚠️ SES_FROM_EMAIL not configured in .env file")
            return False
        
        # Get send quota
        quota = ses.get_send_quota()
        print(f"✅ SES configuration found")
        print(f"   Max 24h send: {quota.get('Max24HourSend', 0)}")
        print(f"   Max send rate: {quota.get('MaxSendRate', 0)}/sec")
        print(f"   Sent last 24h: {quota.get('SentLast24Hours', 0)}")
        
        # Check verified identities
        identities = ses.list_verified_email_addresses()
        verified_emails = identities.get('VerifiedEmailAddresses', [])
        
        if from_email in verified_emails:
            print(f"✅ Email verified: {from_email}")
        else:
            print(f"⚠️ Email not verified: {from_email}")
            print("Run this command to verify:")
            print(f"aws ses verify-email-identity --email-address {from_email}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking SES: {e}")
        return False

def create_iam_policy_template():
    """Create IAM policy template"""
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:ListFoundationModels"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:CreateTable",
                    "dynamodb:DescribeTable",
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Scan",
                    "dynamodb:Query"
                ],
                "Resource": [
                    f"arn:aws:dynamodb:*:*:table/{os.getenv('DYNAMODB_TABLE_NAME', 'pizza-agent-*')}"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:CreateBucket",
                    "s3:ListBucket",
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject"
                ],
                "Resource": [
                    f"arn:aws:s3:::{os.getenv('S3_BUCKET_NAME', 'pizza-agent-*')}",
                    f"arn:aws:s3:::{os.getenv('S3_BUCKET_NAME', 'pizza-agent-*')}/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ses:SendEmail",
                    "ses:SendRawEmail",
                    "ses:GetSendQuota",
                    "ses:GetSendStatistics",
                    "ses:VerifyEmailIdentity"
                ],
                "Resource": "*"
            }
        ]
    }
    
    with open('pizza-agent-iam-policy.json', 'w') as f:
        json.dump(policy, f, indent=2)
    
    print("✅ Created IAM policy template: pizza-agent-iam-policy.json")
    print("Use this policy when creating an IAM user or role")

def main():
    """Main setup function"""
    print("🚀 AWS Pizza Agent Setup")
    print("=" * 40)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please copy .env.aws to .env and configure your settings")
        return False
    
    success = True
    
    # Step 1: Check AWS credentials
    print("\n1. Checking AWS credentials...")
    if not check_aws_credentials():
        success = False
    
    # Step 2: Check Bedrock access
    print("\n2. Checking Bedrock access...")
    if not check_bedrock_access():
        success = False
    
    # Step 3: Setup DynamoDB
    print("\n3. Setting up DynamoDB tables...")
    if not setup_dynamodb_tables():
        success = False
    
    # Step 4: Setup S3
    print("\n4. Setting up S3 bucket...")
    if not setup_s3_bucket():
        success = False
    
    # Step 5: Check SES
    print("\n5. Checking SES configuration...")
    if not check_ses_configuration():
        success = False
    
    # Step 6: Create IAM policy template
    print("\n6. Creating IAM policy template...")
    create_iam_policy_template()
    
    # Summary
    print("\n" + "=" * 40)
    if success:
        print("✅ AWS setup completed successfully!")
        print("\nNext steps:")
        print("1. Verify your email in SES if not already done")
        print("2. Test the setup: python aws_config.py")
        print("3. Run the agent: python aws_agent.py")
        print("4. Or run web interface: python aws_web_interface.py")
    else:
        print("❌ AWS setup completed with errors")
        print("Please fix the issues above and run the setup again")
    
    return success

if __name__ == "__main__":
    main()