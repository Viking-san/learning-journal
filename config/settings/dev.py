from .base import *  # noqa: F403
# "from .base import *" — импортируем ВСЁ из base.py
# noqa: F403 — подавляет предупреждение линтера про "import *", здесь это намеренно

DEBUG = True

# SQLite — удобно локально, не нужно поднимать Postgres
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Медиафайлы хранятся локально на машине разработчика
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Письма выводятся прямо в консоль — не нужно настраивать реальный SMTP
# Запустил сервер, зарегистрировался — письмо появилось в терминале
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# debug-toolbar — показывает SQL запросы, время ответа, использованные шаблоны
# Очень полезно при разработке, в проде категорически не нужно
INSTALLED_APPS += ['debug_toolbar']  # noqa: F405
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']  # noqa: F405
INTERNAL_IPS = ['127.0.0.1']
