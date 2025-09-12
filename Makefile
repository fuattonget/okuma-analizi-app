.PHONY: up down logs api fe wk

# Start all services
up:
	docker compose up -d --build

# Stop all services
down:
	docker compose down

# View logs
logs:
	docker compose logs -f

# Access API container
api:
	docker compose exec api bash

# Access frontend container
fe:
	docker compose exec frontend bash

# Access worker container
wk:
	docker compose exec worker bash


