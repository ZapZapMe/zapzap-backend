# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the application code to the containerCOPY requirements.txt .
COPY backend/* .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port on which the application will run (change as per your app's needs)
EXPOSE 2121

# Set the command to run the application when the container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "2121"]
