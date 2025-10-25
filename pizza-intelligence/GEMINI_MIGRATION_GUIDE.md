# Gemini API Migration Guide

This guide explains how to migrate the Pizza Experiment from OpenAI API to Google's Gemini API.

## What Changed

### 🔄 API Migration
- **Removed**: OpenAI API integration (`openai_functions.py`)
- **Added**: Google Gemini API integration (`gemini_functions.py`)
- **Updated**: All AI functions now use Gemini instead of OpenAI or ASI1

### 📦 Dependencies
- **Removed**: `openai` package
- **Added**: `google-generativeai` package

### ⚙️ Configuration Changes
- **Removed**: `USE_OPENAI` flag
- **Added**: `USE_GEMINI` flag
- **Updated**: Model configuration now uses `GEMINI_MODEL` instead of `OPENAI_MODEL`

## Setup Instructions

### 1. Install Dependencies
```bash
cd pizza-intelligence
pip install -r requirements.txt
```

### 2. Get Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Copy the API key

### 3. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Gemini API key
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 4. Test the Migration
```bash
# Test Gemini functions
python gemini_functions.py

# Test AI functions with Gemini
python ai_functions.py

# Run the agent
python agent.py
```

## Key Features Migrated

### ✅ Story Evaluation
- Uses Gemini to rate pizza stories (1-10 scale)
- Maintains same evaluation criteria
- Robust fallback to rule-based evaluation

### ✅ Intent Detection
- Gemini analyzes user messages to understand intent
- Determines if user wants pizza coupon
- Fallback to keyword matching

### ✅ Dynamic Prompt Generation
- Gemini creates unique, engaging prompts
- Maintains TamuHacks 12.0 theme
- Fallback to static prompts

### ✅ Personalized Responses
- Gemini generates custom responses based on stories
- Acknowledges specific story details
- Maintains enthusiasm levels based on ratings

### ✅ Spam Detection
- Gemini analyzes messages for spam/abuse
- Maintains lenient approach for conference fun
- Fallback to basic keyword detection

## Configuration Options

### Environment Variables
```bash
# Required
GEMINI_API_KEY=your_api_key

# Optional (with defaults)
GEMINI_TIMEOUT=10.0          # Request timeout in seconds
GEMINI_RETRY_COUNT=2         # Number of retries on failure
ENVIRONMENT=development      # Environment mode
```

### Config.py Settings
```python
# Enable/disable Gemini features
USE_GEMINI = True           # Use Gemini for AI functions
USE_AI_EVALUATION = True    # Use AI for story evaluation
USE_AI_RESPONSES = True     # Generate AI responses
USE_AI_MODERATION = True    # Use AI spam detection
USE_AI_PROMPTS = True       # Generate dynamic prompts

# Gemini model configuration
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_TEMPERATURE = 0.9
```

## Error Handling & Fallbacks

The migration maintains robust error handling:

1. **API Failures**: Automatic fallback to static responses
2. **Rate Limiting**: Built-in retry logic with exponential backoff
3. **Timeout Protection**: Configurable timeouts prevent hanging
4. **Failure Tracking**: Monitors API health and switches to fallbacks

## Performance Considerations

### Gemini Advantages
- **Cost Effective**: Generally lower cost than OpenAI
- **Fast Response**: Quick generation times
- **Reliable**: Good uptime and availability
- **Flexible**: Handles various prompt styles well

### Optimization Tips
- Adjust `GEMINI_TIMEOUT` based on your needs
- Monitor failure rates and adjust retry counts
- Use fallbacks for critical path operations

## Testing

### Unit Tests
```bash
# Test individual functions
python -c "import asyncio; from gemini_functions import test_gemini_functions; asyncio.run(test_gemini_functions())"
```

### Integration Tests
```bash
# Test full agent functionality
python test_feedback_agent.py
```

## Troubleshooting

### Common Issues

1. **API Key Not Working**
   - Verify key is correct in `.env` file
   - Check Google AI Studio for key status
   - Ensure billing is enabled if required

2. **Import Errors**
   - Run `pip install google-generativeai`
   - Check Python version compatibility

3. **Timeout Issues**
   - Increase `GEMINI_TIMEOUT` value
   - Check network connectivity
   - Monitor API status

4. **Fallback Behavior**
   - Check logs for error messages
   - Verify fallback functions work correctly
   - Monitor failure counter in logs

### Debug Mode
Set `ENVIRONMENT=development` in `.env` for detailed logging.

## Migration Checklist

- [ ] Install `google-generativeai` package
- [ ] Remove `openai` package (optional)
- [ ] Get Gemini API key from Google AI Studio
- [ ] Create `.env` file with `GEMINI_API_KEY`
- [ ] Update `config.py` settings if needed
- [ ] Test all AI functions work correctly
- [ ] Verify fallbacks work when API fails
- [ ] Run integration tests
- [ ] Deploy with new configuration

## Support

If you encounter issues:
1. Check the logs for specific error messages
2. Verify your API key and billing status
3. Test with the provided test functions
4. Check Google AI Studio documentation

The migration maintains full backward compatibility with existing functionality while providing the benefits of Google's Gemini API.