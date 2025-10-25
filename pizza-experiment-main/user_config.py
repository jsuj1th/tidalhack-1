# user_config.py
"""
User-specific configuration for the Pizza Agent system
Store user preferences and contact information here
"""

# User Information
USER_EMAIL = "sujithjulakanti2002@gmail.com"
USER_NAME = "Sujith Julakanti"

# Test Configuration
DEFAULT_TEST_EMAIL = USER_EMAIL
TEST_USER_IDENTIFIER = "sujith_test_user"

# Email Preferences
EMAIL_NOTIFICATIONS = True
SEND_TEST_EMAILS_TO_USER = True

# Development Settings
DEBUG_MODE = True
VERBOSE_LOGGING = True

# Conference Preferences
PREFERRED_PIZZA_SIZE = "LARGE"
FAVORITE_TOPPINGS = ["pepperoni", "extra cheese", "mushrooms"]

def get_user_email():
    """Get the default user email for testing"""
    return USER_EMAIL

def get_test_config():
    """Get test configuration with user email"""
    return {
        "email": USER_EMAIL,
        "name": USER_NAME,
        "user_id": TEST_USER_IDENTIFIER
    }

if __name__ == "__main__":
    print(f"User Email: {USER_EMAIL}")
    print(f"User Name: {USER_NAME}")
    print(f"Test Config: {get_test_config()}")