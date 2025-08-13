FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# Install Python and FFmpeg
RUN apt-get update && apt-get install -y python3.11 python3-pip ffmpeg git git-lfs && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download the whisper model
# Using a smaller model for faster setup. 
# In a production scenario, you might use a larger model and build it into the image.
RUN git lfs install && \
    git clone https://huggingface.co/guillaumekln/faster-whisper-base /app/faster-whisper-base

COPY main.py .

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]

