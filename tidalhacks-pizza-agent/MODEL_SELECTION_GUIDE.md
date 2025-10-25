# AWS Bedrock Model Selection Guide

## 🤖 Available Models for Pizza Agent

### Google Gemini Models (Recommended)

#### Gemini 1.5 Pro (`google.gemini-1.5-pro-v1:0`)
- **Best for**: Creative story evaluation, detailed responses
- **Max tokens**: 8,192
- **Cost**: $0.0025 per 1K input, $0.0075 per 1K output
- **Strengths**: 
  - Excellent at understanding context and creativity
  - Great for generating personalized responses
  - Strong reasoning capabilities
  - Longer context window
- **Use case**: Primary model for production

#### Gemini 1.5 Flash (`google.gemini-1.5-flash-v1:0`)
- **Best for**: Fast responses, cost optimization
- **Max tokens**: 8,192
- **Cost**: $0.00075 per 1K input, $0.003 per 1K output
- **Strengths**:
  - 3x faster than Gemini Pro
  - 70% lower cost
  - Still maintains good quality
- **Use case**: High-volume events, cost-sensitive deployments

### Anthropic Claude Models (Alternative)

#### Claude 3 Sonnet (`anthropic.claude-3-sonnet-20240229-v1:0`)
- **Best for**: Balanced performance and reliability
- **Max tokens**: 4,096
- **Cost**: $0.003 per 1K input, $0.015 per 1K output
- **Strengths**:
  - Very reliable and consistent
  - Good at following instructions
  - Strong safety features
- **Use case**: Fallback if Gemini unavailable

#### Claude 3 Haiku (`anthropic.claude-3-haiku-20240307-v1:0`)
- **Best for**: Ultra-fast, cost-effective responses
- **Max tokens**: 4,096
- **Cost**: $0.00025 per 1K input, $0.00125 per 1K output
- **Strengths**:
  - Fastest response times
  - Lowest cost
  - Good for simple tasks
- **Use case**: Budget-conscious deployments

## 📊 Performance Comparison

| Model | Speed | Cost | Creativity | Context | Best For |
|-------|-------|------|------------|---------|----------|
| Gemini 1.5 Pro | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Production |
| Gemini 1.5 Flash | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | High Volume |
| Claude 3 Sonnet | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Reliable |
| Claude 3 Haiku | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Budget |

## 💰 Cost Analysis for 1000 Users

Assuming average story length of 100 tokens and response length of 200 tokens:

### Gemini 1.5 Pro
- Input: 1000 × 100 tokens = 100K tokens = $0.25
- Output: 1000 × 200 tokens = 200K tokens = $1.50
- **Total: $1.75**

### Gemini 1.5 Flash
- Input: 100K tokens = $0.075
- Output: 200K tokens = $0.60
- **Total: $0.675**

### Claude 3 Sonnet
- Input: 100K tokens = $0.30
- Output: 200K tokens = $3.00
- **Total: $3.30**

### Claude 3 Haiku
- Input: 100K tokens = $0.025
- Output: 200K tokens = $0.25
- **Total: $0.275**

## 🎯 Recommendations by Use Case

### Hackathon/Conference (Recommended: Gemini 1.5 Pro)
```bash
BEDROCK_MODEL_ID=google.gemini-1.5-pro-v1:0
```
- Best balance of creativity and cost
- Excellent story evaluation
- Great personalized responses
- Professional quality output

### High-Volume Event (Recommended: Gemini 1.5 Flash)
```bash
BEDROCK_MODEL_ID=google.gemini-1.5-flash-v1:0
```
- 3x faster responses
- 70% cost savings
- Still maintains good quality
- Handles traffic spikes well

### Budget-Conscious (Recommended: Claude 3 Haiku)
```bash
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
```
- Lowest cost option
- Fastest responses
- Good enough quality for basic use
- Minimal AWS charges

### Maximum Reliability (Recommended: Claude 3 Sonnet)
```bash
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```
- Most consistent outputs
- Strong safety features
- Reliable performance
- Good fallback option

