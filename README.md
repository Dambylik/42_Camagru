# Camagrrru

Framework-free Python 3.10 application following `en.subject.camagru.pdf`, Version 4.1.
The 2018 evaluation sheet is historical reference only.

## Start

Install/start Docker Desktop, then run from this folder:

```sh
docker desktop start
make up
```

Open http://localhost:8000. Development emails appear at http://localhost:8025.
`make up` builds the image and starts the Python web server, MariaDB and Mailpit.
A missing `.env` is generated with random database passwords by `config/create_env.py`
(Python 3 on the host). Existing credentials and persistent volumes are preserved.
Copying `.env.example` is also possible, but replace its example passwords before startup.
No npm or Composer installation is needed to run the application.

## Architecture

- `backend/server.py`: native HTTP server, request parsing, static-file allowlist, security headers and bounded concurrency.
- `backend/application.py`: routes and application behavior.
- `backend/views.py`: HTML rendering; all dynamic text is escaped.
- `backend/db.py`: parameterized MariaDB queries; database failures raise exceptions.
- `backend/security.py`: bcrypt passwords, input validation, database-backed sessions, CSRF tokens and session rotation.
- `backend/imaging.py`: validates PNG data and composites overlays on the server using Pillow.
- `backend/mail.py`: SMTP messages using Python's standard library.
- `backend/bootstrap.py`: creates the sessions table and adds missing account-security columns without dropping data.
- `public/js/`: native browser JavaScript for the editor and AJAX gallery.
- `public/css/`, `public/overlays/`: the existing design and alpha-channel overlays.
- `sql/schema.sql`, `sql/seeds.sql`: initialize a new MariaDB volume.

MariaDB stores users, images, comments, likes, overlay metadata and sessions. Uploaded PNGs
are stored in the `uploads_data` volume. Existing PHP bcrypt accounts remain usable; users
must log in again because Python uses its own session cookie. Old `index.php?page=...`
links are handled by Python for compatibility; no PHP executable is involved.

Source changes in `backend/` are bind-mounted, but restart `web` to reload Python code:

```sh
docker compose restart web
```

Refresh for CSS/JS edits. Rebuild for dependency, Dockerfile or packaged asset changes.

## Subject requirements

- Registration validates username, email and password in both browser and server.
- A unique 24-hour email confirmation is needed before login.
- Reset links expire after one hour and are consumed after use.
- Profile supports username, password, confirmed email changes and notification preferences.
- Logout is a one-click POST button with CSRF protection on all normal application pages.
- The public gallery orders images newest first and paginates by five.
- Only authenticated users can like/comment or access the editor.
- Comment notification is enabled by default and can be disabled (including notifications for self-comments).
- Capture requires a ready base image AND a selected overlay, per V.4; server checks independently.
- Uploaded photos and webcam frames follow the same server-side composition path.
- Only owners can delete their pictures.
- CSRF, parameterized SQL, escaped HTML, bcrypt, secure random tokens, upload bounds and session revocation protect core flows.
- Native JavaScript retains live overlay preview, drag/resize and infinite gallery loading as bonuses.

See `docs/php-equivalents.md` for dependency/function equivalents and
`docs/evaluation.md` for a subject-based manual verification list.
No claim of universal security or historical browser-version coverage is made; these need actual evaluation.

## Verification and diagnostics

```sh
make test
node tests/ui-regressions.cjs
```

The Python integration test uses temporary accounts/photos in the running database and
removes those fixtures afterward. Test emails remain in Mailpit; existing accounts and images
are not deleted. Node is optional and used only for development regression tests.
The test covers authentication, reset, CSRF, SQL injection, HTML escaping, preferences,
server composition, ownership and pagination. Browser/SMTP checks are described separately.

Routine web access logs are disabled. Unexpected exceptions are recorded privately in
`/tmp/camagru-errors.log` inside `web` and return a generic error response to visitors.
An empty console does not prove the app has no failures: check this file and HTTP responses too.

```sh
docker compose logs --since=2m web
docker compose exec web sh -c 'test ! -s /tmp/camagru-errors.log'
```

Expected invalid input produces controlled 400/403 responses, not tracebacks. Docker/MariaDB
infrastructure messages are separate from application errors. Native Linux AIO is disabled in
MariaDB to avoid the unavailable io_uring path in Docker Desktop. Its memory-pressure facility
can still be unavailable in that environment; this is not a Python error.

`make down` keeps data. `make clean`, `make fclean` and `make re` DELETE the persistent
volumes and therefore your database/uploads. They are explicit reset commands.

The pre-migration working files were backed up at `/tmp/camagru-before-python.tar.gz`;
that temporary archive is not submitted and excludes `.env` and `.git`.
