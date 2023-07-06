FROM python:3.7-slim

WORKDIR /app

COPY . /app

RUN pip3 install -r requirements.txt --no-cache-dir

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000" ]