FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y build-essential python3-pip libglib2.0-0 libsm6 libxext6 libxrender-dev git && \
    apt-get clean

# Set workdir
WORKDIR /workspace

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code into the image
COPY . .

# Set environment variable for output encoding
ENV PYTHONIOENCODING UTF-8

# Entrypoint for CLI-based running (can override)
ENTRYPOINT ["python", "main.py"]
