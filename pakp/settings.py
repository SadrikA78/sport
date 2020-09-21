from django.contrib.messages import constants as messages
import os


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'classroom.apps.ClassroomConfig',
    'ckeditor',
    'ckeditor_uploader',
    'classroom.templatetags.custom_tags',
    'crispy_forms',
    'sorl.thumbnail',
    'star_ratings',
    'qr_code',
    'pakp',
    'jet',
    'jet.dashboard',
]

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'width': 1110,
        'toolbar_Custom': [
            ['Font', 'FontSize', 'TextColor', 'BGColor'],
            ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript'],
            ['Undo', 'Redo', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink', 'Image', 'Table', 'HorizontalRule', 'NumberedList',
             'BulletedList', '-', 'Outdent', 'Indent', 'Blockquote',
             'BidiLtr', 'BidiRtl'],
            ['RemoveFormat', 'Smiley', 'SpecialChar'],
            ['Styles', 'Format'],
            ['Youtube'],
            ['Source']
        ],
        'extraPlugins': 'youtube',
    },
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pakp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
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

WSGI_APPLICATION = 'pakp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '',
        'USER' : '',
        'PASSWORD' : '',
        'HOST' : '',
        'PORT' : '',
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    }
]

# Custom Django auth settings

AUTH_USER_MODEL = 'room.User'

LOGIN_URL = 'login'

LOGOUT_URL = 'logout'

LOGIN_REDIRECT_URL = 'home'

LOGOUT_REDIRECT_URL = 'home'

# Messages built-in framework

MESSAGE_TAGS = {
    messages.DEBUG: 'alert-secondary',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Asia/Manila'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
# STATIC_ROOT = 'static/'  # for production

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Third party apps configuration

CRISPY_TEMPLATE_PACK = 'bootstrap4'

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 587

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

TEMPLATE_CONTEXT_PROCESSOR = 'django.core.context_processors.request'
STAR_RATINGS_STAR_HEIGHT = 20

CKEDITOR_UPLOAD_PATH = 'uploads/'
