FROM python:3.10-slim

# Install system dependencies for Tesseract OCR and FFmpeg
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirement files first (to leverage Docker build caching)
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything else into the container
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
