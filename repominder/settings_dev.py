from .settings import *  # noqa

DEBUG = True
SECRET_KEY = 'dev_secret_key'

SCHEME = 'http://'
HOST = '127.0.0.1'
ALLOWED_HOSTS = [HOST]
PORT = 8000

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'repominder_db.sqlite3')
    }
}

SOCIAL_AUTH_GITHUB_KEY = '9d4d7a7b908b1124523a'
SOCIAL_AUTH_GITHUB_SECRET = get_secret('github_oauth_client_secret-dev.txt')

DJMAIL_REAL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

RAVEN_CONFIG.pop('dsn')

# serve static files without nginx in dev
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'assets'),
)
