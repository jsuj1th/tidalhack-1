# 📧 Quick Email Setup Guide

## For Gmail Users (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Copy the 16-character password

3. **Update .env file**:
```bash
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your_16_character_app_password
EMAIL_FROM_NAME=Pizza Agent
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

## Test Email Configuration

Run this to test your setup:
```bash
python -c "from email_utils import test_email_configuration; print(test_email_configuration())"
```

## Using the Web Interface

1. Start the web interface: `python web_test_interface.py`
2. Go to http://127.0.0.1:5000
3. Check if "EMAIL_CONFIGURED" shows ✅
4. Enter a story and your email address
5. Click "📧 Generate & Email Coupon"

## Other Email Providers

For other providers, update these in `.env`:
- `SMTP_SERVER`: Your provider's SMTP server
- `SMTP_PORT`: Usually 587 for TLS
- `EMAIL_ADDRESS`: Your email address
- `EMAIL_PASSWORD`: Your email password

Common SMTP servers:
- **Outlook/Hotmail**: smtp-mail.outlook.com:587
- **Yahoo**: smtp.mail.yahoo.com:587
- **Custom domain**: Check with your provider

## Troubleshooting

- **"Email not configured"**: Check your .env file
- **"Authentication failed"**: Verify email/password
- **"Connection failed"**: Check SMTP server/port
- **Gmail issues**: Make sure you're using App Password, not regular password