from .settings import *  # noqa
from .settings import RELEASE, os

ALLOWED_HOSTS = [os.environ["SITE"]]

SECRET_KEY = os.environ["SECRET_KEY"]
AWS_ACCESS_KEY_ID = os.environ["SES_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["SES_KEY"]
GH_APP_PEM = os.environ["GHAPP_PRIVKEY"]
GH_APP_WEBHOOK_SECRET = os.environ["GHAPP_WEBHOOK_SECRET"]
SOCIAL_AUTH_GITHUB_APP_SECRET = os.environ["GHAPP_CLIENT_SECRET"]

RAVEN_CONFIG = {
    "dsn": os.environ["RAVEN_DSN"],
    "release": RELEASE,
}
