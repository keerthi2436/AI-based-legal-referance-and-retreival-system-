# Use a slim Python image for lower size
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies if required (e.g., for sentence-transformers and standard compilation)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies (use --no-cache-dir to reduce image size)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app
COPY . .

# Expose port (Streamlit defaults to 8501, or Render/Railway set PORT)
EXPOSE 8501

# Start the Streamlit app on the mandated port (usually $PORT if set by PaaS, else 8501)
CMD streamlit run app.py --server.port="${PORT:-8501}" --server.address="0.0.0.0"
