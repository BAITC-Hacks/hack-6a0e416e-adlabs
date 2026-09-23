FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend /app
COPY datasets /datasets
CMD ["sh","-c","python manage.py migrate --noinput && python manage.py import_career_dataset --path /datasets/career_quest && python manage.py runserver 0.0.0.0:8000"]
