#!/bin/bash
cd "$(dirname "$0")"

if [ ! -f "env/bin/python" ]; then
    echo "[ERROR] Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

source env/bin/activate
pip install -r requirements.txt
python main.py
