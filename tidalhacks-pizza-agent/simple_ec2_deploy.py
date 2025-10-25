#!/usr/bin/env python3
"""
Simple EC2 Deployment for Pizza Agent
Creates a public endpoint quickly and reliably
"""

import boto3
import json
import os
import base64
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

def create_user_data_script():
    """Create user data script with all necessary files"""
    
    # Read the hybrid web interface
    try:
        with open('hybrid_web_interface.py', 'r') as f:
            app_code = f.read()
    except:
        app_code = """
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return '''
    <html>
    <head><title>TidalHACKS 2025 Pizza Agent</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>🍕 TidalHACKS 2025 Pizza Agent</h1>
        <p>Deployment successful! The full application is loading...</p>
        <p>Powered by AWS EC2 + Gemini AI</p>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'Pizza Agent is running!'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
"""
    
    # Read environment variables
    env_content = ""
    try:
        with open('.env', 'r') as f:
            env_content = f.read()
    except:
        env_content = f"""
GEMINI_API_KEY={os.getenv('GEMINI_API_KEY', '')}
AWS_REGION={os.getenv('AWS_REGION', 'us-east-1')}
USE_GEMINI=true
USE_AWS_SERVICES=true
"""
    
    user_data = f"""#!/bin/bash
# Update system
yum update -y

# Install Python and dependencies
yum install -y python3 python3-pip git nginx

# Install Python packages
pip3 install flask flask-cors python-dotenv google-generativeai boto3 uagents aiohttp requests

# Create application directory
mkdir -p /home/ec2-user/pizza-agent
cd /home/ec2-user/pizza-agent

# Create application file
cat > app.py << 'EOF'
{app_code}
EOF

# Create environment file
cat > .env << 'EOF'
{env_content}
EOF

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
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Configure nginx reverse proxy
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
            proxy_connect_timeout 30;
            proxy_send_timeout 30;
            proxy_read_timeout 30;
        }}
        
        location /health {{
            proxy_pass http://127.0.0.1:5000/health;
            proxy_set_header Host $host;
        }}
    }}
}}
EOF

# Set permissions
chown -R ec2-user:ec2-user /home/ec2-user/pizza-agent

# Start services
systemctl daemon-reload
systemctl enable pizza-agent
systemctl start pizza-agent
systemctl enable nginx
systemctl start nginx

# Create status file
echo "Deployment completed at $(date)" > /home/ec2-user/deployment-status.txt
echo "Pizza Agent Status: $(systemctl is-active pizza-agent)" >> /home/ec2-user/deployment-status.txt
echo "Nginx Status: $(systemctl is-active nginx)" >> /home/ec2-user/deployment-status.txt
"""
    
    return user_data