## 🔧 How to Switch Models

### Method 1: Environment Variable
Edit your `.env` file:
```bash
# Switch to Gemini Flash for speed
BEDROCK_MODEL_ID=google.gemini-1.5-flash-v1:0

# Switch to Claude for reliability
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

### Method 2: Use Pre-configured Templates
```bash
# Use Gemini configuration
cp .env.gemini .env

# Use AWS default (Claude)
cp .env.aws .env
```

### Method 3: Runtime Switching (Advanced)
```python
from aws_bedrock import get_bedrock_ai

# Initialize with default model
ai = get_bedrock_ai()

# Switch to different model
ai.switch_model("google.gemini-1.5-flash-v1:0")
```

## 🧪 Testing Different Models

Test all models with the test script:
```bash
# Test current model
python test_aws_integration.py

# Test specific model
BEDROCK_MODEL_ID=google.gemini-1.5-flash-v1:0 python test_aws_integration.py
```

## 📈 Model Performance for Pizza Stories

Based on testing with pizza-related content:

### Story Evaluation Quality
1. **Gemini 1.5 Pro**: Excellent creativity assessment, understands humor
2. **Gemini 1.5 Flash**: Good creativity assessment, slightly less nuanced
3. **Claude 3 Sonnet**: Reliable but conservative ratings
4. **Claude 3 Haiku**: Basic evaluation, tends to be generous

### Response Personalization
1. **Gemini 1.5 Pro**: Highly personalized, references story details
2. **Gemini 1.5 Flash**: Good personalization, slightly more generic
3. **Claude 3 Sonnet**: Professional but less creative responses
4. **Claude 3 Haiku**: Simple, functional responses

### Prompt Generation
1. **Gemini 1.5 Pro**: Creative, varied prompts with personality
2. **Gemini 1.5 Flash**: Good variety, slightly less creative
3. **Claude 3 Sonnet**: Professional, consistent prompts
4. **Claude 3 Haiku**: Basic prompts, functional

## 🚀 Quick Start Recommendations

### For CalHacks 2024 (Recommended Setup)
```bash
# Copy Gemini configuration
cp .env.gemini .env

# Edit with your AWS credentials
# Keep default: BEDROCK_MODEL_ID=google.gemini-1.5-pro-v1:0

# Run setup
python setup_aws.py

# Test
python test_aws_integration.py

# Deploy
python aws_web_interface.py
```

### For Large Scale Events (1000+ users)
```bash
# Use Gemini Flash for speed and cost
sed -i 's/gemini-1.5-pro/gemini-1.5-flash/' .env

# Or manually edit:
# BEDROCK_MODEL_ID=google.gemini-1.5-flash-v1:0
```

### For Budget Deployments
```bash
# Use Claude Haiku for minimum cost
echo "BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0" >> .env
```

## 🔍 Model Access Requirements

### Gemini Models
1. Go to AWS Bedrock console
2. Navigate to "Model access"
3. Request access to "Google" models
4. Usually approved instantly

### Claude Models
1. Same process in Bedrock console
2. Request access to "Anthropic" models
3. Usually approved instantly

### Verification
```bash
# Check available models
python bedrock_models.py

# Test access
python setup_aws.py
```

## 📞 Troubleshooting

### Model Access Denied
- Ensure you've requested access in Bedrock console
- Check IAM permissions include `bedrock:InvokeModel`
- Verify model ID is correct

### High Costs
- Switch to Gemini Flash or Claude Haiku
- Monitor token usage in CloudWatch
- Set up billing alerts

### Slow Responses
- Switch to Gemini Flash or Claude Haiku
- Check AWS region latency
- Consider caching responses

### Poor Quality Responses
- Switch to Gemini Pro or Claude Sonnet
- Adjust temperature settings
- Review prompt engineering

---

**Recommendation**: Start with **Gemini 1.5 Pro** for the best balance of quality and cost for hackathon use cases. Switch to **Gemini 1.5 Flash** if you need faster responses or have budget constraints.