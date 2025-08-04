# ======================================================================================
# GraphRAG-Agent-MK1 - Enhanced & Aligned Makefile v2.1
#
# This Makefile has been patched to work directly with the existing project
# structure. It replaces incompatible commands and adapts to the current file layout.
# ======================================================================================

SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c
.DEFAULT_GOAL := help
.ONESHELL:
.SILENT:

# ======================================================================================
# COLOR DEFINITIONS & FORMATTING
# ======================================================================================

# Colors
RED     := \033[0;31m
GREEN   := \033[0;32m
YELLOW  := \033[1;33m
BLUE    := \033[0;34m
PURPLE  := \033[0;35m
CYAN    := \033[0;36m
WHITE   := \033[1;37m
GRAY    := \033[0;37m
BOLD    := \033[1m
NC      := \033[0m

# Icons
ROCKET  := 🚀
GEAR    := ⚙️
CLEAN   := 🧹
TEST    := 🧪
INFO    := ℹ️
WARN    := ⚠️
ERROR   := ❌
SUCCESS := ✅
DOCKER  := 🐳
BUILD   := 🔨

# ======================================================================================
# CONFIGURATION & VARIABLES
# ======================================================================================

# Project Configuration
PROJECT_NAME := graphrag-agent-mk1
VERSION := $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
BUILD_DATE := $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Docker Configuration
COMPOSE_FILE ?= docker-compose.yml
COMPOSE_TEST_FILE ?= docker-compose.test.yml
COMPOSE_PROD_FILE ?= docker-compose.prod.yml
COMPOSE_DEV_FILE ?= docker-compose.dev.yml

# Dynamic compose command based on environment
# Patched to be resilient if dev/prod files don't exist
ENV ?= dev
COMPOSE_FILES := -f $(COMPOSE_FILE)

ifeq ($(ENV),prod)
    ifneq ("$(wildcard $(COMPOSE_PROD_FILE))","")
        COMPOSE_FILES += -f $(COMPOSE_PROD_FILE)
    endif
else ifeq ($(ENV),test)
    COMPOSE_FILES += -f $(COMPOSE_TEST_FILE)
else
    ifneq ("$(wildcard $(COMPOSE_DEV_FILE))","")
        COMPOSE_FILES += -f $(COMPOSE_DEV_FILE)
    endif
endif

COMPOSE := docker compose $(COMPOSE_FILES)
COMPOSE_EXEC := $(COMPOSE) exec
COMPOSE_RUN := $(COMPOSE) run --rm

# Service Configuration
DEFAULT_SERVICE := app
service ?= $(DEFAULT_SERVICE)

# Build Configuration
DOCKER_BUILDKIT := 1
COMPOSE_DOCKER_CLI_BUILD := 1

# Export environment variables
export DOCKER_BUILDKIT COMPOSE_DOCKER_CLI_BUILD PROJECT_NAME VERSION BUILD_DATE GIT_COMMIT

# ======================================================================================
# UTILITY FUNCTIONS
# ======================================================================================

define log
	echo -e "$(BOLD)$(BLUE)[$(shell date +'%H:%M:%S')] $(1)$(NC)"
endef

define success
	echo -e "$(SUCCESS) $(GREEN)$(1)$(NC)"
endef

define warn
	echo -e "$(WARN) $(YELLOW)$(1)$(NC)"
endef

define error
	echo -e "$(ERROR) $(RED)$(1)$(NC)"
endef

define info
	echo -e "$(INFO) $(CYAN)$(1)$(NC)"
endef

define check_service
	if [ -z "$(1)" ]; then \
		$(call error,"Service name required. Usage: make $(2) service=<service_name>"); \
		exit 1; \
	fi
endef

define check_docker
	if ! command -v docker &> /dev/null; then \
		$(call error,"Docker is not installed or not in PATH"); \
		exit 1; \
	fi
	if ! docker info &> /dev/null; then \
		$(call error,"Docker daemon is not running"); \
		exit 1; \
	fi
endef

# ======================================================================================
# PHONY DECLARATIONS
# ======================================================================================

.PHONY: help version info env-check deps-check \
        up down restart re start stop kill \
        build build-nocache pull \
        logs logs-tail follow shell exec run \
        ps status health inspect \
        test benchmark \
        clean fclean prune reset nuke \
        deploy \
        download-models \
        lint format security-scan \
        graph-backup graph-restore

# ======================================================================================
# HELP & DOCUMENTATION
# ======================================================================================

help: ## Show this help message
	echo -e "$(BOLD)$(BLUE)========================================================================="
	echo -e " $(ROCKET) GraphRAG-Agent-MK1 - Enhanced & Aligned Makefile v2.1"
	echo -e " Version: $(VERSION) | Build: $(BUILD_DATE)"
	echo -e "=========================================================================$(NC)"
	echo ""
	echo -e "$(YELLOW)Usage: make [target] [ENV=env] [service=name] [args=...]$(NC)"
	echo ""
	awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { \
		category = ""; \
		if ($$1 ~ /^(up|down|restart|re|start|stop|kill)$$/) category = "$(GREEN)Core Stack:$(NC)"; \
		else if ($$1 ~ /^(build|pull)/) category = "$(BLUE)Building:$(NC)"; \
		else if ($$1 ~ /^(logs|ps|status|health|inspect|follow|shell|exec|run)/) category = "$(CYAN)Debugging:$(NC)"; \
		else if ($$1 ~ /^(test|benchmark)/) category = "$(PURPLE)Testing:$(NC)"; \
		else if ($$1 ~ /^(clean|fclean|prune|reset|nuke)/) category = "$(RED)Cleaning:$(NC)"; \
		else if ($$1 ~ /^(graph-)/) category = "$(WHITE)Database:$(NC)"; \
		else if ($$1 ~ /^(download-models)/) category = "$(CYAN)Models:$(NC)"; \
		else category = "$(GRAY)Other:$(NC)"; \
		if (category != last_category) { print ""; print category; last_category = category; } \
		printf "  %-20s %s\n", $$1, $$2 \
	}' $(MAKEFILE_LIST)
	echo ""
	echo -e "$(YELLOW)Environment Variables:$(NC)"
	echo -e "  ENV=dev|test|prod    - Set environment (default: dev)"
	echo -e "  service=<name>       - Target specific service"
	echo -e "  args=<arguments>     - Pass additional arguments"

version: ## Show version information
	echo -e "$(BOLD)$(PROJECT_NAME) Version Information$(NC)"
	echo -e "Version: $(GREEN)$(VERSION)$(NC)"
	echo -e "Build Date: $(YELLOW)$(BUILD_DATE)$(NC)"
	echo -e "Git Commit: $(BLUE)$(GIT_COMMIT)$(NC)"
	echo -e "Environment: $(PURPLE)$(ENV)$(NC)"

info: version ## Show system and project information
	echo ""
	echo -e "$(BOLD)System Information$(NC)"
	echo -e "OS: $(shell uname -s) $(shell uname -r)"
	echo -e "Architecture: $(shell uname -m)"
	echo -e "Shell: $$SHELL"
	echo -e "Docker Version: $(shell docker --version 2>/dev/null || echo 'Not installed')"
	echo -e "Docker Compose Version: $(shell docker compose version 2>/dev/null || echo 'Not installed')"
	echo ""
	echo -e "$(BOLD)Project Configuration$(NC)"
	echo -e "Compose Files: $(COMPOSE_FILES)"

# ======================================================================================
# HEALTH CHECKS & PREREQUISITES
# ======================================================================================

env-check: ## Check environment and prerequisites
	$(call log,"Checking environment...")
	$(call check_docker)
	$(call success,"Docker is available and running")

# ======================================================================================
# CORE STACK MANAGEMENT
# ======================================================================================

up: env-check ## Start all services in detached mode
	$(call log,"Starting $(PROJECT_NAME) stack ($(ENV) environment)...")
	$(COMPOSE) up -d --remove-orphans
	$(call success,"Stack is running in detached mode")
	make ps

down: ## Stop and remove all services and networks
	$(call log,"Shutting down $(PROJECT_NAME) stack...")
	$(COMPOSE) down --remove-orphans
	$(call success,"Stack has been stopped")

restart: down up ## Restart all services (down + up)

re: down build up ## Rebuild images and restart all services

start: ## Start existing stopped services
	$(call log,"Starting stopped services...")
	$(COMPOSE) start $(service)
	$(call success,"Services started")

stop: ## Stop services without removing them
	$(call log,"Stopping services...")
	$(COMPOSE) stop $(service)
	$(call success,"Services stopped")

kill: ## Force kill services
	$(call warn,"Force killing services...")
	$(COMPOSE) kill $(service)
	$(call success,"Services killed")

# ======================================================================================
# BUILDING & IMAGE MANAGEMENT
# ======================================================================================

build: ## Build or rebuild images
	$(call log,"Building images for $(or $(service),all services)...")
	$(COMPOSE) build $(service)
	$(call success,"Build completed")

build-nocache: ## Build images without cache
	$(call log,"Building images without cache...")
	$(COMPOSE) build --no-cache $(service)
	$(call success,"Build completed (no cache)")

pull: ## Pull latest images
	$(call log,"Pulling latest images...")
	$(COMPOSE) pull $(service)
	$(call success,"Images pulled")

# ======================================================================================
# DEBUGGING & MONITORING
# ======================================================================================

logs: ## Show logs for services
	$(call info,"Showing logs for $(or $(service),all services)...")
	$(COMPOSE) logs $(service)

logs-tail: ## Follow logs with tail
	$(call info,"Following logs for $(or $(service),all services)...")
	$(COMPOSE) logs -f --tail=100 $(service)

follow: logs-tail ## Alias for logs-tail

shell: ## Get interactive shell in service container
	$(call check_service,$(service),shell)
	$(call log,"Opening shell in $(service)...")
	$(COMPOSE_EXEC) $(service) /bin/bash || \
	$(COMPOSE_EXEC) $(service) /bin/sh || \
	$(call error,"Failed to open shell in $(service)")

exec: ## Execute command in running service
	$(call check_service,$(service),exec)
	$(call log,"Executing command in $(service)...")
	$(COMPOSE_EXEC) $(service) $(args)

run: ## Run one-off command in new container
	$(call check_service,$(service),run)
	$(call log,"Running command in new $(service) container...")
	$(COMPOSE_RUN) $(service) $(args)

ps: ## Show running services with status
	echo -e "$(BOLD)$(DOCKER) Container Status:$(NC)"
	$(COMPOSE) ps

status: ps ## Alias for ps

health: ## Check health of all services
	$(call log,"Checking service health...")
	docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" --filter "label=project=GraphRAG-Agent-MK1"

inspect: ## Inspect service configuration
	$(call check_service,$(service),inspect)
	$(call log,"Inspecting $(service)...")
	$(COMPOSE) config --services | grep -q "$(service)" && \
	docker inspect "$$($(COMPOSE) ps -q $(service))" | jq '.[0]' || \
	$(call error,"Service $(service) not found or not running")

# ======================================================================================
# TESTING SUITE
# ======================================================================================

test: ## Run all available tests
	$(call log,"Running tests...")
	$(COMPOSE_RUN) app python -m pytest tests/ -v $(args)
	$(call success,"Tests completed")

benchmark: ## Run performance benchmarks
	$(call log,"Running performance benchmarks...")
	$(COMPOSE_RUN) app python scripts/benchmark_latency.py $(args)
	$(call success,"Benchmarks completed")

# ======================================================================================
# CLEANING & MAINTENANCE
# ======================================================================================

clean: ## Remove stopped containers and networks
	$(call log,"Cleaning containers and networks...")
	$(COMPOSE) down --remove-orphans
	$(call success,"Clean completed")

fclean: ## Deep clean: remove containers, networks, and volumes
	$(call warn,"Performing deep clean (containers, networks, volumes)...")
	$(COMPOSE) down --volumes --remove-orphans
	$(call success,"Deep clean completed")

prune: ## System prune: remove all unused Docker resources
	$(call warn,"Performing system prune...")
	make fclean
	docker system prune -af --volumes
	docker builder prune -af
	docker network prune -f
	$(call success,"System prune completed")

reset: fclean up ## Reset stack: clean and restart

nuke: ## Nuclear option: remove everything including images
	$(call error,"NUCLEAR CLEAN: This will remove EVERYTHING!")
	read -p "Are you sure? Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ] || exit 1
	$(COMPOSE) down --volumes --remove-orphans --rmi all
	docker system prune -af --volumes
	docker builder prune -af
	docker image prune -af
	$(call success,"Nuclear clean completed")

# ======================================================================================
# OPERATIONS & DEPLOYMENT
# ======================================================================================

deploy: env-check ## Deploy to production
	$(call log,"Deploying to production...")
	ENV=prod make up
	$(call success,"Deployment completed")

# ======================================================================================
# MODEL MANAGEMENT
# ======================================================================================

download-models: ## Download required models using the app's Makefile
	$(call log,"Downloading models via internal app Makefile...")
	$(COMPOSE_RUN) app make -f /app/app/Makefile download-models
	$(call success,"Models downloaded")

# ======================================================================================
# GRAPH DATABASE OPERATIONS
# ======================================================================================

graph-backup: ## Backup the Neo4j database
	$(call log,"Backing up Neo4j database...")
	$(call warn,"Note: This requires a 'backups' volume mounted to the neo4j service.")
	mkdir -p ./backups
	$(COMPOSE_EXEC) neo4j bin/neo4j-admin database backup --name=neo4j --to-path=/backups
	$(call success,"Neo4j backup completed to the container's /backups directory.")

graph-restore: ## Restore the Neo4j database
	$(call error,"Neo4j restore is a complex operation and is not yet implemented.")
	$(call info,"You typically need to stop the database, run 'neo4j-admin database restore', and restart.")

# ======================================================================================
# CODE QUALITY & SECURITY (DISABLED BY DEFAULT)
# ======================================================================================
# To enable these targets, add flake8, pylint, black, isort, safety, and bandit
# to your requirements.txt file and rebuild your 'app' image.

# lint: ## Run code linting
# 	$(call log,"Running linters...")
# 	$(COMPOSE_RUN) $(service) flake8 . $(args)
# 	$(COMPOSE_RUN) $(service) pylint **/*.py $(args)
# 	$(call success,"Linting completed")

# format: ## Format code
# 	$(call log,"Formatting code...")
# 	$(COMPOSE_RUN) $(service) black . $(args)
# 	$(COMPOSE_RUN) $(service) isort . $(args)
# 	$(call success,"Code formatting completed")

# security-scan: ## Run security scanning
# 	$(call log,"Running security scan...")
# 	$(COMPOSE_RUN) $(service) safety check $(args)
# 	$(COMPOSE_RUN) $(service) bandit -r . $(args)
# 	$(call success,"Security scan completed")

# ======================================================================================
# CATCH-ALL & ERROR HANDLING
# ======================================================================================

# Catch undefined targets
%:
	$(call error,"Unknown target: $@")
	echo "Run 'make help' to see available targets."
	exit 1
