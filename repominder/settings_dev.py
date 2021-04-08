import sentry_sdk

from .settings import *  # noqa
from .settings import BASE_DIR, os

DEBUG = True
SECRET_KEY = "dev_secret_key"

SCHEME = "http://"
HOST = "samus.simon.codes"
ALLOWED_HOSTS = ["*"]
PORT = 8000
USE_X_FORWARDED_HOST = False
SECURE_PROXY_SSL_HEADER = None

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "repominder_db.sqlite3"),
    }
}

GH_APP_NAME = "repominder-dev"
GH_APP_ID = 6687
GH_APP_PEM = os.environ["GHAPP_PRIVKEY_DEV"]
GH_APP_WEBHOOK_SECRET = os.environ["GHAPP_WEBHOOK_SECRET_DEV"]

SOCIAL_AUTH_REDIRECT_IS_HTTPS = False
SOCIAL_AUTH_GITHUB_APP_KEY = "Iv1.8673e1a33dca52e9"
SOCIAL_AUTH_GITHUB_APP_SECRET = os.environ["GHAPP_CLIENT_SECRET_DEV"]

DJMAIL_REAL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# serve static files without nginx in dev
STATICFILES_DIRS = (os.path.join(BASE_DIR, "assets"),)

sentry_sdk.init(dsn="")
