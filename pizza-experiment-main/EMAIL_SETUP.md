# 📧 Email Coupon Delivery Setup

The Pizza Agent now supports sending coupons via email! Users can receive beautifully formatted HTML emails with their coupon codes.

## 🚀 Features

- **HTML Email Templates**: Professional-looking emails with coupon codes
- **Email Validation**: Ensures valid email addresses
- **Fallback Support**: Works even if email service is not configured
- **Web Interface**: Test email functionality through the web interface
- **Agent Integration**: Users can request email delivery through chat

## ⚙️ Configuration

### 1. Environment Variables

Add these to your `.env` file:

```bash
# Email Configuration (Optional)
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_FROM_NAME=TamuHacks Pizza Agent
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### 2. Gmail Setup (Recommended)

For Gmail accounts:

1. **Enable 2-Factor Authentication**
   - Go to Google Account settings
   - Security → 2-Step Verification → Turn on

2. **Generate App Password**
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and your device
   - Copy the 16-character password

3. **Use App Password**
   - Use the app password (not your regular password) in `EMAIL_PASSWORD`

### 3. Other Email Providers

For other SMTP providers, update:
- `SMTP_SERVER`: Your provider's SMTP server
- `SMTP_PORT`: Usually 587 for TLS or 465 for SSL
- `EMAIL_ADDRESS`: Your email address
- `EMAIL_PASSWORD`: Your email password or app password

## 🎯 Usage

### Web Interface

1. Generate a coupon using the web interface
2. Enter your email address in the "Email Coupon Option" section
3. Click "Send via Email"
4. Check your inbox (and spam folder)

### Chat Agent

Users can request email delivery by:

```
"Send email to john@example.com"
"Email me the coupon at jane@university.edu"
"Can you email it to my.email@domain.com?"
```

## 📧 Email Template Features

The email includes:
- **Professional HTML design** with TamuHacks branding
- **Coupon code** prominently displayed
- **Tier information** (Premium/Standard/Basic)
- **Story rating** that earned the coupon
- **Redemption instructions** for the conference
- **Personalized message** from the AI agent
- **Mobile-responsive** design

## 🔧 Testing

### Check Configuration

```bash
python email_utils.py
```

### Web Interface Test

1. Start the web interface: `python web_test_interface.py`
2. Go to http://127.0.0.1:5000
3. Check the "EMAIL_CONFIGURED" status
4. Test email sending with the coupon generator

### Manual Test

```python
from email_utils import send_coupon_email

result = send_coupon_email(
    "test@example.com",
    "PIZZA-TEST-PREMIUM-ABC123-1234",
    "PREMIUM",
    9,
    "🎉 Amazing story! You've earned a premium pizza!"
)
print(result)
```

## 🛡️ Security & Privacy

- **Email validation** prevents invalid addresses
- **No email storage** - emails are sent immediately
- **Error handling** for failed deliveries
- **Rate limiting** can be added if needed
- **SMTP encryption** (TLS/SSL) for secure transmission

## 🚨 Troubleshooting

### Common Issues

1. **"Authentication failed"**
   - Check if you're using an app password (not regular password)
   - Verify 2FA is enabled for Gmail

2. **"SMTP connection failed"**
   - Check SMTP server and port settings
   - Verify internet connection
   - Try different SMTP servers

3. **"Email not received"**
   - Check spam/junk folder
   - Verify email address is correct
   - Check email provider's delivery logs

### Debug Mode

Set environment variable for debugging:
```bash
export SMTP_DEBUG=1
```

## 📱 Mobile Compatibility

The HTML email template is mobile-responsive and works well on:
- iPhone Mail app
- Gmail mobile app
- Outlook mobile
- Most email clients

## 🎨 Customization

To customize the email template, edit `email_utils.py`:
- Modify the HTML template in `create_coupon_email()`
- Change colors, fonts, and styling
- Add your own branding elements
- Update the email subject line

## 🔄 Fallback Behavior

If email is not configured:
- Web interface shows "❌ Not Configured" status
- Agent still works normally without email features
- Users get coupons through chat as usual
- No errors or crashes occur

This ensures the pizza agent works perfectly even without email setup!