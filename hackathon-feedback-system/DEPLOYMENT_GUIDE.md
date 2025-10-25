# 🚀 Deployment Guide for Beginners

This guide will help you deploy the hackathon feedback system to AWS, even if you're new to AWS.

## 📋 Prerequisites

1. **AWS Account**: Sign up at [aws.amazon.com](https://aws.amazon.com)
2. **OpenAI API Key**: Get one from [platform.openai.com](https://platform.openai.com)
3. **Python 3.11+**: Download from [python.org](https://python.org)
4. **Git**: Download from [git-scm.com](https://git-scm.com)

## 🔧 Step 1: AWS Setup

### 1.1 Create AWS Account
1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. Follow the registration process
4. **Important**: You'll need a credit card, but we'll use free tier services

### 1.2 Create IAM User (Recommended)
1. Go to AWS Console → IAM → Users
2. Click "Create user"
3. Username: `hackathon-feedback-user`
4. Select "Programmatic access"
5. Attach policies:
   - `AmazonDynamoDBFullAccess`
   - `AmazonS3FullAccess`
   - `AWSLambdaFullAccess`
   - `CloudWatchFullAccess`
   - `IAMFullAccess` (for setup only)
6. Save the Access Key ID and Secret Access Key

### 1.3 Install AWS CLI
```bash
# On macOS
brew install awscli

# On Windows
# Download from: https://aws.amazon.com/cli/

# On Linux
sudo apt-get install awscli
```

### 1.4 Configure AWS CLI
```bash
aws configure
# Enter your Access Key ID
# Enter your Secret Access Key
# Default region: us-east-1
# Default output format: json
```

## 🔑 Step 2: Get OpenAI API Key

1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. **Important**: Save this key securely

## 💻 Step 3: Local Setup

### 3.1 Clone and Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd hackathon-feedback-system

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### 3.2 Configure Environment
Edit `.env` file:
```bash
# Required - Replace with your values
OPENAI_API_KEY=sk-your-openai-key-here
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1

# Hackathon Details - Customize these
HACKATHON_ID=MYHACK2024
HACKATHON_NAME=My Awesome Hackathon 2024
HACKATHON_START_DATE=2024-12-01
HACKATHON_END_DATE=2024-12-03

# Environment
ENVIRONMENT=production
```

## 🏗️ Step 4: Deploy to AWS

### Option A: Automated Setup (Recommended for Beginners)

```bash
# Run the automated setup script
cd deployment
python setup_aws.py --environment production --project myhackathon

# This will create:
# - DynamoDB table
# - S3 bucket
# - IAM roles
# - Lambda function
# - CloudWatch dashboard
```

### Option B: Manual Setup

If the automated script fails, you can set up manually:

#### 4.1 Create DynamoDB Table
```bash
aws dynamodb create-table \
  --table-name hackathon-feedback-production \
  --attribute-definitions \
    AttributeName=feedback_id,AttributeType=S \
    AttributeName=hackathon_id,AttributeType=S \
    AttributeName=timestamp,AttributeType=S \
  --key-schema AttributeName=feedback_id,KeyType=HASH \
  --global-secondary-indexes \
    IndexName=hackathon-timestamp-index,KeySchema=[{AttributeName=hackathon_id,KeyType=HASH},{AttributeName=timestamp,KeyType=RANGE}],Projection={ProjectionType=ALL} \
  --billing-mode PAY_PER_REQUEST
```

#### 4.2 Create S3 Bucket
```bash
# Replace 'your-unique-suffix' with something unique
aws s3 mb s3://hackathon-feedback-production-data-your-unique-suffix
```

#### 4.3 Update Environment Variables
Update your `.env` file with the created resource names:
```bash
DYNAMODB_TABLE_NAME=hackathon-feedback-production
S3_BUCKET_NAME=hackathon-feedback-production-data-your-unique-suffix
```

## 🧪 Step 5: Test Your Setup

```bash
# Test the system
python test_system.py

# You should see:
# ✅ Core Functions working
# ✅ AI Functions working (if OpenAI key is valid)
# ✅ AWS Services working (if AWS is configured)
```

## 🤖 Step 6: Run the Agent

### Local Testing
```bash
# Run locally first to test
python agent.py

# You should see:
# 🚀 Starting TechHack 2024 Feedback Collection Agent...
# Agent Address: agent1q...
```

### Production Deployment

For production, you have several options:

#### Option A: AWS EC2 (Simplest)
1. Launch an EC2 instance (t2.micro is free tier)
2. Install Python and dependencies
3. Upload your code
4. Run with `nohup python agent.py &`

#### Option B: AWS Lambda (Serverless)
The Lambda function is already created by the setup script and handles API requests.

#### Option C: Docker Container
```bash
# Build and run with Docker
cd deployment/docker
docker-compose up -d
```

## 📊 Step 7: Monitor Your System

### CloudWatch Dashboard
1. Go to AWS Console → CloudWatch → Dashboards
2. Find your dashboard: `hackathon-feedback-production-dashboard`
3. Monitor feedback submissions and sentiment

### View Collected Data
```bash
# Check DynamoDB table
aws dynamodb scan --table-name hackathon-feedback-production --max-items 5

# Check S3 backups
aws s3 ls s3://your-bucket-name/feedback-backups/ --recursive
```

## 🎯 Step 8: Use at Your Event

### For Participants
Share these instructions with hackathon participants:

1. **Find the Agent**: Look for `@hackathon-feedback` (or your agent name)
2. **Start Conversation**: Send "I want to give feedback"
3. **Share Expectations**: Tell the agent about your hopes and expectations
4. **Get Confirmation**: Receive a personalized response

### For Organizers
- Monitor the CloudWatch dashboard for real-time feedback
- Export data from DynamoDB for analysis
- Use the analytics to improve your event

## 🔧 Troubleshooting

### Common Issues

**"AWS credentials not found"**
```bash
# Check your credentials
aws sts get-caller-identity

# If this fails, reconfigure
aws configure
```

**"OpenAI API key invalid"**
- Check your API key at platform.openai.com
- Make sure you have credits available
- Verify the key is correctly set in .env

**"DynamoDB table not found"**
```bash
# List your tables
aws dynamodb list-tables

# If missing, run setup again
python deployment/setup_aws.py
```

**"Agent not responding"**
- Check the agent is running: `ps aux | grep agent.py`
- Check logs for errors
- Verify network connectivity

### Getting Help

1. **Check Logs**: Look at CloudWatch logs for errors
2. **Test Components**: Run `python test_system.py`
3. **AWS Support**: Use AWS free tier support for account issues
4. **Documentation**: Check AWS and OpenAI documentation

## 💰 Cost Estimation

### AWS Costs (Free Tier)
- **DynamoDB**: 25GB free storage, 25 read/write units
- **S3**: 5GB free storage, 20,000 GET requests
- **Lambda**: 1M free requests, 400,000 GB-seconds
- **CloudWatch**: 10 custom metrics, 5GB log ingestion

### OpenAI Costs
- **GPT-4o-mini**: ~$0.15 per 1M input tokens
- **Estimated**: $5-20 for a typical hackathon (100-500 participants)

### Total Estimated Cost
- **Small hackathon** (50 participants): $2-5
- **Medium hackathon** (200 participants): $10-15
- **Large hackathon** (500+ participants): $20-30

## 🎉 You're Ready!

Congratulations! Your hackathon feedback system is now deployed and ready to collect valuable participant insights. 

### Next Steps
1. Test with a few team members first
2. Share the agent details with participants
3. Monitor the dashboard during your event
4. Export and analyze the data after the event

### Pro Tips
- Set up CloudWatch alarms for high error rates
- Create a backup plan for critical event data
- Have a technical contact available during the event
- Consider setting up multiple environments (dev/staging/prod)

Good luck with your hackathon! 🚀