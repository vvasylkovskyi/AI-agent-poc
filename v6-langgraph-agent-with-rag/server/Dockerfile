# Build stage
FROM --platform=linux/amd64 python:3.11-slim as builder

# Install poetry
RUN pip install poetry

# Copy only requirements
WORKDIR /app
COPY pyproject.toml poetry.lock ./

# Configure poetry to create venv in the project directory
RUN poetry config virtualenvs.in-project true

# Install dependencies
RUN poetry install --no-dev --no-root

# Runtime stage
FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv ./.venv
COPY ./app ./app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

# Expose the port the app runs on
EXPOSE 443

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "443"] 