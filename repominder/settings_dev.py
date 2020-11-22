from .settings import *  # noqa

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

GH_APP_ID = 6687
GH_APP_PEM = get_secret("ghapp_privkey-dev.pem")

SOCIAL_AUTH_REDIRECT_IS_HTTPS = False
SOCIAL_AUTH_GITHUB_APP_KEY = "Iv1.8673e1a33dca52e9"
SOCIAL_AUTH_GITHUB_APP_SECRET = get_secret("ghapp_client_secret-dev.txt")

DJMAIL_REAL_BACKEND = "django.core.mail.backends.console.EmailBackend"

RAVEN_CONFIG.pop("dsn")

# serve static files without nginx in dev
STATICFILES_DIRS = (os.path.join(BASE_DIR, "assets"),)
