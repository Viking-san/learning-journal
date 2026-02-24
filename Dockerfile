# Базовый образ — Python 3.12 на лёгком Linux
FROM python:3.12-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
# (делаем ДО копирования кода — чтобы Docker кэшировал этот слой)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта
COPY . .

# Аргумент сборки — нужен только для collectstatic
ARG SECRET_KEY=dummy-secret-key-for-build
ENV SECRET_KEY=$SECRET_KEY

# Собираем статику
RUN python manage.py collectstatic --noinput

# Открываем порт 8000
EXPOSE 8000

# Запуск через gunicorn (не runserver — он не для продакшена)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]