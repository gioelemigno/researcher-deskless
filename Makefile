SCRIPT_DIR := $(shell pwd)
PUID := $(shell id -u)
PGID := $(shell id -g)
SENTINEL := $(SCRIPT_DIR)/.last-build

.PHONY: help run build generate check-rebuild

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  run       Build if config changed, then start the launcher"
	@echo "  build     Generate compose, build image and save to tar"
	@echo "  generate  Generate docker-compose.yml from config.yaml"
	@echo "  help      Show this help message"

generate:
	@echo "==> Generating compose.yaml..."
	@python3 $(SCRIPT_DIR)/utils/generate-compose.py

build: generate
	mkdir -p ./data
	PUID=$(PUID) PGID=$(PGID) docker compose build
	docker save researcher-deskless | gzip > $(SCRIPT_DIR)/researcher-deskless.tar.gz
	@grep -v '^\s*#' $(SCRIPT_DIR)/config.yaml | grep -v '^\s*$$' > $(SENTINEL)
	@echo "==> Image saved to $(SCRIPT_DIR)/researcher-deskless.tar.gz"

check-rebuild:
	@CURRENT=$$(grep -v '^\s*#' $(SCRIPT_DIR)/config.yaml | grep -v '^\s*$$'); \
	LAST=$$(cat $(SENTINEL) 2>/dev/null || echo ''); \
	if [ "$$CURRENT" != "$$LAST" ]; then \
		echo "==> List of apps in config.yaml changed, rebuilding..."; \
		$(MAKE) build; \
	else \
		echo "==> List of apps in config.yaml unchanged, skipping rebuild."; \
	fi

run: check-rebuild
	@if ! docker image inspect researcher-deskless:latest &>/dev/null; then \
		if [ -f $(SCRIPT_DIR)/researcher-deskless.tar.gz ]; then \
			echo "==> Loading image..."; \
			docker load < $(SCRIPT_DIR)/researcher-deskless.tar.gz; \
		else \
			echo "ERROR: image not loaded and researcher-deskless.tar.gz not found. Run 'make build' first."; \
			exit 1; \
		fi \
	fi
	xhost +local:docker
	PUID=$(PUID) PGID=$(PGID) docker compose up && PUID=$(PUID) PGID=$(PGID) docker compose down

.DEFAULT_GOAL := help