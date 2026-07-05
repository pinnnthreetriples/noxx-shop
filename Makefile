.PHONY: up down migrate seed logs build backend-shell bot-shell

up:
	cd infra && docker-compose up -d --build

down:
	cd infra && docker-compose down

build:
	cd infra && docker-compose build

migrate:
	docker-compose -f infra/docker-compose.yml exec backend alembic upgrade head

migrate-generate:
	docker-compose -f infra/docker-compose.yml exec backend alembic revision --autogenerate -m "$(msg)"

seed:
	docker-compose -f infra/docker-compose.yml exec backend python -m scripts.seed

logs:
	docker-compose -f infra/docker-compose.yml logs -f

backend-shell:
	docker-compose -f infra/docker-compose.yml exec backend bash

bot-shell:
	docker-compose -f infra/docker-compose.yml exec bot bash

directus-shell:
	docker-compose -f infra/docker-compose.yml exec directus bash
