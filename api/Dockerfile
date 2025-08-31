FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy model files from parent directory
COPY ../data/training/spam_detection_model.pkl data/training/
COPY ../data/training/tfidf_vectorizer.pkl data/training/

# Copy necessary bot utilities
COPY ../groupme_bot/utils/ groupme_bot/utils/
COPY ../groupme_bot/__init__.py groupme_bot/

# Create necessary __init__.py files
RUN touch groupme_bot/__init__.py groupme_bot/utils/__init__.py

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "wsgi:app"]
