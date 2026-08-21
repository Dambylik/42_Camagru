# Camagru — Build & Study Plan

A step-by-step to-do list to deliver Camagru, with a learning plan per step.
Stack chosen to match the subject: **PHP (server) + plain HTML/CSS/JS (client) + MySQL/MariaDB + Docker Compose**.
Rule to remember all the way through: **no errors/warnings in any console (server or client)**, **secrets in `.env` (gitignored)**, **no framework that isn't in the PHP standard library**, **CSS frameworks OK if they add no JS**.

Legend for each step:
- **Do** — the concrete task
- **Learn** — concepts to study before/while doing it
- **Check** — what to verify works / test manually
- **Best practice** — the professional habit to build

---

## Phase 0 — Foundations & environment

### 0.1 Set up the repo and Docker
- **Do:** `git init` (already done). Create `docker-compose.yml` with 3 services: `web` (PHP + Apache or PHP built-in server), `db` (MySQL/MariaDB), optionally `mailpit` (fake SMTP for testing emails). One command deploy: `docker compose up`.
- **Learn:** What a container/image is; `docker-compose.yml` structure (services, ports, volumes, environment, depends_on); how containers talk over the compose network by service name (`db`, not `localhost`).
- **Check:** `docker compose up` starts everything; PHP page loads at `localhost:8000`; PHP can connect to `db`.
- **Best practice:** Never bake credentials into the image. Pass DB creds via `environment:` from `.env`. Use named volumes so DB data survives restarts.

### 0.2 `.env` and secrets
- **Do:** Create `.env` (DB name/user/password, app URL, SMTP settings, an app secret). Add `.env` to `.gitignore`. Commit a `.env.example` with empty/placeholder values.
- **Learn:** Why secrets never go in git; how PHP reads env (`getenv()` / `$_ENV`); the difference between build-time and run-time config.
- **Check:** `git status` never shows `.env`. Fresh clone + copy `.env.example` → `.env` boots the app.
- **Best practice:** "Publicly stored credentials = automatic project failure" (subject). Rotate anything you accidentally commit.

### 0.3 Project skeleton (MVC)
- **Do:** Create folders: `public/` (single entry `index.php` = front controller), `app/controllers`, `app/models`, `app/views`, `app/core` (router, DB, helpers), `sql/` (schema), `config/`.
- **Learn:** What MVC means (Model = data/DB, View = HTML output, Controller = request handling); the **front controller** pattern (all requests hit `index.php`, which routes).
- **Check:** A hard-coded route like `/` renders a view through the controller→view path.
- **Best practice:** Keep business logic out of views. Views only display data handed to them.

---

## Phase 1 — Core plumbing

### 1.1 Router
- **Do:** Small router mapping `METHOD + path` → controller method (e.g. `GET /login`, `POST /login`). Point Apache/PHP to rewrite everything to `public/index.php`.
- **Learn:** HTTP methods (GET vs POST), URL routing, `$_SERVER['REQUEST_METHOD']` and `REQUEST_URI`, Apache `mod_rewrite` or PHP built-in server routing.
- **Check:** Unknown route returns a 404 page, not a crash.
- **Best practice:** Route table in one place; controllers stay thin.

### 1.2 Database connection (PDO)
- **Do:** A `Database` class using **PDO** with prepared statements. Read creds from env.
- **Learn:** **PDO vs mysqli**; why **prepared statements** prevent SQL injection; connection error handling; `PDO::ERRMODE_EXCEPTION`.
- **Check:** A test query returns rows; wrong password fails gracefully (no stack trace to the user).
- **Best practice:** **Never** concatenate user input into SQL. Always bind parameters. This is one of the mandatory security points.

### 1.3 Database schema
- **Do:** Write `sql/schema.sql`: tables `users`, `images`, `likes`, `comments`, `overlays` (superposable images). Auto-load on first DB boot.
- **Learn:** Primary keys, foreign keys, indexes, `created_at` timestamps, one-to-many (user→images) and many-to-many (user↔likes) relationships, `UNIQUE` on email/username.
- **Check:** Schema loads clean; foreign keys enforced; a like can't be duplicated by the same user on the same image (composite unique key).
- **Best practice:** Model relationships in the DB, not in app code. Let the DB enforce uniqueness and referential integrity.

