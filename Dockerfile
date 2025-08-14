FROM python:3.11-slim

# Install ffmpeg (we'll need it later for transcription)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Run with Gunicorn in production
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
