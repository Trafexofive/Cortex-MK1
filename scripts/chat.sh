#!/bin/bash

# ==============================================================================
# Makefile-style shortcuts for Chat Test Service
# ==============================================================================

case "$1" in
    start)
        echo "🚀 Starting Chat Test Service (Docker)..."
        docker-compose up -d chat_test
        echo "✅ Service started at http://localhost:8888"
        ;;
    stop)
        echo "🛑 Stopping Chat Test Service..."
        docker-compose down chat_test
        echo "✅ Service stopped"
        ;;
    restart)
        echo "🔄 Restarting Chat Test Service..."
        docker-compose restart chat_test
        echo "✅ Service restarted"
        ;;
    logs)
        docker-compose logs -f chat_test
        ;;
    build)
        echo "🔨 Building Chat Test Service..."
        docker-compose build chat_test
        echo "✅ Build complete"
        ;;
    rebuild)
        echo "🔨 Rebuilding Chat Test Service..."
        docker-compose build --no-cache chat_test
        docker-compose up -d chat_test
        echo "✅ Rebuilt and started"
        ;;
    status)
        docker-compose ps chat_test
        ;;
    health)
        curl -s http://localhost:8888/health | jq || curl -s http://localhost:8888/health
        ;;
    shell)
        docker-compose exec chat_test /bin/bash
        ;;
    local)
        ./start_chat_test_local.sh
        ;;
    *)
        echo "Chat Test Service - Quick Commands"
        echo ""
        echo "Usage: ./chat.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start     - Start service in Docker"
        echo "  stop      - Stop service"
        echo "  restart   - Restart service"
        echo "  logs      - View logs (Ctrl+C to exit)"
        echo "  build     - Build Docker image"
        echo "  rebuild   - Rebuild from scratch and start"
        echo "  status    - Check service status"
        echo "  health    - Check health endpoint"
        echo "  shell     - Open shell in container"
        echo "  local     - Run locally without Docker"
        echo ""
        echo "Examples:"
        echo "  ./chat.sh start    # Start service"
        echo "  ./chat.sh logs     # Watch logs"
        echo "  ./chat.sh health   # Check if running"
        echo ""
        ;;
esac