---

## Phase 2 — Authentication & user features (V.2)

### 2.1 Sign up
- **Do:** Registration form: email, username, password (with complexity rule). Store user with **hashed** password and an `is_verified = 0` flag + a random confirmation token.
- **Learn:** `password_hash()` / `password_verify()` (bcrypt); password complexity validation (length + mix); server-side vs client-side validation (client is convenience, **server is the real gate**); `filter_var($email, FILTER_VALIDATE_EMAIL)`.
- **Check:** Weak password rejected server-side even if you bypass the JS. Password never stored in plain text (look in DB). Duplicate email/username rejected.
- **Best practice:** Validate and sanitize **every** input at the server boundary. Passwords: hash, never encrypt, never log.

### 2.2 Email confirmation
- **Do:** On signup, email a unique link (`/confirm?token=...`). Clicking it sets `is_verified = 1`. Block login until verified.
- **Learn:** Generating secure random tokens (`random_bytes()` + `bin2hex()`); sending mail from PHP (`mail()` or PHPMailer-as-library check — but subject wants stdlib equivalents; Mailpit for local testing); token expiry.
- **Check:** Unverified user cannot log in. Token works once. Tampered token fails.
- **Best practice:** Tokens must be unguessable (cryptographically random), single-use, and time-limited.

### 2.3 Login / logout / sessions
- **Do:** Login by username+password → start a PHP session. Logout button on every page, one click, destroys session.
- **Learn:** PHP sessions (`session_start()`, `$_SESSION`, `session_destroy()`); cookies; session fixation; why you regenerate the session ID on login (`session_regenerate_id(true)`).
- **Check:** Wrong password fails. Logout works from any page. Protected pages redirect to login when logged out.
- **Best practice:** Regenerate session ID at login. Set cookie flags `HttpOnly` (and `Secure` when on HTTPS).

### 2.4 Password reset
- **Do:** "Forgot password" → email a reset link with a token → form to set a new password.
- **Learn:** Same token pattern as 2.2; don't reveal whether an email exists (avoid user enumeration).
- **Check:** Reset link changes the password; old password stops working; token is single-use.
- **Best practice:** Same neutral message whether or not the email exists.

### 2.5 Edit profile
- **Do:** Logged-in user can change username, email, password.
- **Learn:** CSRF protection (see 2.6) matters most here — a form that changes "private data."
- **Check:** Changing email/username enforces uniqueness. Changing password re-hashes.
- **Best practice:** Re-validate everything on update, not just on create.

### 2.6 CSRF protection (applies to ALL forms — do this now)
- **Do:** Generate a CSRF token per session, embed it as a hidden field in every form, verify it on every POST.
- **Learn:** **What CSRF is** (subject explicitly lists it — "Use an extern form to manipulate private data"); the synchronizer token pattern; SameSite cookies.
- **Check:** A POST without/with a wrong token is rejected. Submitting your form from another origin fails.
- **Best practice:** Every state-changing request (POST/PUT/DELETE) must carry and verify a CSRF token.

---

## Phase 3 — Layout & responsive design (V.1)

### 3.1 Base layout
- **Do:** Shared header / main / footer template. Header shows login/logout/profile depending on auth state.
- **Learn:** Template partials in PHP (`include`), semantic HTML (`<header> <main> <footer> <nav>`).
- **Check:** Every page has header/main/footer; nav reflects auth state.
- **Best practice:** One layout, pages fill the `main`. Don't repeat the header in every file.

