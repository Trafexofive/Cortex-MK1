# ======================================================================================
# MISCELLANEOUS
# ======================================================================================

RED     := \033[0;31m
GREEN   := \033[0;32m
YELLOW  := \033[1;33m 
BLUE    := \033[0;34m
NC      := \033[0m

# ======================================================================================
# GENERAL CONFIGURATION
# ======================================================================================

SHELL := /bin/bash

COMPOSE_FILE ?= docker-compose.yml
COMPOSE_TEST_FILE ?= docker-compose.test.yml
COMPOSE := docker compose -f $(COMPOSE_FILE)
COMPOSE_TEST := docker compose -f $(COMPOSE_TEST_FILE)

# ======================================================================================
# DEFAULT TARGET & SELF-DOCUMENTATION
# ======================================================================================
.DEFAULT_GOAL := help

.PHONY: help up down logs ps build restart re config status clean fclean prune \
        stop start ssh exec test download-models

# ======================================================================================
# HELP & USAGE
# ======================================================================================

help:
	@echo -e "$(BLUE)========================================================================="
	@echo -e " GraphRAG-Agent-MK1 - Makefile "
	@echo -e "=========================================================================$(NC)"
	@echo ""
	@echo -e "$(YELLOW)Usage: make [target] [service=SERVICE_NAME]$(NC)"
	@echo ""
	@echo -e "$(GREEN)Core Stack Management:$(NC)"
	@echo -e "  up                  - Start all services in detached mode."
	@echo -e "  down                - Stop and remove all services and networks."
	@echo -e "  restart             - Restart all services (down + up)."
	@echo -e "  re                  - Rebuild images and restart all services."
	@echo -e "  stop                - Stop all services without removing them."
	@echo ""
	@echo -e "$(GREEN)Building Images:$(NC)"
	@echo -e "  build [service=<name>] - Build images (all or specific service)."
	@echo ""
	@echo -e "$(GREEN)Information & Debugging:$(NC)"
	@echo -e "  status              - Show status of services (Alias: ps)."
	@echo -e "  logs [service=<name>]   - Follow logs (all or specific service)."
	@echo -e "  config              - Validate and display Docker Compose configuration."
	@echo -e "  ssh service=<name>    - Get an interactive shell into a running service."
	@echo ""
	@echo -e "$(GREEN)Cleaning & Pruning:$(NC)"
	@echo -e "  clean               - Remove stopped service containers and default network."
	@echo -e "  fclean              - Perform 'clean' and also remove volumes from compose file."
	@echo -e "  prune               - Ultimate clean: stops stack, removes volumes, and prunes Docker system."
	@echo ""
	@echo -e "$(GREEN)Testing & Model Management:$(NC)"
	@echo -e "  test                - Run the latency benchmark test."
	@echo -e "  download-models     - Download the voice and embedding models."
	@echo ""
	@echo -e "$(YELLOW)Examples:$(NC)"
	@echo -e "  make up"
	@echo -e "  make logs service=app"
	@echo -e "  make ssh service=app"
	@echo -e "  make prune"
	@echo -e "$(BLUE)========================================================================="

# ======================================================================================
# CORE STACK MANAGEMENT
# ======================================================================================

up: ## Start all services in detached mode
	@echo -e "$(GREEN)Starting GraphRAG-Agent-MK1 Stack...$(NC)"
	@$(COMPOSE) up -d --remove-orphans
	@echo -e "$(GREEN)Services are now running in detached mode.$(NC)"

down: ## Stop and remove all services and networks defined in the compose file
	@echo -e "$(RED)Shutting down GraphRAG-Agent-MK1 Stack...$(NC)"
	@$(COMPOSE) down --remove-orphans

stop: ## Stop all services without removing them
	@echo -e "$(YELLOW)Stopping services...$(NC)"
	@$(COMPOSE) stop $(service)

restart: down up ## Restart all services

re: down build up logs ## Rebuild images and restart all services

# ======================================================================================
# BUILDING IMAGES
# ======================================================================================

build: ## Build (or rebuild) images for specified service, or all if none specified
	@echo -e "$(BLUE)Building images for $(or $(service),all services)...$(NC)"
	@$(COMPOSE) build $(service)

# ======================================================================================
# INFORMATION & DEBUGGING
# ======================================================================================

status: ## Show status of running services
	@echo -e "$(BLUE)System Status Report:$(NC)"
	@$(COMPOSE) ps $(service)

ps: status ## Alias for status

logs: ## Follow logs for specified service, or all if none specified
	@echo -e "$(BLUE)Following logs for $(or $(service),all services)...$(NC)"
	@$(COMPOSE) logs -f --tail="100" $(service)

config: ## Validate and display effective Docker Compose configuration
	@echo -e "$(BLUE)Docker Compose Configuration:$(NC)"
	@$(COMPOSE) config

ssh: ## Get an interactive shell into a running service container
	@if [ -z "$(service)" ]; then \
		echo -e "$(RED)Error: Service name required. Usage: make ssh service=<service_name>$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(GREEN)Connecting to $(service)...$(NC)"
	@$(COMPOSE) exec $(service) /bin/sh || $(COMPOSE) exec $(service) /bin/bash || echo -e "$(RED)Failed to find a shell in $(service).$(NC)"

# ======================================================================================
# CLEANING & PRUNING
# ======================================================================================

clean: ## Remove stopped service containers and default network
	@echo -e "$(RED)Cleaning containers and networks...$(NC)"
	@$(COMPOSE) down --remove-orphans 

fclean: ## Remove containers, networks, volumes defined in compose file
	@echo -e "$(RED)Deep cleaning containers, networks, and volumes...$(NC)"
	@$(COMPOSE) down --volumes --remove-orphans

prune: ## Ultimate clean: stops stack, removes volumes, and prunes Docker system.
	@echo -e "$(RED)Executing ultimate prune sequence...$(NC)"
	@make fclean
	@echo -e "$(YELLOW)Pruning unused Docker resources...$(NC)"
	@docker system prune -af --volumes
	@docker builder prune -af
	@echo -e "$(GREEN)Full system prune complete.$(NC)"

# ======================================================================================
# TESTING & MODEL MANAGEMENT
# ======================================================================================

test:
	@echo -e "$(BLUE)Running latency benchmark...$(NC)"
	@$(COMPOSE) run --rm app python scripts/benchmark_latency.py

download-models:
	@echo -e "$(BLUE)Downloading models...$(NC)"
	@$(COMPOSE) run --rm app make -f /app/Makefile download-models

# ======================================================================================
# VARIABLE HANDLING
# ======================================================================================
ifeq ($(file),)
    # file is not set, use default COMPOSE_FILE
else
    COMPOSE_FILE := $(file)
    COMPOSE := docker compose -f $(COMPOSE_FILE)
endif

# Catch-all for targets that might not explicitly handle 'service' or 'args'
%:
	@: