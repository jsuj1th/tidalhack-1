#!/usr/bin/env python3
"""
AWS Setup Script for Hackathon Feedback System
Automated setup of AWS resources for beginners
"""

import boto3
import json
import time
import sys
import os
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, Any

class AWSSetup:
    def __init__(self, region: str = "us-east-1", project_name: str = "hackathon-feedback"):
        self.region = region
        self.project_name = project_name
        self.environment = os.getenv("ENVIRONMENT", "dev")
        
        # Initialize AWS clients
        try:
            self.dynamodb = boto3.client('dynamodb', region_name=region)
            self.s3 = boto3.client('s3', region_name=region)
            self.lambda_client = boto3.client('lambda', region_name=region)
            self.iam = boto3.client('iam', region_name=region)
            self.cloudwatch = boto3.client('cloudwatch', region_name=region)
            self.apigateway = boto3.client('apigateway', region_name=region)
            
            print(f"✅ AWS clients initialized for region: {region}")
        except NoCredentialsError:
            print("❌ AWS credentials not found. Please configure your credentials:")
            print("   aws configure")
            print("   or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to initialize AWS clients: {e}")
            sys.exit(1)
    
    def create_dynamodb_table(self) -> bool:
        """Create DynamoDB table for feedback storage"""
        table_name = f"{self.project_name}-{self.environment}"
        
        try:
            # Check if table already exists
            try:
                response = self.dynamodb.describe_table(TableName=table_name)
                print(f"✅ DynamoDB table '{table_name}' already exists")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise e
            
            print(f"🔄 Creating DynamoDB table: {table_name}")
            
            # Create table
            response = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'feedback_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'feedback_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'hackathon_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'hackathon-timestamp-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'hackathon_id',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'timestamp',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': self.project_name
                    },
                    {
                        'Key': 'Environment',
                        'Value': self.environment
                    }
                ]
            )
            
            # Wait for table to be active
            print("⏳ Waiting for table to be active...")
            waiter = self.dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            print(f"✅ DynamoDB table '{table_name}' created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create DynamoDB table: {e}")
            return False
    
    def create_s3_bucket(self) -> bool:
        """Create S3 bucket for data backup"""
        bucket_name = f"{self.project_name}-{self.environment}-data"
        
        try:
            # Check if bucket exists
            try:
                self.s3.head_bucket(Bucket=bucket_name)
                print(f"✅ S3 bucket '{bucket_name}' already exists")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] != '404':
                    raise e
            
            print(f"🔄 Creating S3 bucket: {bucket_name}")
            
            # Create bucket
            if self.region == 'us-east-1':
                self.s3.create_bucket(Bucket=bucket_name)
            else:
                self.s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            # Enable versioning
            self.s3.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Enable encryption
            self.s3.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'AES256'
                            }
                        }
                    ]
                }
            )
            
            print(f"✅ S3 bucket '{bucket_name}' created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create S3 bucket: {e}")
            return False
    
    def create_iam_role(self) -> str:
        """Create IAM role for Lambda function"""
        role_name = f"{self.project_name}-{self.environment}-lambda-role"
        
        try:
            # Check if role exists
            try:
                response = self.iam.get_role(RoleName=role_name)
                print(f"✅ IAM role '{role_name}' already exists")
                return response['Role']['Arn']
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchEntity':
                    raise e
            
            print(f"🔄 Creating IAM role: {role_name}")
            
            # Trust policy for Lambda
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "lambda.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            # Create role
            response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"IAM role for {self.project_name} Lambda function",
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': self.project_name
                    },
                    {
                        'Key': 'Environment',
                        'Value': self.environment
                    }
                ]
            )
            
            role_arn = response['Role']['Arn']
            
            # Attach basic Lambda execution policy
            self.iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            
            # Create and attach custom policy
            policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "dynamodb:PutItem",
                            "dynamodb:GetItem",
                            "dynamodb:Query",
                            "dynamodb:Scan",
                            "dynamodb:UpdateItem",
                            "dynamodb:DeleteItem"
                        ],
                        "Resource": [
                            f"arn:aws:dynamodb:{self.region}:*:table/{self.project_name}-{self.environment}",
                            f"arn:aws:dynamodb:{self.region}:*:table/{self.project_name}-{self.environment}/index/*"
                        ]
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:PutObject",
                            "s3:GetObject",
                            "s3:DeleteObject"
                        ],
                        "Resource": f"arn:aws:s3:::{self.project_name}-{self.environment}-data/*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "cloudwatch:PutMetricData"
                        ],
                        "Resource": "*"
                    }
                ]
            }
            
            policy_name = f"{self.project_name}-{self.environment}-lambda-policy"
            
            self.iam.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document)
            )
            
            print(f"✅ IAM role '{role_name}' created successfully")
            
            # Wait a bit for role to propagate
            time.sleep(10)
            
            return role_arn
            
        except Exception as e:
            print(f"❌ Failed to create IAM role: {e}")
            return ""
    
    def create_lambda_function(self, role_arn: str) -> bool:
        """Create Lambda function"""
        function_name = f"{self.project_name}-{self.environment}-processor"
        
        try:
            # Check if function exists
            try:
                response = self.lambda_client.get_function(FunctionName=function_name)
                print(f"✅ Lambda function '{function_name}' already exists")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise e
            
            print(f"🔄 Creating Lambda function: {function_name}")
            
            # Create deployment package
            import zipfile
            import io
            
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add lambda function
                zip_file.write('lambda_function.py', 'lambda_function.py')
                
                # Add dependencies (you might need to adjust paths)
                for file_name in ['../aws_services.py', '../functions.py', '../config.py']:
                    if os.path.exists(file_name):
                        zip_file.write(file_name, os.path.basename(file_name))
            
            zip_buffer.seek(0)
            
            # Create function
            response = self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.11',
                Role=role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_buffer.read()},
                Description=f'Hackathon feedback processor for {self.project_name}',
                Timeout=30,
                MemorySize=256,
                Environment={
                    'Variables': {
                        'DYNAMODB_TABLE_NAME': f"{self.project_name}-{self.environment}",
                        'S3_BUCKET_NAME': f"{self.project_name}-{self.environment}-data",
                        'CLOUDWATCH_NAMESPACE': 'HackathonFeedback',
                        'ENVIRONMENT': self.environment
                    }
                },
                Tags={
                    'Project': self.project_name,
                    'Environment': self.environment
                }
            )
            
            print(f"✅ Lambda function '{function_name}' created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create Lambda function: {e}")
            return False
    
    def create_cloudwatch_dashboard(self) -> bool:
        """Create CloudWatch dashboard"""
        dashboard_name = f"{self.project_name}-{self.environment}-dashboard"
        
        try:
            print(f"🔄 Creating CloudWatch dashboard: {dashboard_name}")
            
            dashboard_body = {
                "widgets": [
                    {
                        "type": "metric",
                        "x": 0,
                        "y": 0,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                ["HackathonFeedback", "FeedbackSubmitted"]
                            ],
                            "period": 300,
                            "stat": "Sum",
                            "region": self.region,
                            "title": "Feedback Submissions Over Time"
                        }
                    },
                    {
                        "type": "metric",
                        "x": 12,
                        "y": 0,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                ["HackathonFeedback", "FeedbackBySentiment", "Sentiment", "positive"],
                                [".", ".", ".", "negative"],
                                [".", ".", ".", "neutral"]
                            ],
                            "period": 300,
                            "stat": "Sum",
                            "region": self.region,
                            "title": "Feedback by Sentiment"
                        }
                    }
                ]
            }
            
            self.cloudwatch.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=json.dumps(dashboard_body)
            )
            
            print(f"✅ CloudWatch dashboard '{dashboard_name}' created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create CloudWatch dashboard: {e}")
            return False
    
    def setup_all(self) -> Dict[str, Any]:
        """Setup all AWS resources"""
        print(f"🚀 Setting up AWS infrastructure for {self.project_name}")
        print(f"   Region: {self.region}")
        print(f"   Environment: {self.environment}")
        print()
        
        results = {}
        
        # Create DynamoDB table
        results['dynamodb'] = self.create_dynamodb_table()
        
        # Create S3 bucket
        results['s3'] = self.create_s3_bucket()
        
        # Create IAM role
        role_arn = self.create_iam_role()
        results['iam'] = bool(role_arn)
        
        # Create Lambda function
        if role_arn:
            results['lambda'] = self.create_lambda_function(role_arn)
        else:
            results['lambda'] = False
        
        # Create CloudWatch dashboard
        results['cloudwatch'] = self.create_cloudwatch_dashboard()
        
        # Print summary
        print("\n" + "="*50)
        print("🎉 AWS Setup Complete!")
        print("="*50)
        
        for service, success in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {service.upper()}: {'Success' if success else 'Failed'}")
        
        if all(results.values()):
            print("\n🎊 All services set up successfully!")
            print("\nNext steps:")
            print("1. Update your .env file with the resource names")
            print("2. Deploy your agent code")
            print("3. Test the feedback collection")
            
            # Print resource names
            print(f"\nResource names to use in your .env:")
            print(f"DYNAMODB_TABLE_NAME={self.project_name}-{self.environment}")
            print(f"S3_BUCKET_NAME={self.project_name}-{self.environment}-data")
            print(f"AWS_REGION={self.region}")
        else:
            print("\n⚠️  Some services failed to set up. Check the errors above.")
        
        return results

def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup AWS infrastructure for hackathon feedback system')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--project', default='hackathon-feedback', help='Project name (default: hackathon-feedback)')
    parser.add_argument('--environment', default='dev', help='Environment (default: dev)')
    
    args = parser.parse_args()
    
    # Set environment variable
    os.environ['ENVIRONMENT'] = args.environment
    
    # Run setup
    setup = AWSSetup(region=args.region, project_name=args.project)
    results = setup.setup_all()
    
    # Exit with appropriate code
    sys.exit(0 if all(results.values()) else 1)

if __name__ == "__main__":
    main()