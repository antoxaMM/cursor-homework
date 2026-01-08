# Use Python 3.11 slim as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (frozen to ensure exact versions)
RUN uv sync --frozen

# Copy source code
COPY src/ ./src/

# Set Python to run in unbuffered mode (better for logging)
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["uv", "run", "python", "src/bot.py"]

