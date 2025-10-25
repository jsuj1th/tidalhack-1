# AWS Deployment Guide for Pizza Agent

This guide will help you deploy the Pizza Agent using AWS services including Bedrock, DynamoDB, S3, and SES.

## 🚀 AWS Services Overview

### Services Used:
- **AWS Bedrock**: AI/ML for story evaluation and response generation (replaces Gemini)
- **DynamoDB**: NoSQL database for user states and analytics (replaces local JSON)
- **S3**: Object storage for backups and static assets
- **SES**: Email service for coupon delivery (replaces Gmail SMTP)

### Benefits:
- ✅ No personal email credentials needed
- ✅ Scalable and managed infrastructure
- ✅ Built-in security and compliance
- ✅ Pay-per-use pricing
- ✅ Global availability

## 📋 Prerequisites

1. **AWS Account**: Create an AWS account if you don't have one
2. **AWS CLI**: Install and configure AWS CLI
3. **Python 3.8+**: Ensure Python is installed
4. **Domain (Optional)**: For SES email sending in production

## 🔧 Step 1: AWS Setup

### 1.1 Create IAM User and Policies

Create an IAM user with the following policies:

```json
{
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
                "arn:aws:dynamodb:*:*:table/pizza-agent-*"
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
                "arn:aws:s3:::pizza-agent-*",
                "arn:aws:s3:::pizza-agent-*/*"
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
```

### 1.2 Enable Bedrock Models

1. Go to AWS Bedrock console
2. Navigate to "Model access"
3. Request access to Gemini models (recommended: `google.gemini-1.5-pro-v1:0`)
4. Wait for approval (usually instant for Gemini)
5. Alternative: Claude models are also supported (`anthropic.claude-3-sonnet-20240229-v1:0`)

### 1.3 Configure SES

For development:
```bash
# Verify your email address
aws ses verify-email-identity --email-address your-email@domain.com
```

For production:
1. Verify your domain in SES
2. Set up DKIM and SPF records
3. Request production access (removes sending limits)

## 🛠️ Step 2: Installation

### 2.1 Clone and Setup

```bash
# Navigate to pizza-experiment-main directory
cd pizza-experiment-main

# Install AWS requirements
pip install -r requirements_aws.txt
```

### 2.2 Environment Configuration

Copy the AWS environment template:
```bash
cp .env.aws .env
```

Edit `.env` with your AWS credentials:
```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# DynamoDB Configuration
DYNAMODB_TABLE_NAME=pizza-agent-data
DYNAMODB_ANALYTICS_TABLE=pizza-agent-analytics

# S3 Configuration
S3_BUCKET_NAME=pizza-agent-storage-unique-name-123

# AWS SES Configuration
SES_FROM_EMAIL=noreply@yourdomain.com
SES_FROM_NAME=CalHacks Pizza Agent

# AWS Bedrock Configuration - Using Gemini
BEDROCK_MODEL_ID=google.gemini-1.5-pro-v1:0
BEDROCK_REGION=us-east-1

# Environment Configuration
ENVIRONMENT=production
USE_AWS_SERVICES=true
USE_BEDROCK_AI=true
USE_DYNAMODB=true
USE_S3_STORAGE=true
USE_SES_EMAIL=true
```

## 🧪 Step 3: Testing

### 3.1 Test AWS Configuration

```bash
python aws_config.py
```

Expected output:
```
✅ AWS services initialized successfully
🔍 AWS Services Status:
DynamoDB: ✅
S3: ✅
SES: ✅
Bedrock: ✅
✅ All AWS services are ready!
```

### 3.2 Test Individual Services

```bash
# Test DynamoDB
python aws_dynamodb.py

# Test Bedrock AI
python aws_bedrock.py

# Test SES Email
python aws_ses.py

# Test S3 Storage
python aws_s3.py
```

## 🚀 Step 4: Deployment Options

### Option A: Local Development

```bash
# Run the agent locally
python aws_agent.py
```

### Option B: Web Interface

```bash
# Run the web interface
python aws_web_interface.py
```

Access at: `http://localhost:5000`

### Option C: AWS EC2 Deployment

1. **Launch EC2 Instance**:
   - Choose Amazon Linux 2 or Ubuntu
   - Instance type: t3.micro (free tier) or larger
   - Configure security group to allow HTTP (80) and HTTPS (443)

