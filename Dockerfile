FROM python:3.13-slim

# Install the uv package manager
RUN pip install uv

WORKDIR /app

# Copy dependency files first to cache the virtual environment layer
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev

# Copy our application source code
COPY . .

# Expose the Gunicorn port
EXPOSE 5050

# Boot up the robust Gunicorn server natively connected to our models
CMD ["uv", "run", "gunicorn", "-c", "gunicorn.conf.py", "run:app"]
