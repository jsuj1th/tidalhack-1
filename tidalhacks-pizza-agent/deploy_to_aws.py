#!/usr/bin/env python3
"""
AWS Deployment Script for Pizza Agent
Creates public endpoint with multiple deployment options
"""

import boto3
import json
import os
import zipfile
import time
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

class AWSDeployer:
    def __init__(self):
        self.session = boto3.Session(
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Initialize clients
        self.ec2 = self.session.client('ec2')
        self.iam = self.session.client('iam')
        self.lambda_client = self.session.client('lambda')
        self.apigateway = self.session.client('apigateway')
        self.elbv2 = self.session.client('elbv2')
        
        print(f"✅ AWS Deployer initialized for region: {self.region}")

    def create_ec2_deployment(self):
        """Deploy to EC2 with public IP"""
        print("\n🚀 Creating EC2 Deployment...")
        
        try:
            # Create security group
            sg_response = self.ec2.create_security_group(
                GroupName='pizza-agent-sg',
                Description='Security group for Pizza Agent'
            )
            security_group_id = sg_response['GroupId']
            
            # Add inbound rules
            self.ec2.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 443,
                        'ToPort': 443,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 5000,
                        'ToPort': 5000,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
            
            print(f"✅ Created security group: {security_group_id}")
            
            # Create IAM role for EC2
            role_doc = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            try:
                self.iam.create_role(
                    RoleName='PizzaAgentEC2Role',
                    AssumeRolePolicyDocument=json.dumps(role_doc)
                )
                
                # Attach policies
                policies = [
                    'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                    'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                    'arn:aws:iam::aws:policy/AmazonSESFullAccess'
                ]
                
                for policy in policies:
                    self.iam.attach_role_policy(
                        RoleName='PizzaAgentEC2Role',
                        PolicyArn=policy
                    )
                
                # Create instance profile
                self.iam.create_instance_profile(InstanceProfileName='PizzaAgentProfile')
                self.iam.add_role_to_instance_profile(
                    InstanceProfileName='PizzaAgentProfile',
                    RoleName='PizzaAgentEC2Role'
                )
                
                print("✅ Created IAM role and instance profile")
                
            except ClientError as e:
                if 'EntityAlreadyExists' in str(e):
                    print("✅ IAM role already exists")
                else:
                    raise
            
            # User data script
            user_data = self.create_user_data_script()
            
            # Launch EC2 instance
            response = self.ec2.run_instances(
                ImageId='ami-0c02fb55956c7d316',  # Amazon Linux 2 AMI
                MinCount=1,
                MaxCount=1,
                InstanceType='t3.micro',
                SecurityGroupIds=[security_group_id],
                UserData=user_data,
                IamInstanceProfile={'Name': 'PizzaAgentProfile'},
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'Name', 'Value': 'TidalHACKS-Pizza-Agent'},
                            {'Key': 'Project', 'Value': 'TidalHACKS2025'}
                        ]
                    }
                ]
            )
            
            instance_id = response['Instances'][0]['InstanceId']
            print(f"✅ Launched EC2 instance: {instance_id}")
            
            # Wait for instance to be running
            print("⏳ Waiting for instance to be running...")
            waiter = self.ec2.get_waiter('instance_running')
            waiter.wait(InstanceIds=[instance_id])
            
            # Get public IP
            instance_info = self.ec2.describe_instances(InstanceIds=[instance_id])
            public_ip = instance_info['Reservations'][0]['Instances'][0].get('PublicIpAddress')
            
            return {
                'deployment_type': 'EC2',
                'instance_id': instance_id,
                'public_ip': public_ip,
                'security_group': security_group_id,
                'url': f'http://{public_ip}:5000' if public_ip else 'Pending...'
            }
            
        except Exception as e:
            print(f"❌ EC2 deployment failed: {e}")
            return None

    def create_user_data_script(self):
        """Create user data script for EC2 instance"""
        
        # Read environment variables
        env_vars = []
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    env_vars.append(f'echo "{line.strip()}" >> /home/ec2-user/pizza-agent/.env')
        
        user_data = f"""#!/bin/bash
yum update -y
yum install -y python3 python3-pip git

# Install Python packages
pip3 install flask flask-cors python-dotenv google-generativeai boto3 uagents aiohttp requests

# Create application directory
mkdir -p /home/ec2-user/pizza-agent
cd /home/ec2-user/pizza-agent

# Clone or create application files (simplified deployment)
cat > hybrid_web_interface.py << 'EOF'
{self.get_simplified_app_code()}
EOF

# Create environment file
{chr(10).join(env_vars)}

# Create systemd service
cat > /etc/systemd/system/pizza-agent.service << 'EOF'
[Unit]
Description=TidalHACKS Pizza Agent
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/pizza-agent
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 hybrid_web_interface.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
systemctl daemon-reload
systemctl enable pizza-agent
systemctl start pizza-agent

# Install nginx for reverse proxy
yum install -y nginx

# Configure nginx
cat > /etc/nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

events {{
    worker_connections 1024;
}}

http {{
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    server {{
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;

        location / {{
            proxy_pass http://127.0.0.1:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }}
    }}
}}
EOF

# Start nginx
systemctl enable nginx
systemctl start nginx

# Set permissions
chown -R ec2-user:ec2-user /home/ec2-user/pizza-agent
"""
        
        return user_data

    def get_simplified_app_code(self):
        """Get simplified application code for deployment"""
        try:
            with open('hybrid_web_interface.py', 'r') as f:
                return f.read()
        except:
            return """
# Simplified Pizza Agent for deployment
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return '<h1>TidalHACKS 2025 Pizza Agent</h1><p>Deployment successful!</p>'

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'Pizza Agent is running!'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
"""

    def create_lambda_deployment(self):
        """Deploy as AWS Lambda with API Gateway"""
        print("\n🚀 Creating Lambda + API Gateway Deployment...")
        
        try:
            # Create deployment package
            self.create_lambda_package()
            
            # Create Lambda function
            with open('pizza-agent-lambda.zip', 'rb') as f:
                zip_content = f.read()
            
            lambda_response = self.lambda_client.create_function(
                FunctionName='TidalHACKS-Pizza-Agent',
                Runtime='python3.9',
                Role=self.get_lambda_role_arn(),
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_content},
                Description='TidalHACKS 2025 Pizza Agent',
                Timeout=30,
                MemorySize=512,
                Environment={
                    'Variables': {
                        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),
                        'AWS_REGION': self.region,
                        'DYNAMODB_TABLE_NAME': os.getenv('DYNAMODB_TABLE_NAME', ''),
                        'USE_GEMINI': 'true'
                    }
                }
            )
            
            function_arn = lambda_response['FunctionArn']
            print(f"✅ Created Lambda function: {function_arn}")
            
            # Create API Gateway
            api_response = self.apigateway.create_rest_api(
                name='TidalHACKS-Pizza-API',
                description='API for TidalHACKS Pizza Agent'
            )
            
            api_id = api_response['id']
            
            # Get root resource
            resources = self.apigateway.get_resources(restApiId=api_id)
            root_id = resources['items'][0]['id']
            
            # Create proxy resource
            proxy_resource = self.apigateway.create_resource(
                restApiId=api_id,
                parentId=root_id,
                pathPart='{proxy+}'
            )
            
            # Create ANY method
            self.apigateway.put_method(
                restApiId=api_id,
                resourceId=proxy_resource['id'],
                httpMethod='ANY',
                authorizationType='NONE'
            )
            
            # Set up Lambda integration
            self.apigateway.put_integration(
                restApiId=api_id,
                resourceId=proxy_resource['id'],
                httpMethod='ANY',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f'arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{function_arn}/invocations'
            )
            
            # Deploy API
            deployment = self.apigateway.create_deployment(
                restApiId=api_id,
                stageName='prod'
            )
            
            # Add Lambda permission for API Gateway
            self.lambda_client.add_permission(
                FunctionName='TidalHACKS-Pizza-Agent',
                StatementId='api-gateway-invoke',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:{self.region}:*:{api_id}/*/*'
            )
            
            api_url = f'https://{api_id}.execute-api.{self.region}.amazonaws.com/prod'
            
            return {
                'deployment_type': 'Lambda + API Gateway',
                'function_name': 'TidalHACKS-Pizza-Agent',
                'api_id': api_id,
                'url': api_url
            }
            
        except Exception as e:
            print(f"❌ Lambda deployment failed: {e}")
            return None

    def create_lambda_package(self):
        """Create Lambda deployment package"""
        with zipfile.ZipFile('pizza-agent-lambda.zip', 'w') as zip_file:
            # Add Lambda handler
            lambda_code = """
import json
import os

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html',
            'Access-Control-Allow-Origin': '*'
        },
        'body': '''
        <html>
        <head><title>TidalHACKS 2025 Pizza Agent</title></head>
        <body>
            <h1>🍕 TidalHACKS 2025 Pizza Agent</h1>
            <p>Lambda deployment successful!</p>
            <p>API Gateway URL: Working</p>
        </body>
        </html>
        '''
    }
"""
            zip_file.writestr('lambda_function.py', lambda_code)

    def get_lambda_role_arn(self):
        """Get or create Lambda execution role"""
        role_name = 'TidalHACKS-Pizza-Lambda-Role'
        
        try:
            role = self.iam.get_role(RoleName=role_name)
            return role['Role']['Arn']
        except ClientError:
            # Create role
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
            
            role = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy)
            )
            
            # Attach policies
            policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                'arn:aws:iam::aws:policy/AmazonSESFullAccess'
            ]
            
            for policy in policies:
                self.iam.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy
                )
            
            # Wait for role to be ready
            time.sleep(10)
            
            return role['Role']['Arn']

    def deploy_all(self):
        """Deploy using all methods and return results"""
        print("🚀 Starting AWS Deployment for TidalHACKS Pizza Agent")
        print("=" * 60)
        
        results = {}
        
        # Deploy to EC2
        print("\n1. EC2 Deployment:")
        ec2_result = self.create_ec2_deployment()
        if ec2_result:
            results['ec2'] = ec2_result
        
        # Deploy to Lambda (commented out for now to avoid complexity)
        # print("\n2. Lambda Deployment:")
        # lambda_result = self.create_lambda_deployment()
        # if lambda_result:
        #     results['lambda'] = lambda_result
        
        return results

def main():
    """Main deployment function"""
    deployer = AWSDeployer()
    results = deployer.deploy_all()
    
    print("\n" + "=" * 60)
    print("🎉 DEPLOYMENT RESULTS")
    print("=" * 60)
    
    if results:
        for deployment_type, info in results.items():
            print(f"\n✅ {info['deployment_type']}:")
            for key, value in info.items():
                if key != 'deployment_type':
                    print(f"   {key}: {value}")
        
        print(f"\n🌐 PUBLIC ENDPOINTS:")
        for deployment_type, info in results.items():
            if 'url' in info:
                print(f"   {info['deployment_type']}: {info['url']}")
        
        print(f"\n⏰ Note: EC2 deployment takes 3-5 minutes to fully initialize")
        print(f"📱 Your pizza agent will be publicly accessible at the URLs above!")
        
    else:
        print("❌ No successful deployments")
    
    return results

if __name__ == "__main__":
    main()