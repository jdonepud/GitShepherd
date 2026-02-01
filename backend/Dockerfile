# Dockerfile for test sandbox
FROM python:3.11-slim

# Install common tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install common Python testing tools
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    black \
    ruff \
    mypy

WORKDIR /workspace

# Default command
CMD ["/bin/bash"]
