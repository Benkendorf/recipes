FROM python:3.9
WORKDIR /app
RUN pip install gunicorn==20.1.0
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .

CMD python manage.py makemigrations --noinput && \
    python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput --clear && \
    cp -r /app/collected_static/. /backend_static/static/ && \
    gunicorn --bind 0.0.0.0:8000 foodgram_backend.wsgi