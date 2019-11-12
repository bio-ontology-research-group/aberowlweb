"""
Django settings for aberowlweb project.

Generated by 'django-admin startproject' using Django 1.11.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import sys
from configurations import Configuration
from kombu import Queue, Exchange
from django.contrib import messages

import os, shutil, configparser

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def rel(*x):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)


sys.path.insert(0, rel('apps'))

# Reading setup properties from configuration file
config_dir = os.path.expanduser("~") + "/.config"
configFile = config_dir + "/aberowl.ini"

if not os.path.isfile(configFile):
    os.makedirs(config_dir, exist_ok=True)
    shutil.copyfile("default_aberowl.ini", configFile)

config = configparser.RawConfigParser()
config.read(configFile)

class BaseConfiguration(Configuration):
    # Quick-start development settings - unsuitable for production
    # See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

    global config

    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = 'm^a2@&q12j-t1$*sf+@5#mqbd3b6inp)w)y&)sgalm0g*)^)&q'

    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = True

    ALLOWED_HOSTS = ['*']

    ADMINS = [
        ('Maxat Kulmanov', 'coolmaksat@gmail.com'),
    ]

    # Application definition

    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django.contrib.sites',
        'accounts',
        'allauth',
        'allauth.account',
        'allauth.socialaccount',
        'rest_framework',
        'rest_framework_swagger',
        'widget_tweaks',
        'aberowl',
        'snowpenguin.django.recaptcha2',
        'corsheaders',
    ]

    REST_FRAMEWORK = {
        'DEFAULT_RENDERER_CLASSES': [
            'rest_framework.renderers.JSONRenderer',
            'rest_framework.renderers.BrowsableAPIRenderer',
        ]
    }

    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]

    ROOT_URLCONF = 'aberowlweb.urls'

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [rel('templates'),],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ]

    AUTHENTICATION_BACKENDS = [
        # Needed to login by username in Django admin, regardless of `allauth`
        'django.contrib.auth.backends.ModelBackend',
        # `allauth` specific authentication methods, such as login by e-mail
        'allauth.account.auth_backends.AuthenticationBackend',
    ]

    WSGI_APPLICATION = 'aberowlweb.wsgi.application'


    # Database
    # https://docs.djangoproject.com/en/1.11/ref/settings/#databases

    DATABASES = {
        'default': {
            'ENGINE': config['database']['DATABASE_ENGINE'],
            'NAME': config['database']['DATABASE_NAME'],
            'HOST': config['database']['DATABASE_HOST'],
            'USER': config['database']['DATABASE_USER'],
            'PASSWORD': config['database']['DATABASE_PASSWORD'],
        }
    }

    # Memcached
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
        }
    }

    SESSION_ENGINE = "django.contrib.sessions.backends.cache"

    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.CachedStaticFilesStorage'
    
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

    STATIC_URL = '/static/'
    STATIC_ROOT = 'public/'
    MEDIA_ROOT = 'media/'
    MEDIA_URL = '/media/'

    # User profile module
    AUTH_PROFILE_MODULE = 'accounts.models.UserProfile'
    ACCOUNT_EMAIL_REQUIRED = True
    ACCOUNT_AUTHENTICATION_METHOD = "username_email"
    ACCOUNT_EMAIL_VERIFICATION = "none"
    ACCOUNT_PRESERVE_USERNAME_CASING = "False"

    STATICFILES_DIRS = (
        rel('static'),)

    SITE_ID = 1
    SITE_DOMAIN = 'localhost:8000'
    SERVER_EMAIL = 'info@aber-owl.net'
    
    # Celery configuration
    RABBIT_HOST = 'localhost'
    RABBIT_PORT = 5672

    CELERY_BROKER_URL = 'pyamqp://{user}:{pwd}@{host}:{port}//'.format(
        user=os.environ.get('RABBIT_USER', config['celery']['CELERY_BROKER_USER']),
        pwd=os.environ.get('RABBIT_PASSWORD', config['celery']['CELERY_BROKER_PASSWORD']),
        host=RABBIT_HOST,
        port=RABBIT_PORT)

    CELERY_RESULT_BACKEND = 'rpc://'
    CELERY_WORKER_CONCURRENCY = 24
    CELERY_BROKER_POOL_LIMIT = 100
    CELERY_BROKER_CONNECTION_TIMEOUT = 10

    # configure queues, currently we have only one
    CELERY_DEFAULT_QUEUE = 'default'
    CELERY_QUEUES = (
        Queue('default', Exchange('default'), routing_key='default'),
    )

    # Sensible settings for celery
    CELERY_ALWAYS_EAGER = False
    CELERY_ACKS_LATE = True
    CELERY_TASK_PUBLISH_RETRY = True
    CELERY_DISABLE_RATE_LIMITS = False

    # By default we will ignore result
    # If you want to see results and try out tasks interactively, change it to False
    # Or change this setting on tasks level
    CELERY_IGNORE_RESULT = True
    CELERY_SEND_TASK_ERROR_EMAILS = False
    CELERY_TASK_RESULT_EXPIRES = 600

    # AberOWL setttings
    ABEROWL_API_URL = 'http://localhost:8080/api/'
    ABEROWL_SERVER_URL = 'http://localhost/'
    
    ABEROWL_API_WORKERS = [
        'http://localhost:8080/api/']
    
    FILE_UPLOAD_HANDLERS = [
        # 'django.core.files.uploadhandler.MemoryFileUploadHandler',
        'django.core.files.uploadhandler.TemporaryFileUploadHandler',
    ]

    RECAPTCHA_PRIVATE_KEY = '6LefajoUAAAAAEiswDUvk1quNKpTJCg49gwrLXpb'
    RECAPTCHA_PUBLIC_KEY = '6LefajoUAAAAAOAWkZnaz-M2lgJOIR9OF5sylXmm'
    # ACCOUNT_SIGNUP_FORM_CLASS = 'accounts.forms.SignupForm'
    ACCOUNT_FORMS = {
        'login': 'accounts.forms.CaptchaLoginForm',
        'signup': 'accounts.forms.CaptchaSignupForm'}

    MESSAGE_TAGS = {
        messages.INFO: 'list-group-item-info',
        messages.DEBUG: 'list-group-item-info',
        messages.SUCCESS: 'list-group-item-success',
        messages.WARNING: 'list-group-item-warning',
        messages.ERROR: 'list-group-item-danger',
    }

    CORS_ORIGIN_ALLOW_ALL = True
    CORS_URLS_REGEX = r'^/api/.*$'

    ELASTIC_SEARCH_URL=config['elasticsearch']['ELASTIC_SEARCH_URL']
    ELASTIC_SEARCH_USERNAME=config['elasticsearch']['ELASTIC_SEARCH_USERNAME']
    ELASTIC_SEARCH_PASSWORD=config['elasticsearch']['ELASTIC_SEARCH_PASSWORD']
    ELASTIC_ONTOLOGY_INDEX_NAME = config['elasticsearch']['ELASTIC_ONTOLOGY_INDEX_NAME']
    ELASTIC_CLASS_INDEX_NAME = config['elasticsearch']['ELASTIC_CLASS_INDEX_NAME']


class Development(BaseConfiguration):
    pass


class Production(BaseConfiguration):

    DEBUG = False
    SITE_DOMAIN = 'aber-owl.net'
    ABEROWL_API_URL = 'http://10.254.145.41/api/'
    ABEROWL_API_WORKERS = [
        'http://10.254.145.27:8080/api/',
        'http://10.254.145.30:8080/api/']
    ABEROWL_SERVER_URL = 'http://10.254.145.9/'
    SESSION_COOKIE_SECURE=True
    SESSION_COOKIE_HTTPONLY=True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')


class ProductionCelery(BaseConfiguration):

    DEBUG = False
    SITE_DOMAIN = 'aber-owl.net'
    ABEROWL_API_URL = 'http://10.254.145.41/api/'
    ABEROWL_API_WORKERS = [
        'http://10.254.145.27:8080/api/',
        'http://10.254.145.30:8080/api/']
    ABEROWL_SERVER_URL = 'http://10.254.145.9/'


class TestConfiguration(BaseConfiguration):

    DATABASES = {
        'default': {
            'ENGINE': config['database']['DATABASE_ENGINE'],
            'HOST': config['database']['DATABASE_HOST'],
            'USER': config['database']['DATABASE_USER'],
            'PASSWORD': config['database']['DATABASE_PASSWORD'],
        }
    }

    