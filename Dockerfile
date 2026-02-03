# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY get_vk_session.py .
COPY upload_to_yandex_disk.py .
COPY telegram_bot.py .

# Create directory for downloaded albums
RUN mkdir -p vk_downloaded_albums

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the telegram bot
CMD ["python", "telegram_bot.py"]
