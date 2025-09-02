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

Configuration file (`passivedocs.yml`)

If a repository contains a `passivedocs.yml` file it will be read and used. This file is optional. If it is absent the agent will proceed and will not ignore any files (i.e., no ignore rules are applied).

Docker build and run

The provided `Dockerfile` builds a small image with the `passivedocs` CLI installed. The image does not require model or endpoint values at build time — provide them when you run the container so one image can be used for many runs and repositories.

Build the image:

```bash
docker build -t passivedocs:latest .
```

Run the container (required: provide runtime environment variables):

Mount a host `work` directory into the container so repository clones and PR branches persist on the host. Two options are supported if you have permission problems with mounts:

1) Preferred: create a host directory owned by your UID and mount it. This ensures the non-root `passivedocs` user inside the container can write to it.

```bash
mkdir -p ./work
sudo chown $(id -u):$(id -g) ./work
docker run --rm -e ENDPOINT="http://ollama.local:11434" -e MODEL="llama2:13b" \
  -v $(pwd)/work:/work \
  passivedocs:latest git@github.com:owner/repo.git
```

2. Fallback: if you cannot change host ownership, the container will detect if the mounted `/work` is not writable by the runtime user and automatically use a writable fallback under `/tmp` inside the container; persistent host storage won't be available in that case. To explicitly control the workspace from the host or from Docker, pass `--work-dir` to the CLI or set the `WORK_DIR` environment variable.

```bash
# Explicitly set work dir inside container (overrides WORK_DIR env):
docker run --rm -e ENDPOINT="http://ollama.local:11434" -e MODEL="llama2:13b" \
  -v $(pwd)/work:/work \
  passivedocs:latest git@github.com:owner/repo.git --work-dir /work
```

When running locally (not in Docker), the CLI defaults to `./work` unless you pass `--work-dir` or set the `WORK_DIR` environment variable.

Notes and security

- The Ollama endpoint and model name are passed to the Ollama client by reading the environment variables `ENDPOINT` and `MODEL`. Do not commit secrets into the repo.
- The Docker image is intentionally lightweight (based on python:3.11-slim). If you need system-level libraries for your target repos, add them to the Dockerfile.

Troubleshooting

- If the container cannot reach your Ollama service, confirm the network route and that the Ollama server is listening on an accessible interface.
- For development, prefer running the CLI locally inside a virtualenv so you can iterate quickly.

- If you see errors like "ssh: No such file or directory" or git clone fails for `git@...` URLs, ensure the image has an SSH client and that you provide SSH credentials to the container. The image includes `openssh-client` so `ssh` is available, but you still need to provide keys.

  Two common ways to make SSH keys available inside the container:

  1. Mount your SSH directory (less secure on multi-user hosts):

  ```bash
  docker run --rm -e ENDPOINT="..." -e MODEL="..." \
    -v ~/.ssh:/home/passivedocs/.ssh:ro \
    -v $(pwd)/work:/work \
    passivedocs:latest git@github.com:owner/repo.git
  ```

  2. Use SSH agent forwarding (recommended):

  ```bash
  # On the host
  eval "$(ssh-agent -s)"
  ssh-add ~/.ssh/id_rsa

  # Run container with SSH_AUTH_SOCK mounted
  docker run --rm -e ENDPOINT="..." -e MODEL="..." \
    -v $SSH_AUTH_SOCK:/ssh-agent \
    -e SSH_AUTH_SOCK=/ssh-agent \
    -v $(pwd)/work:/work \
    passivedocs:latest git@github.com:owner/repo.git
  ```