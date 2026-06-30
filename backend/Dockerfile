FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build deps for psycopg/asyncpg wheels just in case + libpq for runtime.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        libpq5 \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt

# Source is bind-mounted in compose for hot-reload during dev.
COPY . .

EXPOSE 8000
