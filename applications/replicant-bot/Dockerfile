# Use the official Python image from the Docker Hub
FROM python:3.13.2-slim

# Install system packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    sox \
    flac \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.md .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.md

# Copy the rest of the application code into the container
COPY . .

# Set environment variable to prevent Python from buffering the output
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "main.py"]
