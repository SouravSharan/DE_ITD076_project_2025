FROM python:3.8-buster

# Set non-interactive mode for apt
ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y gnupg2 && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 04EE7237B7D453EC && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 648ACFD622F3D138
RUN sed -i 's|http://deb.debian.org/debian|http://ftp.us.debian.org/debian|' /etc/apt/sources.list && \
    apt update


# Install system dependencies
RUN apt update && apt install -y \
    tzdata \
    docker.io \
    ansible \
    curl \
    apt-transport-https \
    ca-certificates \
    gnupg \
    && ln -fs /usr/share/zoneinfo/UTC /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir requests kubernetes

# Set working directory
WORKDIR /workspace

# Copy project files inside the container
COPY workspace/ /workspace/
COPY ansible/ /ansible/

# Set environment for Python in workspace
ENV PATH="/workspace/venv/bin:$PATH"
