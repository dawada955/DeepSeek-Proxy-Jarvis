#!/bin/bash
set -e
cd "$(dirname "$0")"

if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python 3 not found. Please install Python 3.11+."
    exit 1
fi

python3 install.py
