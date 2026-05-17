SCRIPT_DIR := $(shell pwd)

HOST_UID := $(shell id -u)
HOST_GID := $(shell id -g)

HOST_DISPLAY := $(DISPLAY)
HOST_XAUTHORITY := $(XAUTHORITY)

PUID := 1000 #$(shell id -u)
PGID := 1000 #$(shell id -g)
SENTINEL := $(SCRIPT_DIR)/.last-build

VERSION := $(shell git rev-parse --short HEAD)

SHELL_PREFIX := PUID=$(PUID) PGID=$(PGID) VERSION=$(VERSION) HOST_UID=$(HOST_UID) HOST_GID=$(HOST_GID) HOST_DISPLAY=$(HOST_DISPLAY) HOST_XAUTHORITY=$(HOST_XAUTHORITY)

.PHONY: help run build generate check-rebuild

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  run       Build if config changed, then start the launcher"
	@echo "  build     Generate compose, build image and save to tar"
	@echo "  generate  Generate compose.yaml from config.yaml"
	@echo "  help      Show this help message"

generate:
	@echo "==> Generating compose.yaml..."
	@python3 $(SCRIPT_DIR)/utils/generate-compose.py

build: generate
	mkdir -p ./data
	$(SHELL_PREFIX) docker compose build
	docker save researcher-deskless:$(VERSION) | gzip > $(SCRIPT_DIR)/researcher-deskless-$(VERSION).tar.gz
	@grep -v '^\s*#' $(SCRIPT_DIR)/config.yaml | grep -v '^\s*$$' > $(SENTINEL)
	@echo "==> Image saved to $(SCRIPT_DIR)/researcher-deskless-$(VERSION).tar.gz"

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
	mkdir -p data/
	@if ! docker image inspect researcher-deskless:$(VERSION) &>/dev/null; then \
		if [ -f $(SCRIPT_DIR)/researcher-deskless-$(VERSION).tar.gz ]; then \
			echo "==> Loading image..."; \
			docker load < $(SCRIPT_DIR)/researcher-deskless-$(VERSION).tar.gz; \
		else \
			echo "ERROR: image not loaded and researcher-deskless-$(VERSION).tar.gz not found. Run 'make build' first."; \
			exit 1; \
		fi \
	fi
	xhost +local:docker
	$(SHELL_PREFIX) docker compose up && $(SHELL_PREFIX) docker compose down

.DEFAULT_GOAL := help
