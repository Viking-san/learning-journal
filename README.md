# Learning Journal

Веб-приложение для ведения дневника обучения с поддержкой Markdown, тегов и REST API.

## Возможности

- Создание, редактирование и удаление записей
- Организация по категориям и тегам
- Markdown редактор с подсветкой синтаксиса
- Загрузка изображений к записям
- Фильтрация по категориям и тегам
- Статистика с графиком активности
- REST API для интеграции с другими приложениями

## Технологии

**Backend:**
- Python 3.12
- Django 6.0
- Django REST Framework
- PostgreSQL (опционально, по умолчанию SQLite)

**Frontend:**
- Bootstrap 5 (тёмная тема)
- EasyMDE (Markdown редактор)
- Chart.js (графики)
- Highlight.js (подсветка кода)

## Установка и запуск

### Требования
- Python 3.11+
- pip
- virtualenv

### Шаги установки

1. Клонировать репозиторий
```bash
git clone https://github.com/Viking-san/learning-journal.git
cd learning-journal
```

2. Создать виртуальное окружение
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate на Windows
```

3. Установить зависимости
```bash
pip install -r requirements.txt
```

4. Применить миграции
```bash
python manage.py migrate
```

5. Создать суперпользователя (для админки)
```bash
python manage.py createsuperuser
```

6. Запустить сервер
```bash
python manage.py runserver
```

Приложение доступно по адресу: http://127.0.0.1:8000/
Админка для создания категорий и тегов http://127.0.0.1:8000/admin/

## API Endpoints

### Записи
- `GET /api/entries/` - список всех записей
- `GET /api/entries/{id}/` - детали записи
- `POST /api/entries/` - создать запись
- `PUT /api/entries/{id}/` - обновить запись
- `DELETE /api/entries/{id}/` - удалить запись

### Фильтрация и поиск
- `/api/entries/?category=1` - фильтр по категории
- `/api/entries/?tags=2` - фильтр по тегу
- `/api/entries/?search=django` - поиск по тексту
- `/api/entries/?ordering=-created_at` - сортировка

### Категории и теги
- `GET /api/categories/` - список категорий
- `GET /api/tags/` - список тегов

**Интерактивная документация:** http://127.0.0.1:8000/api/

## О проекте

Проект создан в рамках изучения Backend разработки и Django.

## Лицензия

MIT
