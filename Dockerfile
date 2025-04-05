FROM python:3.9-slim

WORKDIR /app

# Copy only the render-specific requirements file
COPY requirements-render.txt ./requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all files except those ignored by .dockerignore
COPY . .

# Set environment variable to indicate we're in render mode
ENV DEPLOY_ENV=render

# Run the app
CMD gunicorn --bind 0.0.0.0:$PORT render_app:server