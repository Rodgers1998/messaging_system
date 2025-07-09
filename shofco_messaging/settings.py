from pathlib import Path
import os
from dotenv import load_dotenv


# === Base Directory ===
BASE_DIR = Path(__file__).resolve().parent.parent

# === Load Environment Variables ===
load_dotenv(BASE_DIR / '.env')

# === Security ===
SECRET_KEY = 'django-insecure-fwm7x*zvuy#5xp+b^h5ld+xr)6qwl2n6dy6=pt#q!h$*+f3k3q'
DEBUG = True  # Set to False in production!
ALLOWED_HOSTS = ['messaging-system-bzfq.onrender.com','localhost', '127.0.0.1']

# === Installed Applications ===
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Your apps
    'core',
    'beneficiaries',
    'messaging',
    'surveys',
    'campaigns',
    'ivr',
    'dashboard',

    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap5',
    'import_export',
]

# === Middleware ===
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For serving static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# === URL Configuration ===
ROOT_URLCONF = 'shofco_messaging.urls'

# === Templates ===
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

# === WSGI Application ===
WSGI_APPLICATION = 'shofco_messaging.wsgi.application'

# === Database ===
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# import dj_database_url
# import os

# DATABASES = {
#     'default': dj_database_url.config(default=os.getenv("DATABASE_URL"))
# }


# === Password Validation ===
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# === Internationalization ===
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# === Static Files (CSS, JavaScript, Images) ===
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# === Default Primary Key Field Type ===
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# === Crispy Forms ===
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

LOGIN_URL = 'messaging:login'

LOGIN_REDIRECT_URL = 'messaging:dashboard_home'  # or wherever users go after login
LOGOUT_REDIRECT_URL = 'messaging:login' 
