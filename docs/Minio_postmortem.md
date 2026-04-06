# Postmortem: Отладка интеграции MinIO с Django

## Контекст

Проект: Learning Journal — Django приложение с возможностью загрузки изображений к записям.
Задача: Подключить MinIO как S3-совместимое хранилище для медиафайлов вместо локальной папки.
Окружение: Docker Compose, Django 6.0.2, django-storages 1.14.6, MinIO latest.

---

## Проблема 1: Файлы сохранялись локально вместо MinIO

### Симптом
Картинки загружались без ошибок, запись создавалась успешно, но изображение
не отображалось. В браузере: 404 Not Found на URL вида
`http://localhost/media/entries/2026/04/photo.jpg`.

При проверке внутри контейнера файлы обнаруживались локально:
```
appuser@container:/app/media/entries/2026/04$ ls
photo_2026-03-20_13-32-42.jpg
```

### Диагностика
Проверили какой storage реально используется:
```python
from django.core.files.storage import default_storage
print(type(default_storage))
# <class 'django.core.files.storage.DefaultStorage'>
print(default_storage.__dict__)
# {'_wrapped': <object object at 0x...>}  ← пустой объект!
```

`_wrapped` был пустым объектом — это означало что Django не инициализировал
кастомный storage бэкенд.

### Причина
В Django 4.2+ настройка `DEFAULT_FILE_STORAGE` устарела (deprecated).
Старый синтаксис:
```python
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'  # не работает
```

Новый синтаксис через `STORAGES`:
```python
STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}
```

### Решение
Заменили `DEFAULT_FILE_STORAGE` на новый синтаксис `STORAGES` в `prod.py`.
Заодно перенесли туда настройку `staticfiles` из `base.py` — теперь оба
хранилища описаны в одном месте.

---

## Проблема 2: Файлы шли в MinIO но браузер не мог их открыть

### Симптом
После исправления проблемы 1 файлы перестали сохраняться локально,
но картинки всё равно не отображались. В DevTools был виден запрос на:
```
http://minio:9000/journal-media/entries/2026/04/filename.png
net::ERR_NAME_NOT_RESOLVED
```

### Причина
`minio:9000` — это внутреннее имя сервиса в Docker сети. Браузер на машине
пользователя ничего не знает про Docker сеть и не может разрешить имя `minio`.

django-storages использует `AWS_S3_ENDPOINT_URL` для двух целей одновременно:
1. Для загрузки файлов (Django → MinIO, внутри Docker — правильно)
2. Для генерации публичных URL (браузер → MinIO, снаружи — неправильно)

### Решение
Указали отдельный публичный адрес через `AWS_S3_CUSTOM_DOMAIN`:
```python
AWS_S3_CUSTOM_DOMAIN = config('MINIO_CUSTOM_DOMAIN')
# Значение: your-server-ip/media
```

Теперь:
- `AWS_S3_ENDPOINT_URL = http://minio:9000` — Django использует для загрузки файлов
- `AWS_S3_CUSTOM_DOMAIN = your-ip/media` — браузер использует для отображения

---

## Проблема 3: Публичный URL генерировался с https вместо http

### Симптом
После добавления `AWS_S3_CUSTOM_DOMAIN` URL стал:
```
https://localhost/media/entries/2026/04/filename.png
net::ERR_CONNECTION_REFUSED
```

### Причина
`AWS_S3_CUSTOM_DOMAIN` по умолчанию генерирует URL с протоколом `https://`.
У нас SSL не настроен, сервер работает на http.

### Решение
Явно указали протокол:
```python
AWS_S3_URL_PROTOCOL = 'http:'
```

---

## Проблема 4: collectstatic падал из-за отсутствующих файлов

### Симптом
При переходе на новый синтаксис `STORAGES` контейнер `web` падал при старте:
```
whitenoise.storage.MissingFileError: The file 'journal/css/bootstrap.min.css.map'
could not be found
```

### Причина
`CompressedManifestStaticFilesStorage` (который мы изначально использовали)
проверяет все ссылки внутри CSS файлов. `bootstrap.min.css` ссылается на
`.map` файлы и шрифты которых не было в папке со статикой.

`.map` файлы — это source maps для отладки в DevTools. На продакшене они
не нужны, но whitenoise падал не найдя их.

### Решение
Заменили `CompressedManifestStaticFilesStorage` на `CompressedStaticFilesStorage`
в `STORAGES`. Разница:
- `CompressedManifestStaticFilesStorage` — сжимает + проверяет все ссылки в CSS
- `CompressedStaticFilesStorage` — только сжимает, ссылки не проверяет

---

## Итоговая схема работы после всех исправлений

```
Загрузка файла пользователем:
  Браузер → POST /entry/create/ → Nginx → Django (gunicorn)
  Django → boto3 → MinIO (http://minio:9000) → файл сохранён в бакете
  В БД записан путь: entries/2026/04/uuid.jpg

Отображение файла:
  Django рендерит HTML → URL = http://your-ip/media/entries/2026/04/uuid.jpg
  Браузер → GET /media/entries/... → Nginx → проксирует в MinIO (http://minio:9000)
  MinIO отдаёт файл → Nginx → Браузер
```

---

## Ключевые выводы

**1. DEFAULT_FILE_STORAGE устарел в Django 4.2+**
Всегда используй новый синтаксис `STORAGES`. Старый работает частично
но ненадёжно — не бросает ошибок, молча игнорируется.

**2. Endpoint и публичный URL — разные вещи**
В S3-совместимых хранилищах всегда два адреса:
- Внутренний (для сервера) — `AWS_S3_ENDPOINT_URL`
- Публичный (для браузера) — `AWS_S3_CUSTOM_DOMAIN`

**3. Диагностика storage**
Быстрый способ проверить что реально используется:
```python
from django.core.files.storage import default_storage
print(type(default_storage._wrapped))
```
Если видишь `<object>` вместо имени класса — storage не инициализирован.

**4. Прямая проверка через boto3**
Если django-storages ведёт себя странно — проверь boto3 напрямую:
```python
import boto3
s3 = boto3.client('s3', endpoint_url='...', ...)
s3.put_object(Bucket='bucket', Key='test.txt', Body=b'hello')
```
Это помогает разделить проблему: MinIO работает или Django неправильно настроен.