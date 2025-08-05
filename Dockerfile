FROM python:3.9-slim

WORKDIR /app

# Install system dependencies required for whisper.cpp and other libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    wget \
    git \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Install huggingface-hub directly
RUN pip install huggingface-hub==0.10.1

# Copy only the requirements file to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Clone the Real-Time-Voice-Cloning repository and install its dependencies
RUN git clone https://github.com/CorentinJ/Real-Time-Voice-Cloning.git voice/Real-Time-Voice-Cloning
RUN pip install --no-cache-dir -r voice/Real-Time-Voice-Cloning/requirements.txt

# Clone the whisper.cpp repository
RUN git clone https://github.com/ggerganov/whisper.cpp.git voice/whisper.cpp

# Set the PYTHONPATH to include the cloned repository
ENV PYTHONPATH="/app/voice/Real-Time-Voice-Cloning:/app"

# Copy the rest of the application code
COPY ./core/app /app/app
COPY ./scripts /app/scripts
COPY ./data /app/data
COPY ./core/app/Makefile /app/Makefile
COPY ./tests /app/tests

# Build whisper.cpp directly using its own Makefile
RUN make -C /app/voice/whisper.cpp

# Download models
RUN make -f /app/Makefile download-models

# Expose the ports the app runs on
EXPOSE 8000 8001

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
