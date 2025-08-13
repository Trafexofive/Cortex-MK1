# Makefile for Cortex-Prime - B-Line Genesis
SHELL := /bin/bash
.DEFAULT_GOAL := help

# Configuration
COMPOSE_FILE ?= infra/docker-compose.core.yml
COMPOSE := docker compose -f $(COMPOSE_FILE)

# Cosmetics
GREEN   := \033[0;32m
YELLOW  := \033[1;33m
NC      := \033[0m

help:
	@echo -e "$(GREEN)Cortex-Prime - MVJ B-Line Control Program$(NC)"
	@echo -e "$(YELLOW)Usage: make [target] [service=SERVICE_NAME]$(NC)"
	@echo "  up        - Build and start core services."
	@echo "  down      - Stop and remove core services."
	@echo "  re        - Rebuild and restart core services."
	@echo "  logs      - Follow logs for a service (default: chimera_core)."
	@echo "  clean     - Full cleanup: down + remove volumes."
	@echo "  test      - Run the B-Line interactive test client."

up:
	@echo -e "$(GREEN)Igniting Cortex-Prime B-Line...$(NC)"
	@$(COMPOSE) up --build -d --remove-orphans

down:
	@echo -e "$(YELLOW)Shutting down Cortex-Prime B-Line...$(NC)"
	@$(COMPOSE) down

re: down up

logs:
	@$(COMPOSE) logs -f $(or $(service),chimera_core)

clean:
	@echo -e "$(YELLOW)Performing full cleanup...$(NC)"
	@$(COMPOSE) down -v --remove-orphans

test:
	@echo -e "$(GREEN)Starting B-Line interactive test client...$(NC)"
	@echo "Connect to the gateway and send a message. Press CTRL+C to exit."
	@./scripts/client.sh voice

.PHONY: help up down re logs clean test
