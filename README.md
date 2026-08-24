# Camagru

A small web app for webcam/photo editing (42 project). PHP standard library
only, Docker for one-command deploy.

## Run it

```bash
make        # copies .env from the template on first run, then builds + starts
```

- App:     http://localhost:8000
- Mailpit: http://localhost:8025  (read the emails the app "sends")

Common `make` targets: `up` (default), `down`, `re` (full reset, wipes the DB),
`logs`, `ps`, `db` (MariaDB shell), `clean` / `fclean`. Plain
`docker compose up --build` still works if you prefer.

## Stack

- **PHP 8.2 + Apache** — with `pdo_mysql` (talk to the DB) and `gd` (image editing).
- **MariaDB 11** — the database.
- **Mailpit** — catches outgoing mail in dev so you can read confirmation /
  notification emails without a real SMTP server.

Wiring lives in `docker-compose.yml` (services, ports, volumes) and `Dockerfile`
(the PHP image + extensions). `config/apache.conf` sets the web root to
`public/` so the rest of the source stays out of reach of the browser. The web
container gets `DB_HOST/NAME/USER/PASSWORD` from env; `sql/schema.sql` is
mounted into the db container's init dir and runs on first boot.

## Layout

```
public/          the ONLY web-served folder
  index.php      front controller — the single entry point
app/             application code, NOT reachable from the browser
  core/
    Router.php   maps "METHOD + ?page=" -> a controller method
    Database.php single PDO connection (prepared statements, creds from env)
  controllers/   handle a request, call models, pick a view
    AuthController.php   login / logout (stubs)
    FeedController.php   home / gallery (currently a smoke test + DB check)
  models/        DB / data classes (empty — User, Image, Comment go here)
  views/         HTML templates (empty — inline in controllers for now)
config/apache.conf   Apache vhost: DocumentRoot = public/
sql/schema.sql       tables; auto-loaded by MariaDB on first boot
Makefile             docker compose shortcuts (see "Run it")
```

## How a request flows

1. Every URL is `public/index.php?page=...` (e.g. `index.php?page=login`).
   Serving only `public/` keeps `app/`, `.env`, and `sql/` unreachable — a
   security requirement of the subject.
2. `index.php` starts the session, loads the router, registers routes, then
   calls `dispatch($_SERVER['REQUEST_METHOD'], $_GET['page'] ?? 'home')`.
3. The **Router** looks up `"METHOD page"` (e.g. `GET login`) and finds the
   handler `['AuthController', 'showLogin']`.
4. It loads that controller and runs the method. The **controller** asks a
   **model** for data and renders a **view**.

Routing is query-string based (`?page=login`), not clean URLs — chosen for
simplicity. To switch to clean URLs later, add a `public/.htaccess` rewrite +
`a2enmod rewrite` and route on the path instead of `?page=`.

## MVC in one screen

Separation of concerns — change the DB and the HTML is untouched, and vice versa.

- **Model** (data layer) — the only part that talks to MySQL. Runs queries,
  returns raw data. Never outputs HTML.
- **View** (presentation) — takes data the controller hands it and renders
  HTML. "Dumb": no business logic, no queries.
- **Controller** (traffic cop) — receives the HTTP request, asks the model to
  do the work, tells the view what to render. Stays thin.
- **Front controller** — one entry point (`public/index.php`). Everything
  funnels through it, so session start, `.env` loading, and DB setup happen
  once instead of being duplicated across dozens of files.

## Status

Foundation done (study-plan phase 1): front controller + `?page=` router,
`Database` PDO connection with prepared statements + graceful failure, and the
full schema (`users`, `overlays`, `images`, `comments`, `likes`) with foreign
keys, unique constraints, and cascade deletes verified. Controllers are still
stubs and `models/`, `views/` are empty. The home page (`FeedController::index`)
prints a smoke test confirming `gd`, `pdo_mysql`, and a live DB query.

Reloading the schema: it only runs on the DB's **first** boot, so after editing
`sql/schema.sql` run `make re` (drops the DB volume and rebuilds).

## Notes — PDO & prepared statements

**PDO vs mysqli:** mysqli is designed exclusively for MySQL databases. PDO (PHP
Data Objects) is a versatile interface that supports multiple database systems.
It is generally preferred because it provides a consistent method for
interacting with databases regardless of which one you use.

**Prepared statements & SQL injection:** SQL injection occurs when malicious
user input is accidentally executed as database commands. Prepared statements
prevent this by completely separating the SQL query structure from the user
data — you send the SQL template to the database first, then supply the user
data separately as parameters. The database treats the input strictly as
literal text, never as executable code, neutralizing the attack.

## Notes — the schema, told as a story

**Users table (primary keys & UNIQUE)**
- *Primary key:* Alice registers an account. The database assigns her a
  permanent, unique ID: `id = 1`. Bob registers and gets `id = 2`.
- *UNIQUE:* Alice registers with `alice@email.com` / username `alice_art`. If
  Bob tries to register with `alice@email.com`, the database blocks it instantly.

**Images table (one-to-many, foreign keys, timestamps)**
- *One-to-many:* Alice uploads three pictures. One user, multiple pictures.
- *Foreign key:* Each picture's row stores `user_id = 1` (Alice's primary key).
  That connection is the foreign key proving she owns them.
- *created_at:* When Alice's first picture (`image_id = 10`) is saved, this
  column auto-records e.g. `2026-08-24 11:47:00`. Used to sort the gallery
  newest-first.

**Speeding it up (indexes)**
- *Index:* Viewing Alice's profile asks for "all images where `user_id = 1`".
  With an index on `user_id`, the database jumps straight to her three pictures
  instead of scanning thousands of other uploads.

**Likes table (many-to-many & composite keys)**
- *Many-to-many:* Bob (`id = 2`) likes Alice's picture (`image_id = 10`). Anyone
  can like many pictures — this can't live in the users or images table.
- *Junction table:* A third table `likes` stores `user_id = 2, image_id = 10`
  per like.
- *Double-like problem:* A UNIQUE rule on the combination `(user_id, image_id)`
  physically rejects a second row with `2, 10` — one like per user per image.