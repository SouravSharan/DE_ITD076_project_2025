FROM ubuntu:latest

# Install tzdata first
RUN apt update && apt install -y tzdata

# Set timezone to prevent manual prompts
RUN ln -fs /usr/share/zoneinfo/UTC /etc/localtime && dpkg-reconfigure -f noninteractive tzdata

# Install other dependencies
RUN apt install -y python3-pip docker.io ansible maven && apt install python3-requests

# Set working directory
WORKDIR /workspace

# Copy project files inside the container
COPY workspace/ /workspace/
COPY ansible/ /ansible/
