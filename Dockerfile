FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies including Xvfb and Playwright dependencies
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    xvfb \
    xauth \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxi6 \
    libxext6 \
    libxrender1 \
    libxrandr2 \
    libxtst6 \
    libgl1-mesa-glx \
    libgbm1 \
    libnss3 \
    libnspr4 \
    libxss1 \
    libpango-1.0-0 \
    libcairo2 \
    gcc g++ make python3-dev \
    wget curl \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && playwright install --with-deps chromium

# Copy application files
COPY . .

# Set up dummy server port
ENV PORT=10000
EXPOSE 10000

# Configure entrypoint
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh
ENTRYPOINT ["/app/start.sh"]