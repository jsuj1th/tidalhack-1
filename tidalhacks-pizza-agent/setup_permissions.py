#!/usr/bin/env python3
"""
Setup all necessary AWS permissions for Pizza Agent deployment
"""

import boto3
import json
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

def setup_permissions():
    """Setup all necessary permissions for deployment"""
    
    # Initialize AWS clients
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )
    
    iam = session.client('iam')
    sts = session.client('sts')
    
    print("🔐 Setting up AWS permissions for TidalHACKS Pizza Agent")
    print("=" * 60)
    
    try:
        # Get current user info
        identity = sts.get_caller_identity()
        user_arn = identity.get('Arn', '')
        print(f"Debug - Full ARN: {user_arn}")
        if ':user/' in user_arn:
            username = user_arn.split(':user/')[-1]
            print(f"Debug - Extracted username: {username}")
        else:
            username = None
            print("Debug - Could not find :user/ in ARN")
        
        print(f"Current user: {username}")
        print(f"User ARN: {user_arn}")
        
        if not username:
            print("❌ Cannot determine username from ARN. Please check your credentials.")
            return False
        
        # Read the complete IAM policy
        with open('complete_iam_policy.json', 'r') as f:
            policy_document = f.read()
        
        # Create custom policy
        policy_name = 'TidalHACKS-Pizza-Agent-FullAccess'
        
        try:
            print(f"\n1. Creating custom policy: {policy_name}")
            
            policy_response = iam.create_policy(
                PolicyName=policy_name,
                PolicyDocument=policy_document,
                Description='Full access policy for TidalHACKS Pizza Agent deployment and operation'
            )
            
            policy_arn = policy_response['Policy']['Arn']
            print(f"   ✅ Created policy: {policy_arn}")
            
        except ClientError as e:
            if 'EntityAlreadyExists' in str(e):
                # Get existing policy ARN
                account_id = identity.get('Account')
                policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
                print(f"   ✅ Using existing policy: {policy_arn}")
            else:
                print(f"   ❌ Policy creation failed: {e}")
                return False
        
        # Attach policy to user
        try:
            print(f"\n2. Attaching policy to user: {username}")
            
            iam.attach_user_policy(
                UserName=username,
                PolicyArn=policy_arn
            )
            
            print(f"   ✅ Policy attached successfully")
            
        except ClientError as e:
            if 'EntityAlreadyExists' in str(e) or 'is already attached' in str(e):
                print(f"   ✅ Policy already attached")
            else:
                print(f"   ❌ Policy attachment failed: {e}")
                return False
        
        # Also attach some AWS managed policies for convenience
        managed_policies = [
            'arn:aws:iam::aws:policy/AWSLambda_FullAccess',
            'arn:aws:iam::aws:policy/AmazonAPIGatewayAdministrator',
            'arn:aws:iam::aws:policy/AmazonEC2FullAccess'
        ]
        
        print(f"\n3. Attaching additional managed policies...")
        
        for policy_arn in managed_policies:
            try:
                iam.attach_user_policy(
                    UserName=username,
                    PolicyArn=policy_arn
                )
                policy_name = policy_arn.split('/')[-1]
                print(f"   ✅ Attached: {policy_name}")
                
            except ClientError as e:
                if 'EntityAlreadyExists' in str(e) or 'is already attached' in str(e):
                    policy_name = policy_arn.split('/')[-1]
                    print(f"   ✅ Already attached: {policy_name}")
                else:
                    policy_name = policy_arn.split('/')[-1]
                    print(f"   ⚠️ Failed to attach {policy_name}: {e}")
        
        # List all attached policies for verification
        print(f"\n4. Verifying attached policies...")
        
        try:
            attached_policies = iam.list_attached_user_policies(UserName=username)
            
            print(f"   Total attached policies: {len(attached_policies['AttachedPolicies'])}")
            
            for policy in attached_policies['AttachedPolicies']:
                print(f"   ✅ {policy['PolicyName']}")
            
        except Exception as e:
            print(f"   ⚠️ Could not list policies: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 PERMISSIONS SETUP COMPLETE!")
        print("=" * 60)
        print("Your user now has all necessary permissions for:")
        print("• AWS Lambda functions")
        print("• API Gateway")
        print("• EC2 instances")
        print("• DynamoDB tables")
        print("• S3 buckets")
        print("• SES email service")
        print("• IAM role management")
        
        print(f"\n⏰ Note: It may take 1-2 minutes for permissions to propagate")
        print(f"🚀 You can now run the deployment script!")
        
        return True
        
    except Exception as e:
        print(f"❌ Permission setup failed: {e}")
        return False

def verify_permissions():
    """Verify that all necessary permissions are in place"""
    
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )
    
    print("\n🔍 Verifying permissions...")
    
    services_to_test = [
        ('Lambda', 'lambda', 'list_functions'),
        ('API Gateway', 'apigateway', 'get_rest_apis'),
        ('EC2', 'ec2', 'describe_instances'),
        ('DynamoDB', 'dynamodb', 'list_tables'),
        ('S3', 's3', 'list_buckets'),
        ('SES', 'ses', 'get_send_quota'),
        ('IAM', 'iam', 'list_roles')
    ]
    
    results = {}
    
    for service_name, service_code, test_method in services_to_test:
        try:
            client = session.client(service_code)
            method = getattr(client, test_method)
            method()
            results[service_name] = True
            print(f"   ✅ {service_name}: Access confirmed")
        except Exception as e:
            results[service_name] = False
            print(f"   ❌ {service_name}: Access denied - {str(e)[:50]}...")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n📊 Permission verification: {success_count}/{total_count} services accessible")
    
    if success_count == total_count:
        print("🎉 All permissions verified! Ready for deployment.")
        return True
    else:
        print("⚠️ Some permissions missing. Please check IAM policies.")
        return False

def main():
    """Main function"""
    print("🚀 TidalHACKS Pizza Agent - Permission Setup")
    
    # Setup permissions
    if setup_permissions():
        print(f"\n⏳ Waiting 30 seconds for permissions to propagate...")
        import time
        time.sleep(30)
        
        # Verify permissions
        if verify_permissions():
            print(f"\n🎯 READY FOR DEPLOYMENT!")
            print(f"Run: python lambda_deploy.py")
            return True
        else:
            print(f"\n⚠️ Permission verification failed. Please wait a few minutes and try again.")
            return False
    else:
        print(f"\n❌ Permission setup failed. Please check your AWS credentials and try again.")
        return False

if __name__ == "__main__":
    main()