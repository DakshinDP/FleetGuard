.PHONY: up down logs ps build clean
up:
	@test -f .env || cp .env.example .env
	docker compose up --build
down:
	docker compose down
logs:
	docker compose logs -f --tail=200
ps:
	docker compose ps
build:
	docker compose build
clean:
	docker compose down -v
