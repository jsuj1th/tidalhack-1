# 🚀 Hackathon Feedback Collection System

A production-ready AI-powered system for collecting and analyzing participant feedback at hackathons. Built with uAgents framework and designed for AWS deployment.

## 🌟 Features

- **AI-Powered Analysis**: Automatic sentiment analysis and categorization using Google Gemini 2.0 Flash
- **Real-time Collection**: Interactive chat-based feedback collection
- **AWS Integration**: Full AWS deployment with DynamoDB, S3, and CloudWatch
- **Analytics Dashboard**: Comprehensive feedback analytics and insights
- **Scalable Architecture**: Serverless deployment with Lambda functions
- **Production Ready**: Comprehensive error handling, logging, and monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   uAgents Bot   │───▶│  Lambda API  │───▶│   DynamoDB      │
│  (Chat Interface)│    │  (Processing)│    │  (Data Storage) │
└─────────────────┘    └──────────────┘    └─────────────────┘
                              │                       │
                              ▼                       ▼
                       ┌──────────────┐    ┌─────────────────┐
                       │  OpenAI API  │    │   S3 Backup     │
                       │ (AI Analysis)│    │  (Data Archive) │
                       └──────────────┘    └─────────────────┘
                              │                       │
                              ▼                       ▼
                       ┌──────────────┐    ┌─────────────────┐
                       │  CloudWatch  │    │   Analytics     │
                       │ (Monitoring) │    │   Dashboard     │
                       └──────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- AWS Account with appropriate permissions
- Google AI Studio API key (for Gemini)
- Docker (optional, for local development)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd hackathon-feedback-system

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your configuration
```

### 3. Configuration

Edit `.env` file with your settings:

```bash
# Required
GOOGLE_API_KEY=your_google_api_key
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Hackathon Details
HACKATHON_ID=HACK2024
HACKATHON_NAME="Your Hackathon Name"
```

### 4. Local Development

```bash
# Run with Docker Compose (recommended)
cd deployment/docker
docker-compose up -d

# Or run directly
python agent.py
```

### 5. AWS Deployment

#### Option A: Terraform (Recommended)

```bash
cd deployment/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="hackathon_id=HACK2024" -var="environment=prod"

# Deploy infrastructure
terraform apply
```

#### Option B: Manual AWS Setup

1. **Create DynamoDB Table**:
   ```bash
   aws dynamodb create-table \
     --table-name hackathon-feedback \
     --attribute-definitions \
       AttributeName=feedback_id,AttributeType=S \
       AttributeName=hackathon_id,AttributeType=S \
       AttributeName=timestamp,AttributeType=S \
     --key-schema AttributeName=feedback_id,KeyType=HASH \
     --global-secondary-indexes \
       IndexName=hackathon-timestamp-index,KeySchema=[{AttributeName=hackathon_id,KeyType=HASH},{AttributeName=timestamp,KeyType=RANGE}],Projection={ProjectionType=ALL} \
     --billing-mode PAY_PER_REQUEST
   ```

2. **Create S3 Bucket**:
   ```bash
   aws s3 mb s3://hackathon-feedback-data-your-suffix
   ```

3. **Deploy Lambda Function**:
   ```bash
   # Package the Lambda function
   cd deployment
   zip -r lambda_deployment.zip lambda_function.py ../aws_services.py ../functions.py ../config.py

   # Create Lambda function
   aws lambda create-function \
     --function-name hackathon-feedback-processor \
     --runtime python3.11 \
     --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
     --handler lambda_function.lambda_handler \
     --zip-file fileb://lambda_deployment.zip
   ```

## 💬 User Experience

### Participant Interaction Flow

1. **Initial Contact**:
   ```
   User: "I want to give feedback"
   
   Bot: "🚀 Welcome to TechHack 2024! I'm your feedback assistant! 💡
   
   Before the event kicks off, I'd love to hear about your expectations!
   Tell me:
   • What are you hoping to learn or achieve?
   • What kind of projects excite you?
   • Any specific workshops or mentorship you're looking for?
   
   Share your thoughts - every opinion matters! 🎯"
   ```

2. **Feedback Collection**:
   ```
   User: "I'm excited about learning AI and machine learning! I hope 
   there will be good mentorship and maybe some workshops on neural 
   networks. I'm also looking forward to networking with other developers."
   
   Bot: "🎉 Thank you for your enthusiastic feedback about TechHack 2024!
   
   🌟 I can feel your excitement about AI and machine learning! Your 
   interest in neural networks and networking shows you're ready to make 
   the most of this hackathon.
   
   Your feedback has been recorded and will help the organizers ensure 
   we have great AI mentors and workshops. We're working hard to create 
   amazing networking opportunities too!
   
   🚀 Get ready for an incredible hackathon! See you at the event!"
   ```

## 📊 Analytics & Monitoring

### Available Metrics

- **Feedback Volume**: Total submissions over time
- **Sentiment Distribution**: Positive/Negative/Neutral breakdown
- **Category Analysis**: Expectations, Logistics, Technical, etc.
- **Participant Insights**: Common themes and concerns

### CloudWatch Dashboard

Access your dashboard at:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=hackathon-feedback-dashboard
```

