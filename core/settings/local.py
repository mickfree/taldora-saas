from .base import *
import sys

# Ensure debug is true for local environment
DEBUG = True

# Check if we are running unit tests
IS_RUNNING_TESTS = 'test' in sys.argv or any('test' in arg for arg in sys.argv)

# Add development-only apps and middleware only if not running tests
if not IS_RUNNING_TESTS:
    INSTALLED_APPS += [
        'debug_toolbar',
        'django_browser_reload',
    ]

    # Add development-only middleware
    # DebugToolbarMiddleware should be as early as possible in the list, but after encode/decode middlewares
    # BrowserReloadMiddleware should be near the end or beginning
    MIDDLEWARE.insert(2, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    MIDDLEWARE.append('django_browser_reload.middleware.BrowserReloadMiddleware')

    # Required for django-debug-toolbar
    INTERNAL_IPS = [
        '127.0.0.1',
        '::1',
    ]

    # Force toolbar display in local development
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,
        'IS_RUNNING_TESTS': False,
    }


# Email Configuration for testing
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = env("EMAIL_HOST_USER_DEV")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD_DEV")
DEFAULT_FROM_EMAIL = env("EMAIL_HOST_USER_DEV")
