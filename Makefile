.DEFAULT_GOAL := help

# --- Colors ---
RED     := [0;31m
GREEN   := [0;32m
YELLOW  := [1;33m
NC      := [0m

# --- Configuration ---
COMPOSE_FILE := docker-compose.yml
COMPOSE := docker compose -f $(COMPOSE_FILE)

