FROM python:3.10-slim

WORKDIR /app

# Upgrade system package index and install basic tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, and wheel to ensure clean package installation
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements file and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure the data directory exists inside the container for SQLite
RUN mkdir -p /app/data

EXPOSE 5000

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]