# 🍕 Pizza Coupon Agent

A fun, interactive agent that distributes pizza coupons to conference attendees through story-based engagement. Built using the uAgents framework with **Google Gemini AI** integration for intelligent story evaluation and personalized responses.

## 🚀 Features

- **🤖 Gemini AI Integration**: Powered by Google's Gemini AI for intelligent interactions
- **📖 Interactive Storytelling**: Users share pizza stories to earn coupons
- **🎯 Smart Story Evaluation**: AI rates stories for creativity, relevance, and engagement
- **💬 Personalized Responses**: AI generates custom responses based on user stories
- **🎭 Dynamic Prompts**: AI creates unique, engaging prompts for each interaction
- **📧 Email Coupon Delivery**: Send beautifully formatted coupons via email
- **🏆 Dynamic Coupon Tiers**: Better stories = better coupons (Basic/Standard/Premium)
- **🛡️ Anti-Abuse Protection**: One coupon per user with AI-powered spam detection
- **⚙️ Conference Integration**: Configurable for different events
- **🏪 Vendor-Friendly**: Easy coupon validation for food vendors
- **🚀 Production Ready**: Comprehensive error handling, fallbacks, and logging

## 📋 Quick Start

### 1. Installation

```bash
# Clone or download the agent files
# Install dependencies
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

### 4. Configuration

Edit `config.py` to customize for your conference:

```python
CONFERENCE_ID = "YOURCONF24"  # Change this
CONFERENCE_NAME = "Your Conference 2024"
CONFERENCE_START_DATE = "2024-12-01"
CONFERENCE_END_DATE = "2024-12-03"

# Gemini AI Configuration
USE_GEMINI = True
GEMINI_MODEL = "gemini-1.5-flash"
```

### 5. Test the Setup

```bash
# Test Gemini integration
python test_gemini_migration.py
```

### 6. Run the Agent

```bash
python agents.py
```

### 7. Deploy

1. Ensure all tests pass with `python test_gemini_migration.py`
2. Run the agent with `python agent.py`
3. Test with real interactions

## 💬 User Experience

**Step 1**: User tags the agent
```
@fetch-pizza I want pizza!
```

**Step 2**: Agent requests a story (AI-generated prompt)
```
🧙‍♂️🍕 Greetings, CalHacks 12.0 code wizard! The Pizza Genie has materialized! ✨

You're casting powerful algorithms and debugging spells - Fetch.ai sees your 
hustle and wants to reward your magic with pizza! 💻⚡

**Share YOUR greatest pizza tale!** For example:
• Maybe it was that weird topping combo that powered an all-nighter
• Or your most epic pizza-fueled breakthrough moment
• Perhaps when pizza literally saved your merge conflict
• Any perfect slice during your hackathon grind!

⭐ Remember: Legendary stories earn PREMIUM pizzas, good ones get STANDARD, 
all stories get rewarded! Cast your best spell and unlock your pizza.reward()! 🎁
```

**Step 3**: User shares story
```
Once I was stuck in a snowstorm and the only place open was this tiny 
pizza shop. The owner made me a custom pizza with ingredients from his 
personal stash - best pizza of my life!
```

**Step 4**: Agent evaluates and rewards (AI-powered)
```
🎉 What an incredible story! I love how pizza literally saved your hackathon 
project during that snowstorm - that's the kind of dedication we celebrate! 

**🎫 Your Coupon Code: PIZZA-CALHACKS12-STANDARD-A7B2C3**

🍕 This gets you a MEDIUM pizza with classic toppings at CalHacks 12.0!
📱 Show this code at the Fetch.ai food booth
⭐ Story Rating: 7/10 - Solid storytelling! 👍
```

## 🏪 Vendor Integration

### For Food Vendors

Coupon codes follow this format:
```
PIZZA-[CONFERENCE]-[TIER]-[USER_HASH]-[TIME]
Example: PIZZA-FETCH24-PREMIUM-A7B2C3-1445
```

**Validation Process:**
1. Check format is correct
2. Verify conference ID matches your event
3. Accept TIER levels: BASIC, STANDARD, PREMIUM
4. Mark as redeemed to prevent reuse

**Coupon Tiers:**
- **BASIC**: Regular pizza
- **STANDARD**: Medium pizza with choice of toppings  
- **PREMIUM**: Large pizza with premium toppings

### Validation Helper

```python
from functions import extract_coupon_info

