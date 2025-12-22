# /backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv (The Astral package manager)
# Install uv (The Astral package manager)
RUN pip install uv

# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen: Require lockfile to be up to date
# --no-dev: Skip dev dependencies
RUN uv sync --frozen --no-dev

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 8000

# Run using the virtual environment created by uv
# Note: uv creates venv in .venv by default
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
