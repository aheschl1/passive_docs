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
exec passivedocs "$@"
