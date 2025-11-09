# -------------------------------
# Green AI Backend Container
# -------------------------------
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy all project files into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for data and results
RUN mkdir -p /app/data_clean /app/experiment_results /app/models

# Expose Flask/Backend port
EXPOSE 5000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MODEL_PATH=/app/models
ENV DATA_PATH=/app/data_clean

# Default command
CMD ["python", "run_experiments.py"]
