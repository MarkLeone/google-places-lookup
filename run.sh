#!/usr/bin/env bash
# Quick-start script for running the Google Places lookup

set -e

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Run ./setup_env.sh first"
    exit 1
fi

source venv/bin/activate

# Export API key from .env
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Run ./setup_env.sh first"
    exit 1
fi

export GOOGLE_PLACES_API_KEY=$(grep GOOGLE_PLACES_API_KEY .env | cut -d '=' -f2)

# Run the script with provided arguments or default to queries.txt
if [ $# -eq 0 ]; then
    echo "Running with queries from queries.txt..."
    python google_places_lookup.py --queries-file queries.txt "$@"
else
    python google_places_lookup.py "$@"
fi

