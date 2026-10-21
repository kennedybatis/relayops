#!/bin/sh
set -eu
relayops_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
relayops_bin=${RELAYOPS_OLLAMA:-}
if [ -z "$relayops_bin" ]; then
  relayops_bin=$(command -v ollama || true)
fi
if [ -z "$relayops_bin" ]; then
  relayops_bin="$relayops_root/runtime/ollama-install/Ollama.app/Contents/Resources/ollama"
fi
if [ ! -x "$relayops_bin" ]; then
  echo 'Install Ollama from https://ollama.com/download first.' >&2
  exit 1
fi
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_MODELS="$relayops_root/runtime/ollama-models"
export OLLAMA_NO_CLOUD=true
exec "$relayops_bin" serve
