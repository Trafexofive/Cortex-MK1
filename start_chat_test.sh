#!/bin/bash

set -e

echo "🚀 Starting Cortex Chat Test Service (Docker)"
echo ""
echo "🔨 Building container..."
docker-compose build chat_test

echo ""
echo "🚢 Starting container..."
docker-compose up -d chat_test

echo ""
echo "✅ Service started!"
echo ""
echo "🌐 Access the chat UI at: http://localhost:8888"
echo ""
echo "📊 View logs with:"
echo "   docker-compose logs -f chat_test"
echo ""
echo "🛑 Stop with:"
echo "   docker-compose down chat_test"
echo ""
