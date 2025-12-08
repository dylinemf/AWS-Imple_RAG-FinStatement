# Use Python 3.10
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependency system for psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc

# Copy requirements & install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy whole code
COPY . .

# Expose port 8080 (Default App Runner)
EXPOSE 8080

# Running Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]