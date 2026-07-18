from .base import *

# Ensure debug is true for local environment
DEBUG = True

# Add development-only apps
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

# Console email backend for testing signups in development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
