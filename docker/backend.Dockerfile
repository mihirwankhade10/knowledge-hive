FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
# Install CPU-only torch first (this VM has no GPU). The default PyPI torch
# bundles multi-GB NVIDIA CUDA/cuDNN libraries that are useless here and fill
# the disk. The CPU index ships a much smaller wheel with no nvidia-* deps.
# torch==2.12.0 in requirements.txt is satisfied by 2.12.0+cpu (PEP 440),
# so the later -r install won't pull the CUDA build.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.12.0 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
