# aws_config.py
"""
AWS Configuration and Services Integration
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import json

load_dotenv()

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# DynamoDB Configuration
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "pizza-agent-data")
DYNAMODB_ANALYTICS_TABLE = os.getenv("DYNAMODB_ANALYTICS_TABLE", "pizza-agent-analytics")

# S3 Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "pizza-agent-storage")

# SES Configuration
SES_FROM_EMAIL = os.getenv("SES_FROM_EMAIL", "noreply@yourdomain.com")
SES_FROM_NAME = os.getenv("SES_FROM_NAME", "TidalHACKS25 Pizza Agent")

# Bedrock Configuration - Using Gemini
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "google.gemini-1.5-pro-v1:0")
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")

class AWSServices:
    """AWS Services Manager"""
    
    def __init__(self):
        self.session = None
        self.dynamodb = None
        self.s3 = None
        self.ses = None
        self.bedrock = None
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize AWS session and clients"""
        try:
            # Create session
            if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
                self.session = boto3.Session(
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    region_name=AWS_REGION
                )
            else:
                # Use default credentials (IAM role, profile, etc.)
                self.session = boto3.Session(region_name=AWS_REGION)
            
            # Initialize clients
            self.dynamodb = self.session.resource('dynamodb', region_name=AWS_REGION)
            self.s3 = self.session.client('s3', region_name=AWS_REGION)
            self.ses = self.session.client('ses', region_name=AWS_REGION)
            self.bedrock = self.session.client('bedrock-runtime', region_name=BEDROCK_REGION)
            
            print("✅ AWS services initialized successfully")
            
        except NoCredentialsError:
            print("❌ AWS credentials not found. Please configure AWS credentials.")
            raise
        except Exception as e:
            print(f"❌ Error initializing AWS services: {e}")
            raise
    
    def test_connection(self) -> Dict[str, bool]:
        """Test connection to all AWS services"""
        results = {}
        
        # Test DynamoDB
        try:
            list(self.dynamodb.tables.all())
            results['dynamodb'] = True
        except Exception as e:
            print(f"DynamoDB connection failed: {e}")
            results['dynamodb'] = False
        
        # Test S3
        try:
            self.s3.list_buckets()
            results['s3'] = True
        except Exception as e:
            print(f"S3 connection failed: {e}")
            results['s3'] = False
        
        # Test SES
        try:
            self.ses.get_send_quota()
            results['ses'] = True
        except Exception as e:
            print(f"SES connection failed: {e}")
            results['ses'] = False
        
        # Test Bedrock
        try:
            # Try to list foundation models
            self.bedrock.list_foundation_models()
            results['bedrock'] = True
        except Exception as e:
            print(f"Bedrock connection failed: {e}")
            results['bedrock'] = False
        
        return results

# Global AWS services instance
aws_services = None

def get_aws_services() -> AWSServices:
    """Get or create AWS services instance"""
    global aws_services
    if aws_services is None:
        aws_services = AWSServices()
    return aws_services

def validate_aws_setup() -> bool:
    """Validate AWS setup and return True if ready"""
    try:
        services = get_aws_services()
        results = services.test_connection()
        
        print("\n🔍 AWS Services Status:")
        print(f"DynamoDB: {'✅' if results['dynamodb'] else '❌'}")
        print(f"S3: {'✅' if results['s3'] else '❌'}")
        print(f"SES: {'✅' if results['ses'] else '❌'}")
        print(f"Bedrock: {'✅' if results['bedrock'] else '❌'}")
        
        return all(results.values())
        
    except Exception as e:
        print(f"❌ AWS validation failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing AWS Configuration...")
    if validate_aws_setup():
        print("\n✅ All AWS services are ready!")
    else:
        print("\n❌ Some AWS services need configuration.")