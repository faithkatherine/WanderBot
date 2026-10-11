# Dockerfile for WanderBot AgentCore Agent
FROM public.ecr.aws/docker/library/python:3.14-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY starter.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port for the agent
EXPOSE 8080

# Command to run the agent
CMD ["python", "-m", "uvicorn", "starter:app", "--host", "0.0.0.0", "--port", "8080"]
