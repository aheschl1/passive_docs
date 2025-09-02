# Documentation Agent

This repository contains "PassiveDocs": a small agent that uses an LLM (via Ollama) to add or improve documentation in code repositories and create PRs automatically.

This README explains how to run the project locally and how to build and run it in Docker. The Docker image respects two environment variables to configure the LLM connection:

- MODEL - the model name to pass to the Ollama client (for example, "llama2:13b").
- ENDPOINT - the full Ollama HTTP endpoint (for example, "http://ollama.local:11434").

Both can be supplied at runtime as environment variables. For CI or reproducible runs you may supply defaults at build-time using --build-arg (not recommended for secrets).

Quick start (local):

1. Create a python virtualenv and install requirements:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

2. Run the CLI against a repository (the tool always uses a fixed `./work` directory):

```bash
export ENDPOINT="http://ollama.local:11434"
export MODEL="llama2:13b"
passivedocs git@github.com:owner/repo.git
```

Docker build and run

The provided `Dockerfile` builds a small image with the `passivedocs` CLI installed. The image does not require model or endpoint values at build time — provide them when you run the container so one image can be used for many runs and repositories.

Build the image:

```bash
docker build -t passivedocs:latest .
```

Run the container (required: provide runtime environment variables):

```bash
docker run --rm -e ENDPOINT="http://ollama.local:11434" -e MODEL="llama2:13b" \
  passivedocs:latest git@github.com:owner/repo.git
```

Notes and security

- The Ollama endpoint and model name are passed to the Ollama client by reading the environment variables `ENDPOINT` and `MODEL`. Do not commit secrets into the repo.
- The Docker image is intentionally lightweight (based on python:3.11-slim). If you need system-level libraries for your target repos, add them to the Dockerfile.

Troubleshooting

- If the container cannot reach your Ollama service, confirm the network route and that the Ollama server is listening on an accessible interface.
- For development, prefer running the CLI locally inside a virtualenv so you can iterate quickly.

Contributing

Pull requests welcome. Small improvements: add tests, harden prompt parsing, or add a dry-run mode.
