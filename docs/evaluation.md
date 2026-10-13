# Evaluation preparation — Version 4.1

Use `en.subject.camagru.pdf` as the requirements reference, not the 2018 scale.
Require code evidence and runtime verification before marking an item passed.

## Startup and layout

- Start a fresh checkout with `make up` after Docker is running.
- Verify health, homepage, header/main/footer, assets, browser console and the private error log.
- Use clean Chrome/Firefox profiles to exclude extension errors.
- Test 375px mobile width and inspect overlap/overflow.
- Keep `.env` ignored and inspect submitted files for real credentials.

## Accounts

- Reject missing/invalid username/email and weak passwords in browser and backend.
- Register and inspect the actual Mailpit email. Unconfirmed login must fail.
- Confirm, then log in. Altered/expired/reused confirmation tokens must fail.
- Request reset and inspect its email. Strong new password works; old password/session and reused link fail.
- Logout from every view; protected pages require login afterward.
- Change username/email/password and verify subsequent login and stored data.
- Email changes need current password and confirmation; security changes revoke other sessions.

## Gallery

- Public browsing; only authenticated users can like/comment, including direct requests.
- Newest first, five images per page, working next page/infinite scroll.
- Likes toggle; comments show escaped text, including attempted XSS.
- Comment email enabled by default; disabling preference prevents delivery.

## Editor

- Anonymous access redirects to login.
- Webcam preview, overlays, capture, uploaded alternative, previous-photo thumbnails.
- Require base media and overlay in UI and server checks, per V.4.
- One/multiple overlays, drag/resize/removal, actual server-composed saved pixels.
- Reject invalid/oversized image data and unknown overlays; enforce deletion ownership.

## Security and bonuses

- Hash passwords, parameterize SQL, escape HTML and validate every form.
- Reject missing/wrong CSRF, hostile Origin headers and source/credential access.
- Controlled errors must not expose tracebacks, SQL or filesystem paths.
- Assess bonuses only once mandatory features are fully verified.

`make test` runs temporary-account backend checks. `node tests/ui-regressions.cjs` checks
editor resize/gallery retries. `tests/browser-smoke.cjs` needs a separate Playwright test
environment; it is not an application dependency. Actual webcam hardware and historical
Firefox 41/Chrome 46 remain manual verification tasks.

Migration verification: Chrome smoke and mobile layout passed. Headless Firefox on this
host could not launch because macOS denied sandbox extensions and framebuffer mapping;
that is an unverified check, not a passing Firefox result.
