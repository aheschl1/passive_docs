FROM python:3.11-slim

# Install runtime dependencies and create app user
RUN apt-get update \
    && apt-get install -y --no-install-recommends git build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files
COPY setup.py /app/
COPY passivedocs /app/passivedocs
COPY passivedocs.yml /app/passivedocs.yml
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# Install package
RUN pip install --no-cache-dir . \
    && chmod +x /usr/local/bin/docker-entrypoint.sh

# Do not bake MODEL/ENDPOINT at build-time. They must be provided at runtime.
ENV MODEL=""
ENV ENDPOINT=""

# Provide a non-root user for running the agent
RUN useradd --create-home --shell /bin/bash passivedocs || true
USER passivedocs

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
