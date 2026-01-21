#!/bin/bash
# Airflow Component Generator - Service Startup Script
# This script starts the component generator service with auto-reload

echo "========================================"
echo "Airflow Component Generator Service"
echo "========================================"
echo ""

# Kill any existing uvicorn processes
echo "Stopping any existing service instances..."
pkill -f "uvicorn src.service:app" 2>/dev/null
sleep 2

# Navigate to component-generator directory
cd "$(dirname "$0")/component-generator" || exit 1

# Check if .env file exists
if [ ! -f "../.env" ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and add your ANTHROPIC_API_KEY"
    exit 1
fi

echo ""
echo "Starting service with Phase 2 enhancements..."
echo "- Static analysis integration (mypy, ruff)"
echo "- Enhanced test generation with XCom/templates"
echo "- Model routing by complexity (Haiku for simple)"
echo "- Comprehensive troubleshooting documentation"
echo ""
echo "Service will be available at: http://localhost:8095"
echo "Press Ctrl+C to stop the service"
echo ""

# Start the service with auto-reload
python -m uvicorn src.service:app --host 0.0.0.0 --port 8095 --reload
