# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install netcat for wait-for-db.sh
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*



# Set the working directory
WORKDIR /app

# Copy the requirements file from the app directory
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose port 8000 for FastAPI
EXPOSE 8000

# Default command (overridden by docker-compose)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
