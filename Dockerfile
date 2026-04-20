FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY data/ ./data/

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_PATH=/app/data/nutrition.db

# Initialize database
RUN python -c "from src.database.duckdb_utils import init_database; init_database()"

# Default command
CMD ["python", "-m", "src.main", "--interactive"]
