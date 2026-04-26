FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app

# System dependencies (important for opencv, etc.)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run your script
CMD ["python", "integrated_security.py"]