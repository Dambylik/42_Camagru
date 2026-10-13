"""HTML pages and shared form helpers. Escape all user-provided text."""

from html import escape

PASSWORD = (
    'required minlength="8" maxlength="72" '
    'pattern="(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{8,}"'
)
PASSWORD_HELP = (
    '<small class="form-help">'
    "8+ characters, uppercase, digit, special character"
    "</small>"
)
USER_ATTRS = 'required minlength="3" maxlength="30" pattern="[A-Za-z0-9_]{3,30}"'


def e(value):
    """Display a value as text, rather than executable HTML."""
    return escape(str(value), quote=True)


def csrf(token):
    return f'<input type="hidden" name="_csrf_token" value="{e(token)}">'


def field(name, label, kind="text", value="", attrs=""):
    return f"""
        <div class="form-group">
            <label>
                {e(label)}
                <input type="{kind}" name="{name}" value="{e(value)}" {attrs}>
            </label>
        </div>
    """


def form(page, token, content, button, extra="", button_class="btn btn-primary"):
    return f"""
        <form method="post" action="/?page={page}">
            {csrf(token)}
            {extra}
            {content}
            <button class="{button_class}" type="submit">{e(button)}</button>
        </form>
    """


def heading(title, description):
    return f"""
        <header class="page-heading">
            <span class="eyebrow">A little corner for cat lovers</span>
            <h1>{e(title)}</h1>
            <p>{e(description)}</p>
        </header>
    """


