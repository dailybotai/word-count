FROM python:3.11-slim

# Install Poetry
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml ./

# Configure poetry: don't create a virtual environment inside the container
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --only=main

# Copy application
COPY wordfreq.py ./

# Make script executable
RUN chmod +x wordfreq.py

# Create a volume mount point for input files
VOLUME ["/data"]

# Set the entry point
ENTRYPOINT ["python", "wordfreq.py"] 