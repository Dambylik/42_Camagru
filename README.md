# 🐱 Camagrrru

A webcam/photo editing web app. PHP only, no frameworks, no composer, no npm. Docker for one-command deploy.

## Run it

```bash
make        # copies .env from the template on first run, then builds + starts
make re     # full reset — wipes the DB volume and rebuilds (use after schema changes)
```

- App:     http://localhost:8000
- Mailpit: http://localhost:8025 (read confirmation / notification emails)

Other `make` targets: `down`, `logs`, `ps`, `db` (MariaDB shell), `clean` / `fclean`.

## Stack

- **PHP 8.2 + Apache** — `pdo_mysql` (DB), `gd` (image compositing), `msmtp` (mail).
- **MariaDB 11** — database, schema auto-loaded on first boot.
- **Mailpit** — catches all outgoing mail in dev.

## Layout

```
public/               the ONLY web-served folder
  index.php           front controller — single entry point
  css/app.css         all styles
  uploads/            user-generated images (gitignored except .gitkeep)
  overlays/           sticker PNGs
  cat-cartoon.png     logo
config/
  database.php        Database class — PDO singleton (ERRMODE_EXCEPTION)
  setup.php           bootstrap: .env loading + session_start()
  apache.conf         DocumentRoot = public/
  msmtp.conf          routes mail to Mailpit:1025
app/
  core/
    Router.php        maps "METHOD + ?page=" -> [Controller, method]
    Database.php      requires config/database.php
    Csrf.php          token generation + hash_equals verify
    Mailer.php        wraps mail(), reads MAIL_FROM from env
  controllers/
    AuthController.php   register / confirm / login / logout / forgot / reset / profile
    FeedController.php   gallery / like-ajax / comment-ajax / gallery-json
    EditorController.php show / capture / delete
  models/
    User.php          all user DB operations
    Image.php         images, overlays, likes
    Comment.php       comments
  views/
    partials/
      header.php      nav + <head>, shared across all pages
      footer.php      closes main/body/html
    gallery.php       public gallery with infinite scroll + AJAX likes/comments
    editor.php        webcam/upload editor with sticker compositing
    login.php / register.php / forgot.php / reset.php / profile.php
    register_done.php / 404.php / error.php
sql/
  schema.sql          5 tables: users, overlays, images, comments, likes
  seeds.sql           6 cat overlays
Dockerfile            PHP+Apache image, msmtp, gd, pdo_mysql
docker-compose.yml    web / db / mailpit services
Makefile              shortcuts
.env.example          template — copy to .env and fill in
```

## How a request flows

1. Every URL is `?page=X` (e.g. `index.php?page=login`). Only `public/` is web-accessible — `app/`, `config/`, `.env`, `sql/` are unreachable from the browser.
2. `index.php` requires `config/setup.php` (loads `.env` + starts session), then dispatches via `Router`.
3. The **Router** matches `"METHOD page"` to `[Controller, method]`, loads the controller file and calls the method.
4. The **controller** calls **models** (PDO prepared statements) and renders a **view**.

## Features

### Auth
- Register with username / email / bcrypt password (min 8 chars, uppercase, digit, special char)
- Email confirmation with unique token (24h expiry) — can't log in until confirmed
- Login with session regeneration on privilege change
- Password reset via email (1h token, single-use)
- Profile: update username / email / password / email notification preference
- CSRF protection on all POST forms (`hash_equals` timing-safe verify)

### Gallery (public)
- All images ordered by creation date, 5 per page
- **Infinite scroll** — next page loads automatically as you scroll down
- **AJAX likes** — toggle without page reload
- **AJAX comments** — post and appear instantly, no reload
- Email notification to image owner on new comment (if preference enabled)
- Guests can view; only logged-in users can like/comment

### Editor (login required)
- Live webcam preview on canvas (`requestAnimationFrame` loop)
- Upload a photo instead of webcam — loads onto canvas client-side
- Pick cat stickers from the overlay panel — click to add, multiple stickers supported
- Each sticker is **draggable** and **resizable from any corner**
- Capture sends base64 + sticker positions to server
- Server-side GD compositing: resizes base to 600×600, composites each sticker at user-specified position/size
- Zero stickers, one sticker, or many — all handled
- Thumbnail grid of your own images with delete (ownership enforced server-side)

## Security
- All DB queries use PDO prepared statements — no SQL injection possible
- `PDO::ATTR_EMULATE_PREPARES => false` — real server-side prepared statements
- All user output escaped with `htmlspecialchars()` — no XSS
- Passwords stored as bcrypt hashes — never plain text
- CSRF tokens on all POST forms — `hash_equals` prevents timing attacks
- Ownership checked server-side before delete — 403 if mismatch
- No user enumeration on login (same error for wrong user or wrong password)
- `app/`, `config/`, `.env`, `sql/` outside web root — not browser-accessible

## Bonuses
1. **Draggable stickers** — move any sticker anywhere on the canvas
2. **Resizable stickers from any corner** — drag any of the 4 corner handles
3. **Upload flow** — photo loads client-side onto canvas before capture, overlay positioning works on uploads too
4. **Multiple stickers** — add as many overlays as you want, each independently positioned
5. **Infinite scroll** — gallery loads more images automatically on scroll

## Browser compatibility
Tested against Firefox ≥ 41 and Chrome ≥ 46. No `aspect-ratio`, no CSS grid, no `fetch`, no `{ once }` event option — all replaced with compatible equivalents.