### Analytics API

```python
# Get feedback summary
import requests

response = requests.post('YOUR_API_GATEWAY_URL', json={
    'action': 'get_analytics',
    'data': {'hackathon_id': 'HACK2024'}
})

analytics = response.json()
print(f"Total feedback: {analytics['total_feedback']}")
print(f"Sentiment: {analytics['sentiment_distribution']}")
```

## 🔧 Configuration Options

### Core Settings

```python
# config.py
HACKATHON_ID = "HACK2024"  # Your event identifier
HACKATHON_NAME = "TechHack 2024"  # Display name
MAX_REQUESTS_PER_USER = 3  # Feedback limit per participant
```

### AI Features

```python
USE_AI_ANALYSIS = True      # Enable AI-powered analysis
USE_AI_RESPONSES = True     # Generate personalized responses
USE_AI_SENTIMENT = True     # Sentiment analysis
USE_AI_CATEGORIZATION = True # Auto-categorize feedback
```

### AWS Services

```python
DYNAMODB_TABLE_NAME = "hackathon-feedback"
S3_BUCKET_NAME = "hackathon-feedback-data"
CLOUDWATCH_METRICS_NAMESPACE = "HackathonFeedback"
```

## 🛠️ Development

### Local Testing

```bash
# Test core functions
python functions.py

# Test AI functions (requires Google API key)
python ai_functions.py

# Test AWS services (requires AWS credentials)
python aws_services.py

# Run full agent
python agent.py
```

### Adding New Features

1. **New Feedback Categories**: Edit `FEEDBACK_CATEGORIES` in `config.py`
2. **Custom AI Prompts**: Modify prompts in `ai_functions.py`
3. **Additional Analytics**: Extend `generate_analytics()` in `aws_services.py`

### Code Quality

```bash
# Format code
black *.py

# Lint code
flake8 *.py

# Run tests
pytest tests/
```

## 📈 Production Deployment Checklist

- [ ] Configure environment variables in `.env`
- [ ] Set up AWS credentials and permissions
- [ ] Deploy infrastructure with Terraform
- [ ] Test feedback collection end-to-end
- [ ] Configure CloudWatch alerts
- [ ] Set up backup and monitoring
- [ ] Brief event staff on system usage
- [ ] Monitor during event

## 🔒 Security Considerations

1. **Data Privacy**: All feedback is encrypted at rest and in transit
2. **Rate Limiting**: Prevents spam and abuse
3. **Input Validation**: Sanitizes all user input
4. **Access Control**: AWS IAM roles with minimal permissions
5. **Audit Trail**: Complete logging of all operations

## 🐛 Troubleshooting

### Common Issues

**Agent not responding:**
- Check AWS credentials and permissions
- Verify Google API key is valid
- Check CloudWatch logs for errors

**DynamoDB errors:**
- Ensure table exists and has correct schema
- Check IAM permissions for DynamoDB access
- Verify region configuration

**AI analysis failing:**
- Check Google API key and quota
- Review API rate limits
- Check network connectivity

### Logs and Debugging

```bash
# View Lambda logs
aws logs tail /aws/lambda/hackathon-feedback-processor --follow

# Check DynamoDB table
aws dynamodb scan --table-name hackathon-feedback --max-items 5

# View CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace HackathonFeedback \
  --metric-name FeedbackSubmitted \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review CloudWatch logs for error details
3. Test with the provided validation functions
4. Consult AWS and uAgents documentation

## 📜 License

This project is provided as-is for hackathon use. Modify as needed for your event.

---

**Ready to collect some amazing feedback? 🚀✨**