# Use Python 3.12 on Alpine as base image
FROM python:3.12-alpine

# Set working directory
WORKDIR /app

# Install necessary dependencies for Chrome and ChromeDriver
RUN apk update && \
    apk add --no-cache \
    wget \
    bash \
    curl \
    chromium \
    chromium-chromedriver \
    libstdc++ \
    udev \
    ttf-freefont \
    mesa-gl \
    dbus

# Set environment variables for Chrome in headless mode
ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROME_PATH=/usr/lib/chromium/
ENV RENEWAL_SERVICE_URL=https://secure.tncountyclerk.com//index.php

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Expose the FastAPI port
EXPOSE 80

# Start FastAPI with Uvicorn
CMD ["uvicorn", "Main:app", "--host", "0.0.0.0", "--port", "80"]
