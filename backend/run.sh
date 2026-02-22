#!/usr/bin/env bash
# Run backend using the venv in this folder (avoids "python not found" or wrong interpreter)
cd "$(dirname "$0")"
if [ ! -d "venv" ]; then
  echo "Creating venv..."
  python3 -m venv venv
  ./venv/bin/pip install -r requirements.txt
fi
./venv/bin/pip install -q -r requirements.txt
./venv/bin/python manage.py runserver 8000
