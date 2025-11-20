"""
Django settings for mirefugio project.
"""

from pathlib import Path
import os
import environ

# --------------------------------------------------------------------------------------
# Paths & env
# --------------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))  # lee .env si existe

# --------------------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------------------
DEBUG = env.bool("DEBUG", default=False) == "True"
SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-uoer87vu*-unues@)*1l#jcn*wete2kf%pv^t-f8uel#e35^2l",
)

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[
        "127.0.0.1",
        "localhost",
        "mi-refugio-web.onrender.com",
    ],
)

# Para CSRF se requieren esquemas (http/https)
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "https://mi-refugio-web.onrender.com",
    ],
)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
APPEND_SLASH = True

CONTACT_BYPASS_RECAPTCHA = env.bool("CONTACT_BYPASS_RECAPTCHA", default=False)
RECAPTCHA_SITE_KEY = env("RECAPTCHA_SITE_KEY", default="")
RECAPTCHA_SECRET = env("RECAPTCHA_SECRET", default="")
DONATION_MIN_CLP = env.int("DONATION_MIN_CLP", default=500)

# --------------------------------------------------------------------------------------
# Apps
# --------------------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "payments",
]

if DEBUG:
    INSTALLED_APPS.append("sslserver")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # justo después de SecurityMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mirefugio.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.project_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "mirefugio.wsgi.application"

# --------------------------------------------------------------------------------------
# Database (RDS PostgreSQL)
# --------------------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="mirefugio"),
        # Usa SIEMPRE el usuario de app (no el maestro):
        "USER": env("DB_USER", default="mirefugio_owner"),
        "PASSWORD": env("DB_PASS", default="Mirefugio2025!"),
        "HOST": env(
            "DB_HOST",
            default="mirefugio.c9ie2ckqg3rt.us-east-2.rds.amazonaws.com",
        ),
        "PORT": env("DB_PORT", default="5432"),
        "OPTIONS": {
            "sslmode": "require",
            "options": "-c search_path=web,core,public",
        },
        # Mantiene conexiones vivas y saludables
        "CONN_MAX_AGE": env.int("DB_CONN_MAX_AGE", default=60),
        "CONN_HEALTH_CHECKS": True,
    }
}

# --------------------------------------------------------------------------------------
# Passwords
# --------------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------------------------------------------------------------------
# I18N / TZ
# --------------------------------------------------------------------------------------
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------------------
# Static & Media (Whitenoise)
# --------------------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Whitenoise para servir estáticos comprimidos en prod
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media (si luego subes imágenes)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --------------------------------------------------------------------------------------
# Seguridad (activar en prod)
# --------------------------------------------------------------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# --------------------------------------------------------------------------------------
# Logging básico (útil en prod)
# --------------------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO" if not DEBUG else "DEBUG",
    },
}

# --------------------------------------------------------------------------------------
# Transbank (Webpay) - Integration por defecto
# --------------------------------------------------------------------------------------
TBK_API_KEY_ID = env("TBK_API_KEY_ID", default="597055555532")
TBK_API_KEY_SECRET = env(
    "TBK_API_KEY_SECRET",
    default="579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C",
)
TBK_ENV = env("TBK_ENV", default="integration")  # integration | production
TBK_RETURN_URL = env(
    "TBK_RETURN_URL",
    default="https://mi-refugio-web.onrender.com/donar/retorno/",
)

# --------------------------------------------------------------------------------------
# Auth redirects
# --------------------------------------------------------------------------------------
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "login"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
