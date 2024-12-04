# Use AWS Lambda Python runtime as base image
FROM python:3.12-slim

# Create a non-root user and group
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY main.py .

# Create the /var/task directory
RUN mkdir -p /var/task

# Change ownership of the application files to the non-root user
RUN chown -R appuser:appuser /var/task

# Switch to non-root user
USER appuser

# Set the CMD to your handler
CMD [ "main.lambda_handler" ]