### 3.2 Responsive CSS
- **Do:** Make it work on mobile and small screens. Editing page follows the Figure V.1 layout (main + side).
- **Learn:** The **viewport meta tag**, CSS media queries, Flexbox/Grid, mobile-first CSS. A CSS framework (e.g. a classless one, or Bootstrap CSS-only) is allowed **only if it adds no JS**.
- **Check:** Resize the browser narrow — layout adapts, nothing overflows, side section stacks on mobile.
- **Best practice:** Mobile-first; test at real breakpoints; relative units (`rem`, `%`, `fr`) over fixed pixels.

---

## Phase 4 — Editing features (V.4) — the heart of the project

### 4.1 Access control
- **Do:** Editing page only for authenticated users; politely reject others (redirect to login with a message).
- **Learn:** Authorization guard/middleware pattern; checking `$_SESSION` at the top of protected controllers.
- **Check:** Logged-out access to `/editor` redirects, does not error.
- **Best practice:** Guard on the **server**, not by hiding a link. Never trust the client.

### 4.2 Webcam preview
- **Do:** Main section shows live webcam via `getUserMedia()` in a `<video>`, plus the list of selectable overlay images and a capture button.
- **Learn:** `navigator.mediaDevices.getUserMedia()`, `<video>`, drawing a frame to `<canvas>` and exporting via `toDataURL()`; DOM manipulation with vanilla JS (subject lists "DOM Manipulation" as a learning goal).
- **Check:** Webcam preview shows. (Note: `getUserMedia` errors over plain HTTP are **tolerated** by the subject.)
- **Best practice:** Feature-detect the API; handle "no camera / denied" gracefully.

### 4.3 Overlay selection + capture gating
- **Do:** Overlay thumbnails are selectable. **Capture button stays disabled until an overlay is selected.**
- **Learn:** DOM event handling, toggling `disabled`, tracking selected state.
- **Check:** Button is unclickable with nothing selected; enables on selection. Verify server-side too (reject a capture with no overlay).
- **Best practice:** Enforce the "overlay required" rule on the server as well — client gating is UX, not security.

### 4.4 Upload fallback
- **Do:** Allow uploading an image file instead of using the webcam.
- **Learn:** `<input type="file">`, `$_FILES`, MIME/type checking, size limits.
- **Check:** Only real images accepted; a renamed `.php` or oversized file is rejected. (Subject: "Offer the ability to upload unwanted content on the server" = NOT secure.)
- **Best practice:** Validate type by content (`getimagesize`/`finfo`), not just extension. Store with a generated filename, never the user's. Keep uploads out of an executable path.

