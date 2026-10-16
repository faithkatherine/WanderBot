# Use official Python base image
FROM public.ecr.aws/docker/library/python:3.14-slim

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY starter.py .
COPY datasets/ ./datasets/

# Environment variables
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Run the agent
CMD ["python", "starter.py"]
