FROM cdrx/pyinstaller-windows:latest

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements и устанавливаем Flask, gunicorn
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения
COPY . .

# Открываем порт, который ожидает Render (обычно 8080)
EXPOSE 8080

# Запускаем приложение через gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
