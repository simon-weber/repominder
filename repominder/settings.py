"""
Django settings for repominder project.

Generated by 'django-admin startproject' using Django 1.11.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import datetime
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS_DIR = os.path.join(BASE_DIR, 'secrets')


def get_secret(filename):
    with open(os.path.join(SECRETS_DIR, filename)) as f:
        return f.read().strip()


DEBUG = False
SECRET_KEY = get_secret('secret_key.txt')

SCHEME = 'https://'
HOST = 'www.repominder.com'
ALLOWED_HOSTS = [HOST]
PORT = 8000

try:
    with open(os.path.join(BASE_DIR, 'release.sha')) as f:
        RELEASE = f.read().strip()
except:
    RELEASE = str(datetime.datetime.now())

# Security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'repominder.apps.core',

    'bootstrap3',
    'djmail',
    'raven.contrib.django.raven_compat',
    'social_django',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'repominder.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'repominder.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, '..', 'repominder_db.sqlite3')
    }
}

# Email
EMAIL_BACKEND = 'djmail.backends.async.EmailBackend'
DJMAIL_REAL_BACKEND = 'django_amazon_ses.EmailBackend'
AWS_ACCESS_KEY_ID = get_secret('ses.id')
AWS_SECRET_ACCESS_KEY = get_secret('ses.key')
DEFAULT_FROM_EMAIL = 'Repominder <noreply@repominder.com>'

ADMINS = (('Simon', 'simon@simonmweber.com'),)
SERVER_EMAIL = DEFAULT_FROM_EMAIL


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/assets/'
STATIC_ROOT = os.path.join(BASE_DIR, '..', 'assets')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'simple': {
            'format': '%(levelname)s: %(asctime)s - %(name)s: %(message)s'
        },
        'withfile': {
            'format': '%(levelname)s: %(asctime)s - %(name)s (%(module)s:%(lineno)s): %(message)s'
        },
    },
    'handlers': {
        'console_simple': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'console_verbose': {
            'class': 'logging.StreamHandler',
            'formatter': 'withfile',
        },
        'sentry': {
            'level': 'WARNING',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
    },
    'loggers': {
        '': {
            'level': 'WARNING',
            'handlers': ['sentry'],
        },
        'django': {
            'handlers': ['console_simple'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'WARNING'),
        },
        'django.server': {
            'handlers': ['console_simple'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'github': {
            'handlers': ['console_simple'],
            'level': 'INFO',  # TODO DEBUG has full requests -- get just method/url
        },
        'repominder': {
            'handlers': ['console_verbose'],
            'level': 'INFO',
        },
        'requests.packages.urllib3': {
            'handlers': ['console_simple'],
            'level': 'DEBUG',
        },
    },
}


# python-social-auth
AUTHENTICATION_BACKENDS = (
    'social_core.backends.github.GithubOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
SOCIAL_AUTH_GITHUB_KEY = '26c2b5da7746008ddc28'
SOCIAL_AUTH_GITHUB_SECRET = get_secret('github_oauth_client_secret.txt')
SOCIAL_AUTH_GITHUB_SCOPE = ['user:email']
SOCIAL_AUTH_URL_NAMESPACE = 'social'
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'repominder.apps.core.subscribe_to_list',
    'repominder.apps.core.cache_github_details',
)


# Sentry
RAVEN_CONFIG = {
    'dsn': get_secret('raven.dsn'),
    'release': RELEASE,
}

BOOTSTRAP3 = {
    'horizontal_label_class': 'col-md-3',
    'horizontal_field_class': 'col-md-9',
}

MAILCHIMP_API_KEY = get_secret('mailchimp_api.key')
MAILCHIMP_API_USER = get_secret('mailchimp_api.user')
MAILCHIMP_LIST_ID = 'b3a7b4d47f'
