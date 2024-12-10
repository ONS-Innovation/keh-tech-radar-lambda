# Use an official Python image as a base image
FROM python:3.12-slim

# Create a non-root user
RUN useradd -m appuser

# Set the working directory
WORKDIR /app

# Install system dependencies for Python and pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt /app/

# Install dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . /app

# Adjust permissions and ownership
RUN chmod +x main.py
RUN chown -R appuser:appuser /app

# Use non-root user
USER appuser

# Set the entry point to execute the script using Python
ENTRYPOINT ["python", "main.py"]
