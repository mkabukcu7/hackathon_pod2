#!/bin/bash

# Multi-Agent System - Start Script

echo "========================================"
echo "Multi-Agent System - Startup"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "Warning: .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "Please edit .env file with your API keys before running the application."
    echo ""
fi

# Ask user which mode to run
echo ""
echo "Select mode to run:"
echo "1) API Server (FastAPI)"
echo "2) CLI Interactive Mode"
echo "3) CLI Query Mode"
echo "4) Run Examples"
echo "5) Run Tests"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo ""
        echo "Starting API server..."
        echo "API will be available at http://localhost:8000"
        echo "API documentation at http://localhost:8000/docs"
        python src/api.py
        ;;
    2)
        echo ""
        echo "Starting interactive CLI..."
        python src/main.py --mode interactive
        ;;
    3)
        read -p "Enter your query: " query
        read -p "Enter location (default: London): " location
        location=${location:-London}
        python src/main.py --mode query --query "$query" --location "$location"
        ;;
    4)
        echo ""
        echo "Running examples..."
        python examples/examples.py
        ;;
    5)
        echo ""
        echo "Running tests..."
        python test_basic.py
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
