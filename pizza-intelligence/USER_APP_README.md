# 🍕 Pizza Coupon Generator - User App

A clean, production-ready web interface for users to get pizza coupons by sharing their pizza stories.

## 🚀 Quick Start

1. **Check your setup**:
```bash
python check_setup.py
```

2. **Start the app**:
```bash
python pizza_coupon_app.py
```

3. **Open in browser**: http://127.0.0.1:5002

## ✨ Features

- **Clean, mobile-friendly interface**
- **Story-based coupon generation** with AI evaluation
- **Email delivery** of beautifully formatted coupons
- **Three coupon tiers**: Premium, Standard, Basic
- **Copy-to-clipboard** functionality
- **Responsive design** for all devices

## 📧 Email Setup (Optional)

To enable email delivery, edit `.env`:

```bash
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_FROM_NAME=Pizza Agent
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

For Gmail:
1. Enable 2-Factor Authentication
2. Generate an App Password
3. Use the App Password (not your regular password)

## 🤖 AI Features (Optional)

For enhanced story evaluation and responses, add to `.env`:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

Without AI, the app uses rule-based evaluation and static responses.

## 🎯 How It Works

1. **User enters a pizza story** - The more creative and detailed, the better!
2. **AI evaluates the story** (or uses rule-based scoring)
3. **Coupon tier is determined**:
   - 8-10 rating: **Premium** (Large pizza with premium toppings)
   - 6-7 rating: **Standard** (Medium pizza with choice of toppings)
   - 1-5 rating: **Basic** (Regular pizza)
4. **Coupon is generated** with unique code
5. **Email sent** (if email provided and configured)

## 📱 User Experience

- **Simple form**: Story textarea + optional email
- **Instant feedback**: Loading states and clear results
- **Beautiful coupons**: Professional design with tier badges
- **Clear instructions**: How to redeem the coupon
- **Error handling**: Graceful fallbacks for any issues

## 🔧 Technical Details

- **Framework**: Flask (Python)
- **AI**: Google Gemini (optional)
- **Email**: SMTP with HTML templates
- **Frontend**: Vanilla JavaScript, responsive CSS
- **No database required**: Stateless operation

## 📂 Files

- `pizza_coupon_app.py` - Main user application
- `check_setup.py` - Setup verification tool
- `email_utils.py` - Email functionality
- `functions.py` - Core coupon logic
- `config.py` - Configuration settings
- `.env` - Environment variables (create this)

## 🎨 Customization

The interface can be easily customized by modifying the `USER_TEMPLATE` in `pizza_coupon_app.py`:

- Colors and styling in the `<style>` section
- Text and messaging in the HTML
- Form fields and validation in JavaScript

## 🛠️ Troubleshooting

**"Email not configured"**: Check your `.env` file and email settings

**"AI features not working"**: Verify your `GEMINI_API_KEY` in `.env`

**"Port already in use"**: Change the port in `app.run()` at the bottom of the file

**"Import errors"**: Install dependencies with `pip install -r requirements.txt`

## 🎉 Ready for Production!

This app is designed to be clean, user-friendly, and production-ready. No test functions, admin panels, or debugging interfaces - just a simple, beautiful way for users to get their pizza coupons!