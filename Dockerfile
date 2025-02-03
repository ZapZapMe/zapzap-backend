# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set environment variables
# PYTHONDONTWRITEBYTECODE Purpose: Prevents Python from writing .pyc files (compiled bytecode) to disk.
# PYTHONUNBUFFERED        Purpose: Prevents Python from buffering stdout and stderr (it just writes them directly).
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install the Python dependencies
COPY backend/requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code to the container
COPY backend/app/ /app/

# Expose the port on which the application will run (change as per your app's needs)
EXPOSE 8080

# Set the command to run the application when the container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1" ]
