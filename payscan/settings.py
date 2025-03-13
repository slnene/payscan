"""
Django settings for payscan project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-mnfxx8wt#p8q03e-&h!y6ud=c(r9&5@^$0$$)ez32o*&!js17l'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'twilio',
    'axes',
    'payscan',
    'agents',
    'businesses',
    'users',
    #'django_ratelimit',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend',  # Axes must be first
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [
    'axes.middleware.AxesMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    #'payscan.middleware.RestrictIPMiddleware',
    #'django_ratelimit.middleware.RatelimitMiddleware',
    
]
# settings.py
RATELIMIT_VIEW = 'payscan.middleware.CustomRatelimitMiddleware'

## CACHES = {
   # 'default': {
    #    'BACKEND': 'django_redis.cache.RedisCache',
     #   'LOCATION': 'redis://127.0.0.1:6379/1',
      #  'OPTIONS': {
       #     'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        #}
    #}
#}


ROOT_URLCONF = 'payscan.urls'

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
            ],
            
        },
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

WSGI_APPLICATION = 'payscan.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

#DATABASES = {
 #   'default': {
#'ENGINE': 'django.db.backends.mysql',
#'NAME': 'softlabe_payscandb',
#'USER': 'root',
#'PASSWORD': '',
#'HOST': 'localhost', # Or an IP Address that your DB is hosted on
#'PORT': '3306',}
#}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
   
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
 
    {
        'NAME': 'businesses.validators.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

# settings.py
TIME_ZONE = 'Africa/Johannesburg'
USE_TZ = True
USE_I18N = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'payscan/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'payscan/static')]

LOGIN_REDIRECT_URL='/afterlogin'
LOGIN_URL = 'login'
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Security settings
#SECURE_HSTS_SECONDS = 31536000 # 1 year
#SECURE_SSL_REDIRECT = True
#SESSION_COOKIE_SECURE = True
#CSRF_COOKIE_SECURE = True
#SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#SECRET_KEY = 'randomly_generated_secret_key'
#SECURE_HSTS_PRELOAD = True

# Axes configuration
AXES_FAILURE_LIMIT = 50  # Number of allowed attempts
AXES_COOLOFF_TIME = 1  # Cool-off period in hours
AXES_RESET_ON_SUCCESS = True  # Reset attempts on successful login

SITE_URL = 'http://127.0.0.1:8000/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
print("Base Directory:", BASE_DIR)
print("Static Root:", STATIC_ROOT)
print("Media Root:", MEDIA_ROOT)


# settings.py
from decouple import config

# MTN MoMo API credentials
MTN_MOMO_API_KEY = config('MTN_MOMO_API_KEY', default='0365be4731f24275994ddc69866d0342')
MTN_MOMO_SUBSCRIPTION_KEY = config('MTN_MOMO_SUBSCRIPTION_KEY', default='b9642e7f19d84220b5d0774daf08840b')
MTN_MOMO_USER_ID = config('MTN_MOMO_USER_ID', default='98da44ce-dff8-4eb1-9fad-1fd68c9d4450')
MOMO_API_ENVIRONMENT = config('MOMO_API_ENVIRONMENT', default='sandbox')

# MoMo API settings
MOMOAPI = {
    'collections': {
        'sandbox': {
            'subscription_key': MTN_MOMO_SUBSCRIPTION_KEY,
            'user_id': MTN_MOMO_USER_ID,
            'api_key': MTN_MOMO_API_KEY,
            'environment': MOMO_API_ENVIRONMENT,
            'base_url': 'https://sandbox.momodeveloper.mtn.com/collection'
        },
        'production': {
            'subscription_key': config('PROD_MTN_MOMO_SUBSCRIPTION_KEY', default='your_production_subscription_key'),
            'user_id': config('PROD_MTN_MOMO_USER_ID', default='your_production_user_id'),
            'api_key': config('PROD_MTN_MOMO_API_KEY', default='your_production_api_key'),
            'environment': 'production',
            'base_url': 'https://momodeveloper.mtn.com/collection'
        },
    },
}


import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("payscan/payscaneswatini-firebase-adminsdk-wwqfv-92f0cdae19.json")
firebase_admin.initialize_app(cred)




