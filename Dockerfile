FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD gunicorn --bind 0.0.0.0:$PORT render_app:server