def deploy_to_ec2():
    """Deploy Pizza Agent to EC2 with public access"""
    
    # Initialize AWS clients
    session = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )
    
    ec2 = session.client('ec2')
    iam = session.client('iam')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    print(f"🚀 Deploying TidalHACKS Pizza Agent to AWS EC2 ({region})")
    print("=" * 60)
    
    try:
        # 1. Create Security Group
        print("1. Creating security group...")
        try:
            sg_response = ec2.create_security_group(
                GroupName='tidalhacks-pizza-agent-sg',
                Description='Security group for TidalHACKS Pizza Agent'
            )
            security_group_id = sg_response['GroupId']
            
            # Add rules
            ec2.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTP access'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 443,
                        'ToPort': 443,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTPS access'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH access'}]
                    }
                ]
            )
            print(f"   ✅ Created security group: {security_group_id}")
            
        except ClientError as e:
            if 'InvalidGroup.Duplicate' in str(e):
                # Get existing security group
                sgs = ec2.describe_security_groups(
                    Filters=[{'Name': 'group-name', 'Values': ['tidalhacks-pizza-agent-sg']}]
                )
                security_group_id = sgs['SecurityGroups'][0]['GroupId']
                print(f"   ✅ Using existing security group: {security_group_id}")
            else:
                raise
        
        # 2. Create IAM Role (if needed)
        print("2. Setting up IAM role...")
        role_name = 'TidalHACKS-Pizza-EC2-Role'
        
        try:
            # Create role
            assume_role_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                Description='Role for TidalHACKS Pizza Agent EC2 instance'
            )
            
            # Attach policies
            policies = [
                'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                'arn:aws:iam::aws:policy/AmazonSESFullAccess'
            ]
            
            for policy in policies:
                iam.attach_role_policy(RoleName=role_name, PolicyArn=policy)
            
            # Create instance profile
            iam.create_instance_profile(InstanceProfileName=role_name)
            iam.add_role_to_instance_profile(
                InstanceProfileName=role_name,
                RoleName=role_name
            )
            
            print(f"   ✅ Created IAM role: {role_name}")
            
        except ClientError as e:
            if 'EntityAlreadyExists' in str(e):
                print(f"   ✅ Using existing IAM role: {role_name}")
            else:
                print(f"   ⚠️ IAM role creation failed: {e}")
                role_name = None
        
        # 3. Launch EC2 Instance
        print("3. Launching EC2 instance...")
        
        # Get latest Amazon Linux 2 AMI
        images = ec2.describe_images(
            Owners=['amazon'],
            Filters=[
                {'Name': 'name', 'Values': ['amzn2-ami-hvm-*-x86_64-gp2']},
                {'Name': 'state', 'Values': ['available']}
            ]
        )
        
        # Sort by creation date and get the latest
        latest_ami = sorted(images['Images'], key=lambda x: x['CreationDate'], reverse=True)[0]
        ami_id = latest_ami['ImageId']
        
        user_data = create_user_data_script()
        
        launch_params = {
            'ImageId': ami_id,
            'MinCount': 1,
            'MaxCount': 1,
            'InstanceType': 't3.micro',  # Free tier eligible
            'SecurityGroupIds': [security_group_id],
            'UserData': user_data,
            'TagSpecifications': [
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': 'TidalHACKS-Pizza-Agent'},
                        {'Key': 'Project', 'Value': 'TidalHACKS2025'},
                        {'Key': 'Environment', 'Value': 'Production'}
                    ]
                }
            ]
        }
        
        # Add IAM instance profile if available
        if role_name:
            launch_params['IamInstanceProfile'] = {'Name': role_name}
        
        response = ec2.run_instances(**launch_params)
        instance_id = response['Instances'][0]['InstanceId']
        
        print(f"   ✅ Launched instance: {instance_id}")
        print(f"   ⏳ Waiting for instance to be running...")
        
        # Wait for instance to be running
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id], WaiterConfig={'Delay': 15, 'MaxAttempts': 20})
        
        # Get instance details
        instance_info = ec2.describe_instances(InstanceIds=[instance_id])
        instance = instance_info['Reservations'][0]['Instances'][0]
        
        public_ip = instance.get('PublicIpAddress')
        public_dns = instance.get('PublicDnsName')
        
        print("=" * 60)
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("=" * 60)
        print(f"Instance ID: {instance_id}")
        print(f"Public IP: {public_ip}")
        print(f"Public DNS: {public_dns}")
        print(f"Security Group: {security_group_id}")
        
        if public_ip:
            print(f"\n🌐 PUBLIC ENDPOINTS:")
            print(f"   Main URL: http://{public_ip}")
            print(f"   Health Check: http://{public_ip}/health")
            print(f"   Alternative: http://{public_dns}")
        
        print(f"\n⏰ IMPORTANT NOTES:")
        print(f"   • Instance is initializing (takes 3-5 minutes)")
        print(f"   • Application will be available at port 80 (HTTP)")
        print(f"   • Nginx reverse proxy is configured")
        print(f"   • Auto-restart enabled for reliability")
        
        print(f"\n🔧 MANAGEMENT:")
        print(f"   • SSH: ssh -i your-key.pem ec2-user@{public_ip}")
        print(f"   • Logs: sudo journalctl -u pizza-agent -f")
        print(f"   • Status: sudo systemctl status pizza-agent")
        
        print(f"\n💰 COST ESTIMATE:")
        print(f"   • t3.micro: ~$8.76/month (free tier eligible)")
        print(f"   • Data transfer: ~$0.09/GB")
        print(f"   • Stop instance when not needed to save costs")
        
        return {
            'instance_id': instance_id,
            'public_ip': public_ip,
            'public_dns': public_dns,
            'security_group': security_group_id,
            'url': f'http://{public_ip}' if public_ip else None
        }
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return None

def main():
    """Main deployment function"""
    result = deploy_to_ec2()
    
    if result and result['url']:
        print(f"\n🚀 Your TidalHACKS Pizza Agent is deploying at:")
        print(f"   {result['url']}")
        print(f"\n📱 Share this URL with hackathon participants!")
        print(f"   They can get pizza coupons by sharing their stories!")
        
        # Create a simple status checker
        print(f"\n🔍 To check deployment status:")
        print(f"   curl {result['url']}/health")
        
    return result

if __name__ == "__main__":
    main()