# Validate a coupon
info = extract_coupon_info("PIZZA-FETCH24-PREMIUM-A7B2C3-1445")
if info['valid']:
    print(f"Valid {info['tier']} coupon for {info['pizza_size']} pizza")
    print(f"Issued at: {info['time_issued']}")
else:
    print(f"Invalid coupon: {info['error']}")
```

## 🤖 AI Features (Powered by Gemini)

### Story Evaluation
- **Intelligent Rating**: Gemini evaluates stories on creativity, pizza relevance, storytelling quality, and effort
- **Fair Scoring**: Generous but fair 1-10 scale rating system
- **Fallback Protection**: Automatic fallback to rule-based evaluation if AI fails

### Personalized Responses  
- **Custom Messages**: Each response is uniquely generated based on the user's specific story
- **Appropriate Enthusiasm**: Response energy matches the story rating (higher ratings = more excitement)
- **Story Acknowledgment**: AI references specific details from the user's story

### Dynamic Prompts
- **Unique Every Time**: AI generates fresh, creative prompts for each interaction
- **Themed Personalities**: Pizza wizards, code sorcerers, debug detectives, and more
- **Hackathon Context**: Prompts are tailored to the coding/hackathon environment

### Smart Intent Detection
- **Natural Understanding**: AI analyzes user messages to understand what they want
- **Context Aware**: Determines if users want coupons, have questions, or are sharing stories
- **Fallback Ready**: Keyword matching backup if AI is unavailable

### Spam Protection
- **AI Moderation**: Intelligent detection of spam, abuse, or system gaming attempts
- **Lenient Approach**: Designed for fun conference activities, not overly strict
- **Basic Fallback**: Simple keyword detection as backup

## 🔧 Configuration Options

### Basic Settings
- `CONFERENCE_ID`: Your event identifier
- `AGENT_NAME`: Agent handle (default: "fetch-pizza")
- `MAX_REQUESTS_PER_USER`: Prevent abuse (default: 1)

### Gemini AI Settings
- `USE_GEMINI`: Enable Gemini AI features (default: True)
- `GEMINI_MODEL`: Model to use (default: "gemini-1.5-flash")
- `GEMINI_TIMEOUT`: Request timeout in seconds (default: 10.0)
- `GEMINI_RETRY_COUNT`: Number of retries on failure (default: 2)

### AI Feature Flags
- `USE_AI_EVALUATION`: Use AI for story evaluation (default: True)
- `USE_AI_RESPONSES`: Generate personalized AI responses (default: True)
- `USE_AI_PROMPTS`: Generate dynamic AI prompts (default: True)
- `USE_AI_MODERATION`: Use AI for spam detection (default: True)

### Story Evaluation
- `MIN_STORY_LENGTH`: Minimum characters required
- `STORY_EVALUATION_TIMEOUT`: AI evaluation timeout
- `FALLBACK_TO_RULE_BASED`: Use backup evaluation if AI fails

### Time Restrictions
- `ENABLE_TIME_RESTRICTIONS`: Only allow during conference hours
- `CONFERENCE_START_HOUR`: Start time (24h format)
- `CONFERENCE_END_HOUR`: End time (24h format)

### Security
- `ENABLE_SPAM_PROTECTION`: Basic abuse prevention
- `MAX_MESSAGE_LENGTH`: Limit message size
- `BLOCKED_WORDS`: Filter inappropriate content

## 📊 Analytics

The agent tracks:
- Total coupons issued
- Distribution by tier
- Hourly usage patterns
- Story ratings distribution

Access analytics:
```python
from functions import get_coupon_stats
stats = get_coupon_stats()
```

## 🛠 Development

### Testing
```bash
# Test Gemini migration
python test_gemini_migration.py

# Test Gemini functions
python gemini_functions.py

# Test AI functions
python ai_functions.py

# Test coupon generation
python functions.py

