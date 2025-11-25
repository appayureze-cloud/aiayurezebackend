# HF Spaces with T4 GPU - Fixed for GPU support
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc g++ git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements WITHOUT torch (we'll install it separately)
COPY requirements_gpu_fixed.txt requirements.txt

# Install GPU PyTorch FIRST from CUDA index
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install other packages
RUN pip install --no-cache-dir -r requirements.txt

COPY main_enhanced.py .
COPY app ./app

# Create empty static directory (optional for FCM testing)
# If you need FCM test page, copy your static folder to hf_space_deploy/static before building
RUN mkdir -p /app/cache /app/models /app/static

ENV HF_HOME=/app/cache
ENV PORT=7860
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

EXPOSE 7860

CMD ["uvicorn", "main_enhanced:app", "--host", "0.0.0.0", "--port", "7860"]
