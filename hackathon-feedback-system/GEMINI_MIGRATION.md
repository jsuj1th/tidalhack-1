# 🔄 Migration Guide: OpenAI to Google Gemini

This guide helps you migrate from OpenAI to Google Gemini 2.0 Flash for better performance and cost efficiency.

## 🎯 Why Gemini?

- **Cost Effective**: Generous free tier, much lower costs than OpenAI
- **High Performance**: Gemini 2.0 Flash is optimized for speed and quality
- **Better Context**: Larger context window for processing more feedback
- **Multimodal**: Ready for future features like image analysis

## 🔧 Migration Steps

### 1. Get Google AI Studio API Key

1. Visit [aistudio.google.com](https://aistudio.google.com)
2. Sign in with your Google account
3. Click "Get API key" in the left sidebar
4. Create a new API key
5. Copy the key (starts with `AIza...`)

### 2. Update Environment Variables

Replace in your `.env` file:
```bash
# OLD - OpenAI
OPENAI_API_KEY=sk-your-openai-key

# NEW - Google Gemini
GOOGLE_API_KEY=AIza-your-google-key
```

### 3. Install New Dependencies

```bash
# Remove OpenAI dependency
pip uninstall openai

# Install Google Generative AI
pip install google-generativeai>=0.8.0
```

### 4. Update Configuration

The system automatically uses Gemini when `GOOGLE_API_KEY` is set. No code changes needed!

## 📊 Performance Comparison

| Feature | OpenAI GPT-4o-mini | Gemini 2.0 Flash |
|---------|-------------------|-------------------|
| **Cost** | $0.15/1M tokens | Free tier + $0.075/1M |
| **Speed** | ~2-3 seconds | ~1-2 seconds |
| **Context** | 128K tokens | 1M tokens |
| **Quality** | Excellent | Excellent |
| **Rate Limits** | 500 RPM | 1000 RPM (free) |

## 🧪 Testing Your Migration

Run the test script to verify everything works:

```bash
python test_system.py
```

You should see:
```
Testing Gemini AI functions...
✅ Analysis: {'sentiment': 'positive', 'category': 'EXPECTATIONS', ...}
✅ Response: Thank you for your enthusiastic feedback...
✅ Category: EXPECTATIONS
✅ Spam Detection: Not spam
```

## 🔍 Key Differences

### Response Format
- **OpenAI**: Sometimes includes markdown formatting
- **Gemini**: Clean text responses, automatically strips formatting

### JSON Parsing
- **OpenAI**: Consistent JSON structure
- **Gemini**: May include code blocks, automatically cleaned

### Error Handling
- **OpenAI**: Rate limit errors, quota exceeded
- **Gemini**: Different error codes, handled automatically

## 💡 Optimization Tips

### 1. Model Selection
```python
# Current default (recommended)
GEMINI_MODEL = "gemini-2.0-flash-exp"

# For production stability
GEMINI_MODEL = "gemini-1.5-pro"

# For maximum speed
GEMINI_MODEL = "gemini-1.5-flash"
```

### 2. Temperature Settings
```python
# For consistent categorization
GEMINI_TEMPERATURE = 0.1

# For creative responses
GEMINI_TEMPERATURE = 0.9

# Balanced (default)
GEMINI_TEMPERATURE = 0.7
```

### 3. Token Management
```python
# Adjust based on your needs
GEMINI_MAX_TOKENS = 1000  # Standard responses
GEMINI_MAX_TOKENS = 2000  # Detailed reports
GEMINI_MAX_TOKENS = 500   # Quick categorization
```

## 🚨 Troubleshooting

### Common Issues

**"Google API key not configured"**
```bash
# Check your .env file
cat .env | grep GOOGLE_API_KEY

# Verify the key format (should start with AIza)
echo $GOOGLE_API_KEY
```

**"Model not found"**
```bash
# Update to latest model
GEMINI_MODEL = "gemini-2.0-flash-exp"

# Or use stable version
GEMINI_MODEL = "gemini-1.5-pro"
```

**"Rate limit exceeded"**
- Gemini has generous free tier limits
- Consider upgrading to paid tier for high volume
- Implement exponential backoff (already included)

### API Quota Limits

**Free Tier:**
- 15 requests per minute
- 1,500 requests per day
- 1 million tokens per minute

**Paid Tier:**
- 1,000 requests per minute
- No daily limit
- 4 million tokens per minute

## 🎉 Benefits After Migration

### Cost Savings
- **Before**: $20-30 for large hackathon
- **After**: $5-10 for large hackathon
- **Savings**: 60-75% cost reduction

### Performance Improvements
- **Faster responses**: 1-2 seconds vs 2-3 seconds
- **Better context**: Can process longer feedback
- **Higher rate limits**: More concurrent users

### Enhanced Features
- **Better multilingual support**: Great for international hackathons
- **Improved reasoning**: Better categorization accuracy
- **Future-ready**: Access to latest Google AI features

## 🔄 Rollback Plan

If you need to rollback to OpenAI:

1. **Keep both API keys** in your `.env`:
```bash
GOOGLE_API_KEY=your-google-key
OPENAI_API_KEY=your-openai-key  # Backup
```

2. **Modify config.py** to switch back:
```python
USE_GEMINI = False  # Switch to OpenAI
```

3. **Reinstall OpenAI**:
```bash
pip install openai>=1.0.0
```

## 📞 Support

- **Google AI Studio**: [aistudio.google.com](https://aistudio.google.com)
- **Documentation**: [ai.google.dev](https://ai.google.dev)
- **Community**: [Google AI Discord](https://discord.gg/google-ai)

---

**Ready to enjoy faster, cheaper AI analysis? 🚀**