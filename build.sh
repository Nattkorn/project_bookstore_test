#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Update package lists
echo "Updating package lists..."
sudo apt-get update

# Install Python and pip if not already installed
echo "Checking and installing Python and pip..."
sudo apt-get install -y python3 python3-pip

# Install virtualenv if not already installed
echo "Checking and installing virtualenv..."
pip3 install virtualenv

# Create a virtual environment
echo "Creating virtual environment..."
virtualenv venv

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run database migrations if needed (uncomment if applicable)
# echo "Running database migrations..."
# flask db upgrade

# Start the Flask application
echo "Starting Flask application..."
export FLASK_APP=app.py
export FLASK_ENV=production
flask run --host=0.0.0.0 --port=5000

echo "Deployment script executed successfully."