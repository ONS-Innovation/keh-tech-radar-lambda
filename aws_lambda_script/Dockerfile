FROM python:3.12-slim

# Create a non-root user and group
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY main.py .

# Change ownership of the application files to the non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set the CMD to your handler (module_name.function_name)
CMD [ "python", "-c", "import main; main.lambda_handler(None, None)" ]