FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including build tools for scipy/numpy
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libpq-dev \
    libopenblas-dev \
    liblapack-dev \
    pkg-config \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with verbose output
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/media/videos /app/media/pointclouds

EXPOSE 8004

CMD ["python", "manage.py", "runserver", "0.0.0.0:8004"]
