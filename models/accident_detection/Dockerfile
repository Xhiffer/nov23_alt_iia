

# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI app code
COPY . .

# Expose the port FastAPI will run on
EXPOSE 83


#erf flemme de lancé direct
# CMD ["python3", "accident_detection.py"]



# Start FastAPI using uvicorn
# CMD ["uvicorn", "accident_detection:app", "--host", "0.0.0.0", "--port", "83"]
