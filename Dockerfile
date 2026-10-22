FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Ensure the data directory exists inside the container for SQLite
RUN mkdir -p /app/data

EXPOSE 5000

# Run with Gunicorn (ensure 'gunicorn' is in your requirements.txt)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]