### 4.5 Server-side image compositing
- **Do:** **On the server**, superimpose the selected overlay (with alpha channel) onto the captured/uploaded image → save final PNG.
- **Learn:** PHP **GD library** (`imagecreatefrompng`, `imagecopy`/`imagecopyresampled`, alpha blending, `imagesavealpha`, `imagepng`); why the overlays need an alpha channel (subject's note).
- **Check:** Final image visibly merges both; transparency preserved; saved to disk + recorded in DB with author + timestamp.
- **Best practice:** Compositing MUST be server-side (subject requirement). Handle image errors without leaking paths.

### 4.6 Thumbnails + delete own images
- **Do:** Side section shows thumbnails of the user's previous pictures. User can delete **only their own** images.
- **Learn:** Query by owner; authorization check on delete (ownership); deleting both DB row and file.
- **Check:** You can delete your own image; you **cannot** delete someone else's (test by forging an ID in the request).
- **Best practice:** Always re-check ownership on the server for delete/edit — never trust the ID sent by the client.

---

## Phase 5 — Gallery features (V.3)

### 5.1 Public gallery + pagination
- **Do:** Public page listing ALL users' images, newest first, paginated (≥5 per page).
- **Learn:** SQL `ORDER BY created_at DESC` with `LIMIT`/`OFFSET`; building page links; escaping output.
- **Check:** Non-logged-in visitors see the gallery. Pagination navigates correctly; edge pages don't break.
- **Best practice:** **Escape everything on output** with `htmlspecialchars()` to prevent XSS (subject: injecting HTML/JS = NOT secure).

### 5.2 Likes & comments (logged-in only)
- **Do:** Connected users can like and comment images. Guests can view but not interact.
- **Learn:** Many-to-many likes (unique per user+image, toggle), comment insert with author + timestamp, CSRF on these POSTs, output escaping on comments.
- **Check:** A guest can't like/comment. A user can't like twice. A comment containing `<script>` renders as text, not code.
- **Best practice:** This is the classic XSS trap — never render user text as raw HTML.

### 5.3 Comment email notification + preference
- **Do:** When an image gets a new comment, email the image's author. Preference **defaults ON**, toggleable in user settings.
- **Learn:** Reading a user preference flag; sending mail on an event; testing with Mailpit.
- **Check:** Author gets email on new comment; turning the preference off stops emails; default is on for new users.
- **Best practice:** Respect the notification preference everywhere it's checked; test the toggle both ways.

---

## Phase 6 — Security hardening pass (mandatory)

Go back through everything against the subject's NOT-secure list:
- **Passwords:** hashed (`password_hash`) — verify in DB. ✅ Phase 2.1
- **XSS:** all user output escaped (`htmlspecialchars`). ✅ Phase 5
- **Uploads:** type/size validated, safe filenames, non-executable storage. ✅ Phase 4.4
- **SQL injection:** 100% prepared statements. ✅ Phase 1.2
- **CSRF / external form manipulation:** tokens on all state-changing forms. ✅ Phase 2.6
- **Learn:** OWASP Top 10 basics; defense in depth; least privilege (DB user needs only what it uses).
- **Check:** Try to break your own app: submit a form from a separate HTML file, inject `<script>` in a comment, forge another user's image ID on delete, put `' OR 1=1 --` in a login field, upload a `.php`.
- **Best practice:** Assume all input is hostile. Validate on input, escape on output, authorize on the server.

---

## Phase 7 — Polish & submission (IV, VII)

### 7.1 Zero console noise
- **Do:** Fix every PHP notice/warning and every JS console error/warning (except tolerated `getUserMedia` HTTP errors).
- **Learn:** PHP error reporting settings; reading the browser dev-tools console.
- **Check:** Open dev tools on every page — clean. Check server logs — clean.
- **Best practice:** A warning is a bug you haven't been bitten by yet. Zero-warning is a graded requirement here.

### 7.2 Cross-browser
- **Do:** Test on Firefox (≥41) and Chrome (≥46).
- **Check:** Signup→confirm→login→edit→gallery→comment→logout works end-to-end in both.

### 7.3 One-command deploy check
- **Do:** From a clean clone: copy `.env.example`→`.env`, run `docker compose up`. Everything works.
- **Check:** No manual steps beyond that. DB schema auto-loads.
- **Best practice:** If a fresh clone doesn't boot with one command, it's not done.

### 7.4 Submit
- **Do:** Everything committed to git (never `.env`). Double-check file/folder names. Confirm `.gitignore` covers `.env`, uploads if generated, `vendor/` if any.
- **Best practice:** Only what's in the repo is graded. Do a fresh clone in a temp dir and defend against *that*.

---

## Phase 8 — Bonus (only if mandatory part is PERFECT — see subject)

Do NOT touch these until the mandatory part is complete and bug-free (bonus is only assessed if mandatory is perfect):
- **AJAXify** exchanges with the server → learn `fetch()`, JSON responses, updating DOM without reload.
- **Live preview** of the edit on the webcam feed → canvas overlay in real time (subject says easier than it looks).
- **Infinite scroll** pagination for the gallery → `IntersectionObserver`.
- **Share to social networks** → Open Graph meta tags, share URLs.
- **Animated GIF** render.

---

## Suggested study order (fastest path to competence)
1. Docker Compose basics → boot PHP + MySQL.
2. PHP + PDO + prepared statements.
3. Sessions & `password_hash`.
4. HTTP/forms/validation, then CSRF & XSS.
5. `getUserMedia` + canvas (client) and GD (server).
6. Responsive CSS (Flexbox/Grid + media queries).

Build in the phase order above; study each topic the day you need it, not all upfront.
