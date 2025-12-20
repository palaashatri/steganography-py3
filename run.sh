#!/usr/bin/env bash
set -euo pipefail

# Bootstrap venv and run the steganography CLI
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

# shellcheck source=/dev/null
source .venv/bin/activate

pip install --upgrade pip >/dev/null
pip install -r requirements.txt >/dev/null

# If arguments are provided, pass them through to the CLI.
# Otherwise, run a simple encode demo.
if [[ $# -gt 0 ]]; then
  python3 1_Implementation/app.py "$@"
else
  python3 1_Implementation/app.py encode \
    --image "1_Implementation/test.jpg" \
    --out "secret.png" \
    --message "Hello, World"
fi