def layout(title, body, token, user=None, message="", error=False):
    page = title.lower()
    gallery_class = "active" if page == "home" else ""
    gallery_link = f'<a class="nav-link {gallery_class}" href="/?page=home">Gallery</a>'

    if user:
        studio_class = "active" if page == "editor" else ""
        profile_class = "active" if page == "profile" else ""
        links = (
            gallery_link
            + f'<a class="nav-link {studio_class}" href="/?page=editor">Studio</a>'
            + f'<a class="nav-link account-link {profile_class}" '
            f'href="/?page=profile">{e(user["username"])}</a>'
            + form("logout", token, "", "Log out")
        )
    else:
        login_class = "active" if page == "login" else ""
        register_class = "active" if page == "register" else ""
        links = (
            gallery_link
            + f'<a class="nav-link {login_class}" href="/?page=login">Log in</a>'
            + f'<a class="nav-link nav-join {register_class}" '
            'href="/?page=register">Join the club</a>'
        )

    notice = ""
    if message:
        alert_class = "error" if error else "success"
        notice = (
            f'<div role="status" class="alert alert-{alert_class}">'
            f"{e(message)}</div>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{e(title)} — Camagrrru</title>
    <link rel="stylesheet" href="/css/app.css?v=cat-club-2">
    <link rel="icon" href="/cat-cartoon.png">
</head>
<body>
    <a class="skip-link" href="#content">Skip to content</a>
    <nav aria-label="Main navigation">
        <div class="nav-inner">
            <a class="brand" href="/">
                <span class="brand-icon">
                    <img width="35" height="35" src="/cat-cartoon.png" alt="">
                </span>
                Camagrrru
                <span class="brand-heart" aria-hidden="true">♡</span>
            </a>
            <div class="nav-links">{links}</div>
        </div>
    </nav>
    <main id="content">{notice}{body}</main>
    <footer>
        <span aria-hidden="true">🐾</span>
        Made with love to cats.
        <span class="footer-brand">Camagrrru</span>
    </footer>
</body>
</html>"""


def error():
    page_heading = heading("A little snag", "Let’s get you back to the cozy corner.")
    return f"""
        <section class="auth-wrap">
            {page_heading}
            <div class="card centered-card">
                <img class="empty-cat" width="80" height="80"
                     src="/cat-cartoon.png" alt="A friendly illustrated cat">
                <a class="btn btn-primary" href="/?page=home">
                    Back to the gallery
                </a>
            </div>
        </section>
    """


def auth(page, token, values):
    username = field(
        "username",
        "Username",
        value=values.get("username", ""),
        attrs=USER_ATTRS + ' autocomplete="username"',
    )
    email = field(
        "email",
        "Email address",
        "email",
        values.get("email", ""),
        'required maxlength="255" autocomplete="email"',
    )
    password = (
        field(
            "password",
            "Password",
            "password",
            attrs=PASSWORD + ' autocomplete="new-password"',
        )
        + PASSWORD_HELP
    )

    if page == "register":
        title = "Join the cat club"
        description = "Your photos, a few whiskers, and a place to belong."
        content = form(page, token, username + email + password, "Create account")
        links = "<p>Already part of the club? " '<a href="/?page=login">Log in</a></p>'

    elif page == "login":
        title = "Welcome back"
        description = "Your cozy corner is waiting for you."
        login_password = field(
            "password",
            "Password",
            "password",
            attrs='required autocomplete="current-password"',
        )
        content = form(page, token, username + login_password, "Log in")
        links = (
            '<a href="/?page=forgot">Forgot your password?</a>'
            "<p>New around here? "
            '<a href="/?page=register">Join the cat club</a></p>'
        )

    elif page == "forgot":
        title = "Let’s get you back in"
        description = "We’ll email you a link to choose a new password."
        content = form(page, token, email, "Send reset link")
        links = '<a href="/?page=login">Back to login</a>'

    elif page == "reset":
        title = "A fresh start"
        description = "Choose a new password for your cozy corner."
        reset_token = (
            f'<input type="hidden" name="token" '
            f'value="{e(values.get("token", ""))}">'
        )
        content = form(page, token, password, "Save new password", reset_token)
        links = '<a href="/?page=login">Back to login</a>'

    else:
        title = "You’ve got happy mail"
        description = "One little click, and you’re part of the club."
        content = """
            <div class="centered-card">
                <img class="empty-cat" width="80" height="80"
                     src="/cat-cartoon.png" alt="A friendly illustrated cat">
                <h2>Check your inbox</h2>
                <p>Follow the confirmation link in your email before logging in.</p>
            </div>
        """
        links = '<a href="/?page=login">Back to login</a>'

    page_heading = heading(title, description)
    return f"""
        <section class="auth-wrap">
            {page_heading}
            <div class="card auth-card">
                {content}
                <div class="auth-links">{links}</div>
            </div>
        </section>
    """


def profile(user, token):
    username_fields = field(
        "username", "Username", value=user["username"], attrs=USER_ATTRS
    )
    email_fields = (
        field("email", "Email", "email", user["email"], 'required maxlength="255"')
        + field("current_password", "Current password", "password", attrs="required")
        + '<p class="form-help">'
        "Your current email stays active until you confirm the new address."
        "</p>"
    )
    password_fields = (
        field("current_password", "Current password", "password", attrs="required")
        + field("new_password", "New password", "password", attrs=PASSWORD)
        + PASSWORD_HELP
    )
    checked = "checked" if user["notify_on_comment"] else ""
    notification_fields = f"""
        <label class="checkbox-label">
            <input type="checkbox" name="notify_on_comment" value="1" {checked}>
            Email me when someone comments on my image
        </label>
    """

    sections = [
        ("Username", "username", username_fields, "Update username"),
        ("Email", "email", email_fields, "Verify new email"),
        ("Password", "password", password_fields, "Update password"),
        ("Notifications", "notify", notification_fields, "Save preference"),
    ]

    cards = []
    for title, action, fields, button in sections:
        action_field = f'<input type="hidden" name="action" value="{action}">'
        section_form = form("profile", token, fields, button, action_field)
        cards.append(f"""
            <section class="profile-section card">
                <h2>{title}</h2>
                {section_form}
            </section>
        """)

    page_heading = heading(
        "Your cozy corner", "A few small settings to make this place yours."
    )
    return f"""
        <section class="profile-wrap">
            {page_heading}
            {''.join(cards)}
        </section>
    """


def gallery(images, page, pages, token, user):
    cards = []

    for image in images:
        image_id = image["id"]
        if user:
            liked_class = "liked" if image["liked"] else ""
            likes = f"""
                <button class="like-btn {liked_class}" data-id="{image_id}">
                    💞 <span class="like-count">{image["like_count"]}</span>
                </button>
            """
        else:
            likes = f'<span>💞 {image["like_count"]}</span>'

        comments = []
        for comment in image["comments"]:
            comments.append(f"""
                <div class="comment">
                    <span class="author">{e(comment["username"])}</span>
                    {e(comment["content"])}
                </div>
            """)

        comment_form = ""
        if user:
            comment_form = f"""
                <form class="comment-form" data-id="{image_id}">
                    <input name="content" placeholder="Say something nice..."
                           maxlength="500" required>
                    <button class="btn btn-ghost">Post</button>
                </form>
            """

        cards.append(f"""
            <article class="gallery-card" id="img-{image_id}">
                <img src="/uploads/{e(image["path"])}"
                     alt="Image by {e(image["username"])}">
                <div class="meta">
                    <span>{e(image["username"])}</span>
                    {likes}
                </div>
                <div class="comments">
                    <div class="comment-list">{''.join(comments)}</div>
                    {comment_form}
                </div>
            </article>
        """)

    page_links = []
    first_page = max(1, page - 2)
    last_page = min(pages, page + 2)
    for number in range(first_page, last_page + 1):
        page_links.append(f'<a href="/?page=home&p={number}">{number}</a>')

    empty_message = ""
    if not images:
        empty_message = """
            <div class="card gallery-empty centered-card">
                <img class="empty-cat" width="80" height="80"
                     src="/cat-cartoon.png" alt="A friendly illustrated cat">
                <h2>A little empty, a little cozy</h2>
                <p>The first lovely creation could be yours.</p>
                <a class="btn btn-primary" href="/?page=editor">
                    Create your first photo
                </a>
            </div>
        """

    page_heading = heading(
        "The little gallery", "A cozy collection of your cat-inspired creations."
    )
    logged_in = str(bool(user)).lower()
    return f"""
        <section class="gallery-wrap">
            {page_heading}
            {empty_message}
            <div class="gallery-grid">{''.join(cards)}</div>
            <div class="pagination" id="pagination">{''.join(page_links)}</div>
            <div id="gallery-config"
                 data-csrf="{e(token)}"
                 data-logged-in="{logged_in}"
                 data-page="{page}"
                 data-pages="{pages}"></div>
            <div id="scroll-sentinel" style="height:1px"></div>
            <p id="scroll-loader" style="display:none">Loading...</p>
            <button id="scroll-retry" class="btn btn-ghost" style="display:none">
                Could not load images. Retry
            </button>
            <script src="/js/gallery.js"></script>
        </section>
    """


def editor(overlays, images, token, preview=""):
    stickers = []
    for overlay in overlays:
        stickers.append(f"""
            <button type="button" class="overlay-thumb"
                    data-id="{overlay["id"]}" title="{e(overlay["name"])}">
                <img src="/overlays/{e(overlay["path"])}"
                     alt="{e(overlay["name"])}">
            </button>
        """)

    photos = []
    for image in images:
        image_field = f'<input type="hidden" name="image_id" value="{image["id"]}">'
        delete_form = form(
            "delete-image", token, image_field, "Delete", button_class="del-btn"
        )
        photos.append(f"""
            <div class="thumb-item">
                <img src="/uploads/{e(image["path"])}" alt="Your image">
                {delete_form}
            </div>
        """)

    photo_list = "".join(photos)
    if not photo_list:
        photo_list = "<p class=empty-note>Your first creation will appear here.</p>"

    preview_url = e("/uploads/" + preview if preview else "")
    page_heading = heading(
        "The whisker studio",
        "Take a photo, add a little cat magic, and make it yours.",
    )
    return f"""
        <section class="studio-wrap">
            {page_heading}
            <div class="editor-wrap">
                <div class="editor-main card">
                    <div id="preview-wrap">
                        <div class="camera-placeholder" id="camera-placeholder">
                            <span aria-hidden="true">📷</span>
                            <h2>Your next lovely photo</h2>
                            <p>Use your camera or upload a favorite picture.</p>
                        </div>
                        <video id="webcam" autoplay playsinline muted
                               style="display:none"></video>
                        <canvas id="canvas-preview"
                                data-preview="{preview_url}"></canvas>
                    </div>
                    <div class="capture-actions">
                        <button class="btn btn-primary" id="btn-capture" disabled>
                            📷 Capture
                        </button>
                        <button class="btn btn-ghost" id="btn-retake"
                                style="display:none">↩ Retake</button>
                    </div>
                    <form id="capture-form" method="post" action="/?page=capture"
                          style="display:none">
                        {csrf(token)}
                        <input type="hidden" name="image_data" id="image_data">
                        <input type="hidden" name="stickers" id="stickers_data">
                    </form>
                    <details class="upload-panel">
                        <summary>Choose a photo from your device</summary>
                        <input type="file" id="file-input"
                               accept="image/png,image/jpeg,image/webp">
                    </details>
                    <p class="editor-help">
                        Add a sticker to enable capture. Drag to move, pull a corner
                        to resize, or double-click to remove.
                    </p>
                </div>
                <aside class="editor-side">
                    <div class="card">
                        <h2>A little cat magic</h2>
                        <p class="section-copy">Pick a sticker. Make it purr-sonal.</p>
                        <div class="overlay-list">{''.join(stickers)}</div>
                    </div>
                    <div class="card">
                        <h2>Your creations</h2>
                        <p class="section-copy">Your lovely little collection.</p>
                        <div class="thumb-grid">{photo_list}</div>
                    </div>
                </aside>
            </div>
            <script src="/js/editor.js"></script>
        </section>
    """
