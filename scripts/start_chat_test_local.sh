#!/bin/bash

# ==============================================================================
# Local Development Startup Script for Chat Test Service
# Use this when you want to run the service locally without Docker
# ==============================================================================

set -e

echo "🚀 Starting Cortex Chat Test Service (Local)"
echo ""

cd "$(dirname "$0")"

# Check if running in the repo root
if [ ! -d "services/chat_test" ]; then
    echo "❌ Error: Must run from repository root"
    exit 1
fi

# Check dependencies
echo "🔍 Checking dependencies..."
if ! python3 -c "import fastapi, uvicorn, pydantic" 2>/dev/null; then
    echo "⚠️  Missing dependencies. Installing..."
    pip3 install -r services/chat_test/requirements.txt
fi

echo ""
echo "🌐 Starting server on http://localhost:8888"
echo ""

# Run the service
cd services/chat_test
python3 chat_test_service.py
