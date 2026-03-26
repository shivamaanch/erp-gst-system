#!/bin/bash
echo "Starting build..."

# Install requirements
pip install -r requirements.txt

# Start application
python app.py

echo "Build started!"
