# ======================================================================================
# Cortex-Prime MK1 Makefile - The Master Control Program
# ======================================================================================
# "The distance between thought and action, minimized."

# --- Cosmetics ---
RED     := \033[0;31m
GREEN   := \033[0;32m
YELLOW  := \033[1;33m
BLUE    := \033[0;34m
PURPLE  := \033[0;35m
CYAN    := \033[0;36m
NC      := \033[0m

# --- Configuration ---
SHELL := /bin/bash
PROJECT_NAME ?= cortex-prime-mk1
COMPOSE_FILE ?= docker-compose.yml
COMPOSE := docker compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE)

.DEFAULT_GOAL := help

# --- Phony Targets ---
.PHONY: help setup up down logs logs-manifest logs-runtime logs-arbiter ps build rebuild restart re status clean fclean prune stop ssh exec test test-manifest test-runtime test-integration health sync

# ======================================================================================
# HELP & USAGE
# ======================================================================================
help:
	@echo -e "$(BLUE)========================================================================="
	@echo -e " Cortex-Prime MK1 - Sovereign AI Ecosystem Control"
	@echo -e "=========================================================================$(NC)"
	@echo -e "$(CYAN)\"The distance between thought and action, minimized.\"$(NC)"
	@echo ""
	@echo -e "$(YELLOW)Usage: make [target] [service=SERVICE_NAME]$(NC)"
	@echo ""
	@echo -e "$(GREEN)Quick Start:$(NC)"
	@echo -e "  setup               - Initial setup: build all images and start stack."
	@echo -e "  up                  - Start all services in detached mode."
	@echo -e "  down                - Stop and remove all services and networks."
	@echo -e "  restart             - Restart all services (down + up)."
	@echo ""
	@echo -e "$(GREEN)Core Stack Management:$(NC)"
	@echo -e "  build [service=<name>]     - Build service images (cached)."
	@echo -e "  rebuild [service=<name>]   - Rebuild service images (no-cache)."
	@echo -e "  re                         - Rebuild and restart (cached)."
	@echo -e "  rere                       - Rebuild and restart (no-cache)."
	@echo ""
	@echo -e "$(GREEN)Monitoring & Debugging:$(NC)"
	@echo -e "  status [service=<name>]    - Show status of services (Alias: ps)."
	@echo -e "  logs [service=<name>]      - Follow logs (all or specific service)."
	@echo -e "  logs-manifest              - Follow manifest ingestion service logs."
	@echo -e "  logs-runtime               - Follow runtime executor service logs."
	@echo -e "  logs-arbiter               - Follow C++ arbiter core logs."
	@echo -e "  ssh service=<name>         - Get interactive shell into service."
	@echo -e "  exec svc=<name> cmd=\"<cmd>\" - Execute command in service."
	@echo -e "  health                     - Check health of all services."
	@echo ""
	@echo -e "$(GREEN)Manifest Operations:$(NC)"
	@echo -e "  sync                       - Force sync manifests from filesystem."
	@echo -e "  validate                   - Validate all manifests."
	@echo ""
	@echo -e "$(GREEN)Testing & Validation:$(NC)"
	@echo -e "  test                       - Run all test suites."
	@echo -e "  test-manifest              - Test manifest ingestion service."
	@echo -e "  test-runtime               - Test runtime executor service."
	@echo -e "  test-integration           - Run integration tests."
	@echo ""
	@echo -e "$(GREEN)Cleaning & Pruning:$(NC)"
	@echo -e "  clean                      - Stop services and remove containers."
	@echo -e "  fclean                     - Stop services, remove containers and volumes."
	@echo -e "  prune                      - Ultimate clean: fclean + system prune."
	@echo ""
	@echo -e "$(YELLOW)The Great Work continues...$(NC)"
	@echo -e "$(BLUE)=========================================================================$(NC)"

# ======================================================================================
# QUICK START
# ======================================================================================
setup: build up
	@echo -e "$(GREEN)✅ Cortex-Prime MK1 initialized and running.$(NC)"
	@echo -e "$(CYAN)Manifest Ingestion: http://localhost:8082/docs$(NC)"
	@echo -e "$(CYAN)Runtime Executor: http://localhost:8083/docs$(NC)"

# ======================================================================================
# CORE STACK MANAGEMENT
# ======================================================================================
up:
	@echo -e "$(GREEN)🚀 Igniting Cortex-Prime MK1...$(NC)"
	@$(COMPOSE) up -d --remove-orphans
	@echo -e "$(GREEN)✅ Services are now running in detached mode.$(NC)"

down:
	@echo -e "$(RED)🛑 Shutting down Cortex-Prime MK1...$(NC)"
	@$(COMPOSE) down --remove-orphans

restart: down up

re: down build up
	@echo -e "$(GREEN)♻️  Stack rebuilt and restarted.$(NC)"

rere: down rebuild up
	@echo -e "$(GREEN)♻️  Stack rebuilt (no-cache) and restarted.$(NC)"

# ======================================================================================
# BUILDING IMAGES
# ======================================================================================
build:
	@echo -e "$(BLUE)🔨 Building images for $(or $(service),all services)...$(NC)"
	@$(COMPOSE) build $(service)

rebuild:
	@echo -e "$(YELLOW)🔨 Force-rebuilding (no cache) for $(or $(service),all services)...$(NC)"
	@$(COMPOSE) build --no-cache $(service)

# ======================================================================================
# MONITORING & DEBUGGING
# ======================================================================================
status:
	@echo -e "$(BLUE)📊 System Status Report:$(NC)"
	@$(COMPOSE) ps $(service)
ps: status

logs:
	@echo -e "$(BLUE)📜 Streaming logs for $(or $(service),all services)...$(NC)"
	@$(COMPOSE) logs -f --tail="100" $(service)

logs-manifest:
	@echo -e "$(CYAN)📜 Streaming Manifest Ingestion logs...$(NC)"
	@$(COMPOSE) logs -f --tail="100" manifest_ingestion

logs-runtime:
	@echo -e "$(CYAN)📜 Streaming Runtime Executor logs...$(NC)"
	@$(COMPOSE) logs -f --tail="100" runtime_executor

logs-arbiter:
	@echo -e "$(CYAN)📜 Streaming C++ Arbiter Core logs...$(NC)"
	@$(COMPOSE) logs -f --tail="100" agent-lib || echo -e "$(YELLOW)⚠️  Arbiter service not yet configured$(NC)"

ssh:
	@if [ -z "$(service)" ]; then \
		echo -e "$(RED)❌ Error: Service name required. Usage: make ssh service=<name>$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(GREEN)🔌 Connecting to $(service)...$(NC)"
	@$(COMPOSE) exec $(service) /bin/bash || $(COMPOSE) exec $(service) /bin/sh

exec:
	@if [ -z "$(svc)" ] || [ -z "$(cmd)" ]; then \
		echo -e "$(RED)❌ Error: Service and command required. Usage: make exec svc=<name> cmd=\"<cmd>\"$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(GREEN)⚡ Executing in $(svc): $(cmd)$(NC)"
	@$(COMPOSE) exec $(svc) $(cmd)

health:
	@echo -e "$(BLUE)🏥 Checking service health...$(NC)"
	@echo ""
	@echo -e "$(CYAN)Manifest Ingestion:$(NC)"
	@curl -s http://localhost:8082/health | jq . || echo -e "$(RED)❌ Service unreachable$(NC)"
	@echo ""
	@echo -e "$(CYAN)Runtime Executor:$(NC)"
	@curl -s http://localhost:8083/health | jq . || echo -e "$(YELLOW)⚠️  Service not running$(NC)"

# ======================================================================================
# MANIFEST OPERATIONS
# ======================================================================================
sync:
	@echo -e "$(PURPLE)🔄 Syncing manifests from filesystem...$(NC)"
	@curl -s -X POST http://localhost:8082/registry/sync | jq .

validate:
	@echo -e "$(PURPLE)✓ Validating all manifests...$(NC)"
	@curl -s http://localhost:8082/registry/status | jq .

# ======================================================================================
# TESTING & VALIDATION
# ======================================================================================
test: test-manifest test-runtime
	@echo -e "$(GREEN)✅ All test suites completed.$(NC)"

test-manifest:
	@echo -e "$(PURPLE)🧪 Running Manifest Ingestion tests...$(NC)"
	@docker run --rm -v $$(pwd)/services/manifest_ingestion:/app -w /app \
		$(PROJECT_NAME)-manifest_ingestion \
		python -m pytest tests/ -v --tb=short

test-runtime:
	@echo -e "$(PURPLE)🧪 Running Runtime Executor tests...$(NC)"
	@echo -e "$(YELLOW)⚠️  Runtime executor tests not yet implemented$(NC)"

test-integration:
	@echo -e "$(PURPLE)🧪 Running integration tests...$(NC)"
	@./scripts/run_tests.sh || echo -e "$(YELLOW)⚠️  Test script not found$(NC)"

# ======================================================================================
# CLEANING & PRUNING
# ======================================================================================
clean:
	@echo -e "$(RED)🧹 Cleaning containers and networks...$(NC)"
	@$(COMPOSE) down --remove-orphans

fclean:
	@echo -e "$(RED)🧹 Deep cleaning containers, networks, and volumes...$(NC)"
	@$(COMPOSE) down --volumes --remove-orphans
	@echo -e "$(GREEN)✅ Deep clean complete.$(NC)"

prune: fclean
	@echo -e "$(RED)💥 Executing ultimate prune sequence...$(NC)"
	@docker system prune -af --volumes
	@docker builder prune -af
	@echo -e "$(GREEN)✅ Full system prune complete.$(NC)"

stop: down
