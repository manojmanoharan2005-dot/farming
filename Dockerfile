FROM python:3.11-slim

# Prevent Python writing pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=""

WORKDIR /app

# Install system deps needed to build some packages (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application source
COPY . /app

# Expose port used by Vercel runtime
ENV PORT 8080

# Use gunicorn to serve the WSGI app. Ensure your Flask app exposes `app` in wsgi.py
# If your entrypoint file is different (e.g. app.py), change "wsgi:app" to "app:app" or similar.
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:${PORT}", "wsgi:app"]
