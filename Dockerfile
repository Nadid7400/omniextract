FROM python:3.11-slim

# Install system dependencies (ffmpeg helps yt-dlp extract & merge video streams)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Default port
ENV PORT=8000

EXPOSE 8000

# Launch server dynamically binding to platform's assigned PORT
CMD ["sh", "-c", "uvicorn backend.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
