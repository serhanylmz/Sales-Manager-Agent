FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Keep the existing SQLite database path
RUN mkdir -p /app/data
ENV DATABASE_URL=sqlite:///./data/app.db

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PYTHONDEVMODE=1

# Use python -u to force unbuffered output
CMD ["python", "-u", "main.py"] 