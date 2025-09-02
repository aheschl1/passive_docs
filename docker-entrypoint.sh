#!/usr/bin/env bash
set -euo pipefail

# Entrypoint that ensures ENDPOINT and MODEL are provided at runtime
if [ -z "${ENDPOINT:-}" ]; then
  echo "ERROR: ENDPOINT environment variable is not set. Provide your Ollama endpoint, e.g. http://ollama.local:11434" >&2
  exit 1
fi

if [ -z "${MODEL:-}" ]; then
  echo "ERROR: MODEL environment variable is not set. Provide the model name, e.g. llama2:13b" >&2
  exit 1
fi

# Execute the CLI with provided args
# If WORK_DIR is set (from Dockerfile ENV) check writability. If the
# mounted path is not writable by the current user, create a writable
# fallback under /tmp and pass it to the CLI via --work-dir.
WORK_DIR=${WORK_DIR:-/work}
if [ -d "${WORK_DIR}" ] && [ -w "${WORK_DIR}" ]; then
  exec passivedocs --work-dir "${WORK_DIR}" "$@"
else
  FALLBACK="/tmp/passivedocs-work"
  mkdir -p "$FALLBACK"
  chmod 700 "$FALLBACK"
  echo "INFO: ${WORK_DIR} not writable; using fallback work dir: ${FALLBACK}" >&2
  exec passivedocs --work-dir "${FALLBACK}" "$@"
fi
