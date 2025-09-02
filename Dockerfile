FROM python:3.11-slim

# Install runtime dependencies and create app user
RUN apt-get update \
    && apt-get install -y --no-install-recommends git openssh-client build-essential \
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

# Provide a persistent work directory mounted by users at runtime.
# The container will use /work as the workspace; declare it as a volume so
# users can mount a host directory into it.
VOLUME ["/work"]

# Ensure /work exists and is owned by the non-root runtime user
## Provide a non-root user for running the agent
RUN useradd --create-home --shell /bin/bash passivedocs || true

# Ensure /work exists and is owned by the non-root runtime user
RUN mkdir -p /work \
    && chown -R passivedocs:passivedocs /work

USER passivedocs
ENV WORK_DIR="/work"

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
