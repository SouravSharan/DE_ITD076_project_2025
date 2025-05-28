# Use Python 3.9 slim base image
FROM python:3.9-slim

# Set environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    PATH="/venv/bin:$PATH" \
    VIRTUAL_ENV=/venv

# Install system dependencies + Docker CLI (without daemon)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk \
    wget \
    curl \
    git \
    ca-certificates \
    && curl -fsSL https://get.docker.com | sh \
    && rm -rf /var/lib/apt/lists/*

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/

# Create and activate virtual environment
RUN python -m venv /venv

# Upgrade pip and install Python packages
RUN /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install \
    numpy \
    pandas \
    requests \
    kubernetes \
    docker \
    ansible

# Set working directory
WORKDIR /workspace

# Copy project files
COPY workspace/ /workspace/
COPY ansible/ /ansible/

# Set default command
CMD ["/bin/bash"]