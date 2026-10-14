# 复用项目已有 .env；Windows PowerShell 可直接执行等价的 Compose 命令。
DOCKER_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_ROOT := $(abspath $(DOCKER_DIR)/..)
COMPOSE = docker compose --env-file "$(PROJECT_ROOT)/.env" -f "$(DOCKER_DIR)docker-compose.yml"

.PHONY: help config build up down logs ps superuser check push-multi

help:
	@echo "config build up down logs ps superuser check push-multi"
	@echo "From project root, Windows PowerShell: docker compose --env-file .env -f docker/docker-compose.yml up -d --build"

config:
	$(COMPOSE) config --quiet

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

ps:
	$(COMPOSE) ps -a

superuser:
	$(COMPOSE) exec testhub python manage.py createsuperuser

check:
	$(COMPOSE) exec testhub python manage.py check
	$(COMPOSE) exec testhub python manage.py migrate --check

push-multi:
	bash "$(DOCKER_DIR)build-multiplatform.sh" --push
