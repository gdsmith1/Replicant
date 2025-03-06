FROM python:3.10

# Install necessary system dependencies
RUN apt update && apt install -y \
    libsndfile1 \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    gfortran

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel

# Install PyTorch (CPU version) and TTS with specific versions
RUN pip install torch==2.0.0 torchaudio==2.0.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip install TTS==0.10.0 numpy==1.22.4 scipy==1.8.0

# Copy the main.py script
COPY main.py .

# Set the entrypoint to run the main.py script
ENTRYPOINT ["python", "main.py"]