# Camagru — thin wrapper over docker compose. `make` brings the stack up.
.DEFAULT_GOAL := up
.PHONY: up build down re logs ps db clean fclean overlays

up: .env          ## build if needed and start (app :8000, mailpit :8025)
	docker compose up --build -d

build: .env       ## build images without starting
	docker compose build

down:             ## stop and remove containers (keeps DB data)
	docker compose down

re: fclean up     ## full reset: wipe DB volume, then rebuild from scratch

logs:             ## follow all container logs
	docker compose logs -f

ps:               ## show container status
	docker compose ps

overlays:         ## generate placeholder overlay PNGs inside the web container
	docker compose exec web php /var/www/html/sql/make_overlays.php

db:               ## open a MariaDB shell in the db container
	docker compose exec db sh -c 'exec mariadb -u"$$MYSQL_USER" -p"$$MYSQL_PASSWORD" "$$MYSQL_DATABASE"'

clean: down       ## stop containers and drop volumes (DB data lost)
	docker compose down -v

fclean: clean     ## clean + remove built images
	docker compose down -v --rmi local

# Create .env from the template on first run so `up` never fails silently.
.env:
	cp .env.example .env
	@echo ">> Created .env from .env.example — edit the credentials before going to prod."
