# Используем официальный и легковесный базовый образ Python
FROM python:3.12-slim

# Настраиваем переменные окружения, чтобы Python не буферизировал логи (важно для ELK)
ENV PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем список зависимостей
COPY requirements.txt .

# Обновляем pip и устанавливаем библиотеки без сохранения кэша (уменьшает размер образа)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем структуру проекта внутрь контейнера
COPY app/ ./app/
COPY models/ ./models/

# Указываем сетевой порт, который будет слушать контейнер
EXPOSE 5000

# Инструкция для запуска Flask-приложения при старте контейнера
CMD ["python", "app/api.py"]