# Test story evaluation
python -c "from functions import evaluate_story_quality; print(evaluate_story_quality('test story'))"
```

### Environment Variables
```bash
# Required
export GEMINI_API_KEY=your_api_key_here

# Optional
export ENVIRONMENT=development  # or staging, production
export LOG_LEVEL=DEBUG
export GEMINI_TIMEOUT=10.0
export GEMINI_RETRY_COUNT=2
```

### Code Quality
```bash
# Format code
black agents.py functions.py config.py

# Lint code
flake8 agents.py functions.py config.py
```

## 📈 Deployment Checklist

- [ ] Get Gemini API key from Google AI Studio
- [ ] Set `GEMINI_API_KEY` in .env file
- [ ] Update `CONFERENCE_ID` in config.py
- [ ] Configure conference dates
- [ ] Run `python test_gemini_migration.py` (all tests should pass)
- [ ] Test coupon generation locally
- [ ] Test AI functions with real API calls
- [ ] Verify fallback behavior works
- [ ] Test end-to-end flow
- [ ] Brief vendors on coupon validation
- [ ] Monitor during conference

## 🔒 Security Considerations

1. **Rate Limiting**: One coupon per user prevents abuse
2. **Input Validation**: Messages are length-limited and sanitized
3. **Time Restrictions**: Optional conference-hours-only operation  
4. **Coupon Format**: Cryptographic hashes prevent guessing
5. **Session Management**: Proper state tracking prevents race conditions

## 📧 Email Coupon Delivery

The Pizza Agent now supports sending coupons via email with beautiful HTML templates!

### Setup Email (Optional)

1. **Add to .env file:**
```bash
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_FROM_NAME=CalHacks Pizza Agent
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

2. **For Gmail (Recommended):**
   - Enable 2-factor authentication
   - Generate an App Password (not your regular password)
   - Use the app password in `EMAIL_PASSWORD`

3. **Test Configuration:**
```bash
python demo_email_feature.py
```

### Usage

**Web Interface:**
- Generate a coupon and enter your email
- Click "Send via Email" 
- Check inbox (and spam folder)

**Chat Agent:**
Users can request email delivery:
```
"Send email to john@example.com"
"Email me the coupon at jane@university.edu"
"Can you email it to my.email@domain.com?"
```

### Email Features

- **Professional HTML design** with conference branding
- **Mobile-responsive** templates
- **Coupon code** prominently displayed
- **Tier and rating information**
- **Redemption instructions**
- **Personalized AI message**

### Fallback Behavior

If email is not configured:
- Agent works normally without email features
- Web interface shows configuration status
- No errors or functionality loss

📖 **Full Documentation**: See `EMAIL_SETUP.md` for detailed setup instructions.

## 🐛 Troubleshooting

**Agent not responding:**
- Check Gemini API key is set correctly
- Verify internet connectivity
- Check logs for errors

**Stories not being evaluated:**
- Confirm `GEMINI_API_KEY` is set in .env
- Check Gemini API quota/billing status
- Verify story meets minimum length
- Check if fallback evaluation is working

**AI functions failing:**
- Run `python test_gemini_migration.py` to diagnose
- Check Google AI Studio for API key status
- Verify `google-generativeai` package is installed
- Check network connectivity to Google services

**Coupons not generating:**
- Check conference date settings
- Verify user hasn't already received coupon
- Review time restriction settings

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review agent logs for error messages
3. Test with the provided validation functions
4. Consult uAgents documentation

## 📜 License

This agent is provided as-is for conference use. Modify as needed for your event.

## 🔄 Migration from OpenAI

This project has been migrated from OpenAI to Google Gemini API. If you're upgrading from a previous version:

1. **See Migration Guide**: Check `GEMINI_MIGRATION_GUIDE.md` for detailed migration instructions
2. **Update Dependencies**: Run `pip install -r requirements.txt` to get Gemini packages
3. **Get New API Key**: Obtain a Gemini API key from Google AI Studio
4. **Test Migration**: Run `python test_gemini_migration.py` to verify everything works
5. **Update Configuration**: Ensure `USE_GEMINI=True` in config.py

The migration maintains full backward compatibility while providing the benefits of Google's Gemini AI.

---

**Ready to distribute some pizza coupons with AI magic? 🍕🤖✨**