from .base import *  # noqa: F403
import dj_database_url

DEBUG = False
# DEBUG=False — принципиальное отличие от dev.
# При DEBUG=True Django показывает подробные страницы ошибок с кодом и переменными.
# В проде это дыра безопасности — пользователь увидит внутренности твоего приложения.

# PostgreSQL через DATABASE_URL из .env
# Формат строки: postgresql://user:password@host:port/dbname
# conn_max_age=600 — держать соединение с БД открытым 10 минут вместо того
# чтобы открывать новое на каждый запрос. Экономит ресурсы.
DATABASES = {
    'default': dj_database_url.config(
        env='DATABASE_URL',
        conn_max_age=600
    )
}

# MinIO — S3-совместимое хранилище которое мы поднимем в Docker
# django-storages — библиотека которая умеет работать с S3/MinIO
# Все загружаемые пользователем файлы (картинки) будут идти туда
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

AWS_ACCESS_KEY_ID = config('MINIO_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = config('MINIO_SECRET_KEY')
AWS_STORAGE_BUCKET_NAME = config('MINIO_BUCKET_NAME', default='journal-media')
AWS_S3_ENDPOINT_URL = config('MINIO_ENDPOINT_URL')  # http://minio:9000 внутри Docker
AWS_S3_USE_SSL = False  # внутри Docker сети SSL не нужен
AWS_DEFAULT_ACL = 'public-read'  # файлы публично доступны (нам так и нужно)
AWS_QUERYSTRING_AUTH = False  # URL без подписи — просто прямая ссылка на файл
AWS_S3_CUSTOM_DOMAIN = config('MINIO_CUSTOM_DOMAIN')
# AWS_S3_URL_PROTOCOL = 'http:'

# Откуда браузер будет грузить медиафайлы
# Это будет публичный URL через nginx, не прямой MinIO порт
MEDIA_URL = config('MINIO_PUBLIC_URL', default='/media/')

# Email — реальная отправка через Gmail SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

# Дополнительные настройки безопасности для прода
# Эти заголовки браузер будет получать с каждым ответом

# Говорит браузеру: всегда используй HTTPS, не пробуй HTTP
# Включать только когда у тебя реально настроен HTTPS/SSL сертификат!
# Пока закомментировано — раскомментируешь когда подключишь домен и SSL
# SECURE_SSL_REDIRECT = True # nginx уже редиректит на https, если включить, то доступ по ip сломается.
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 3600