2. **Setup on EC2**:
   ```bash
   # Connect to EC2 instance
   ssh -i your-key.pem ec2-user@your-instance-ip
   
   # Install Python and dependencies
   sudo yum update -y
   sudo yum install python3 python3-pip git -y
   
   # Clone your repository
   git clone your-repo-url
   cd pizza-experiment-main
   
   # Install requirements
   pip3 install -r requirements_aws.txt
   
   # Set up environment variables
   cp .env.aws .env
   # Edit .env with your values
   
   # Run with nohup for background execution
   nohup python3 aws_web_interface.py > app.log 2>&1 &
   ```

3. **Configure Reverse Proxy (Optional)**:
   ```bash
   # Install nginx
   sudo yum install nginx -y
   
   # Configure nginx to proxy to your app
   sudo nano /etc/nginx/nginx.conf
   ```

### Option D: AWS Lambda + API Gateway

For serverless deployment, you can adapt the code to run on AWS Lambda with API Gateway.

## 🔒 Step 5: Security Best Practices

### 5.1 IAM Roles (Recommended for EC2)

Instead of access keys, use IAM roles:

1. Create an IAM role with the required policies
2. Attach the role to your EC2 instance
3. Remove `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` from `.env`

### 5.2 Environment Variables

Never commit `.env` files to version control:
```bash
# Add to .gitignore
echo ".env" >> .gitignore
```

### 5.3 SES Configuration

For production:
- Use a verified domain
- Set up proper SPF/DKIM records
- Monitor bounce and complaint rates

## 📊 Step 6: Monitoring and Analytics

### 6.1 CloudWatch Integration

Add CloudWatch logging:
```python
import boto3
import logging

# Configure CloudWatch logging
cloudwatch_logs = boto3.client('logs')
```

### 6.2 DynamoDB Monitoring

Monitor DynamoDB metrics:
- Read/Write capacity units
- Throttled requests
- Item counts

### 6.3 Cost Monitoring

Set up AWS billing alerts:
- DynamoDB: Pay per request
- Bedrock: Pay per token
- SES: Pay per email
- S3: Pay per storage/requests

## 🔧 Step 7: Scaling Considerations

### 7.1 DynamoDB Scaling

- Use on-demand billing for variable workloads
- Consider provisioned capacity for predictable loads
- Implement proper partition key design

### 7.2 Bedrock Rate Limits

- Monitor token usage
- Implement retry logic with exponential backoff
- Consider caching responses for similar stories

### 7.3 SES Limits

- Start with sandbox limits (200 emails/day)
- Request production access for higher limits
- Monitor bounce/complaint rates

## 🐛 Troubleshooting

### Common Issues:

1. **Bedrock Access Denied**:
   - Ensure model access is granted in Bedrock console
   - Check IAM permissions

2. **DynamoDB Table Not Found**:
   - Tables are created automatically on first run
   - Check AWS region configuration

3. **SES Email Not Sending**:
   - Verify email address in SES console
   - Check if in sandbox mode

4. **S3 Bucket Creation Failed**:
   - Bucket names must be globally unique
   - Use a unique suffix in bucket name

### Debug Commands:

```bash
# Check AWS credentials
aws sts get-caller-identity

# List DynamoDB tables
aws dynamodb list-tables

# Check SES verified identities
aws ses list-verified-email-addresses

# List S3 buckets
aws s3 ls
```

## 💰 Cost Estimation

Approximate costs for moderate usage:

- **DynamoDB**: $0.25 per million requests
- **Bedrock**: $0.003 per 1K input tokens, $0.015 per 1K output tokens
- **SES**: $0.10 per 1,000 emails
- **S3**: $0.023 per GB per month
- **EC2**: $8.76/month for t3.micro (if not using free tier)

For a hackathon with 1000 participants:
- Estimated cost: $5-15 total

## 🎯 Next Steps

1. **Custom Domain**: Set up a custom domain for the web interface
2. **SSL Certificate**: Use AWS Certificate Manager for HTTPS
3. **Load Balancer**: Use Application Load Balancer for high availability
4. **Auto Scaling**: Set up auto scaling groups for EC2 instances
5. **CI/CD**: Implement deployment pipeline with AWS CodePipeline

## 📞 Support

For issues:
1. Check AWS service health dashboard
2. Review CloudWatch logs
3. Check IAM permissions
4. Verify service quotas

---

🍕 **Happy Pizza Deployment!** 🚀