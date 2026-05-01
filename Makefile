SCRIPT_DIR := $(shell pwd)
PUID := $(shell id -u)
PGID := $(shell id -g)
DATA_DIR := data

.PHONY: help run build

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  run     Load image from tar if needed and start Zotero"
	@echo "  build   Build the Docker image and save it to zotero.tar.gz"
	@echo "  help    Show this help message"

run:
	@if [ ! -d "$(DATA_DIR)" ]; then \
		mkdir -p "$(DATA_DIR)"; \
	fi
	@if ! docker image inspect zotero-portable:latest &>/dev/null; then \
		if [ -f $(SCRIPT_DIR)/zotero.tar.gz ]; then \
			echo "Loading Zotero image from tar..."; \
			docker load < $(SCRIPT_DIR)/zotero.tar.gz; \
		else \
			echo "Error: image not loaded and zotero.tar.gz not found. Run 'make build' first."; \
			exit 1; \
		fi \
	fi
	xhost +local:docker
	PUID=$(PUID) PGID=$(PGID) docker compose up && PUID=$(PUID) PGID=$(PGID) docker compose down

build:
	PUID=$(PUID) PGID=$(PGID) docker compose build --no-cache
	docker save zotero-portable | gzip > $(SCRIPT_DIR)/zotero.tar.gz
	@echo "Image saved to $(SCRIPT_DIR)/zotero.tar.gz"

.DEFAULT_GOAL := help