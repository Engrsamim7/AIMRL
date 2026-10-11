#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3.12 -m venv .venv
.venv/bin/python -m pip install --requirement requirements-lock.txt
.venv/bin/python -m pip check
echo 'Activate with: source .venv/bin/activate'
