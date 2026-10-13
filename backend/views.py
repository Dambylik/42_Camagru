"""HTML rendering with explicit escaping (PHP equivalent: htmlspecialchars)."""
from html import escape

def e(value):
    return escape(str(value), quote=True)

def csrf(token):
    return f'<input type="hidden" name="_csrf_token" value="{e(token)}">'

def field(name, label, kind='text', value='', attrs=''):
    return f'<div class="form-group"><label>{e(label)}<input type="{kind}" name="{name}" value="{e(value)}" {attrs}></label></div>'
PASSWORD = 'required minlength="8" maxlength="72" pattern="(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{8,}"'
PASSWORD_HELP = '<small class="form-help">8+ characters, uppercase, digit, special character</small>'
USER_ATTRS = 'required minlength="3" maxlength="30" pattern="[A-Za-z0-9_]{3,30}"'

def form(page, token, content, button, extra=''):
    return f'<form method="post" action="/?page={page}">{csrf(token)}{extra}{content}<button class="btn btn-primary" type="submit">{e(button)}</button></form>'

def heading(title, description):
    return (f'<header class="page-heading"><span class="eyebrow">A little corner for cat lovers</span>'
            f'<h1>{e(title)}</h1><p>{e(description)}</p></header>')


def layout(title, body, token, user=None, message='', error=False):
    active = title.lower()
    gallery_link = f'<a class="nav-link {"active" if active == "home" else ""}" href="/?page=home">Gallery</a>'
    if user:
        links = (gallery_link
                 + f'<a class="nav-link {"active" if active == "editor" else ""}" href="/?page=editor">Studio</a>'
                 + f'<a class="nav-link account-link {"active" if active == "profile" else ""}" href="/?page=profile">{e(user["username"])}</a>'
                 + form('logout', token, '', 'Log out'))
    else:
        links = (gallery_link
                 + f'<a class="nav-link {"active" if active == "login" else ""}" href="/?page=login">Log in</a>'
                 + f'<a class="nav-link nav-join {"active" if active == "register" else ""}" href="/?page=register">Join the club</a>')
    notice = (f'<div role="status" class="alert alert-{"error" if error else "success"}">{e(message)}</div>'
              if message else '')
    return f'''<!DOCTYPE html>
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
    <nav aria-label="Main navigation"><div class="nav-inner">
        <a class="brand" href="/"><span class="brand-icon"><img width="35" height="35" src="/cat-cartoon.png" alt=""></span>Camagrrru<span class="brand-heart" aria-hidden="true">♡</span></a>
        <div class="nav-links">{links}</div>
    </div></nav>
    <main id="content">{notice}{body}</main>
    <footer><span aria-hidden="true">🐾</span> A little creativity. A lot of cat love.<span class="footer-brand">Camagrrru</span></footer>
</body>
</html>'''


def error():
    return ('<section class="auth-wrap">'
            + heading('A little snag', 'Let’s get you back to the cozy corner.')
            + '<div class="card centered-card"><img class="empty-cat" width="80" height="80" src="/cat-cartoon.png" alt="A friendly illustrated cat">'
              '<a class="btn btn-primary" href="/?page=home">Back to the gallery</a></div></section>')


def auth(page, token, values):
    username = field('username', 'Username', value=values.get('username', ''), attrs=USER_ATTRS + ' autocomplete="username"')
    email = field('email', 'Email address', 'email', values.get('email', ''), 'required maxlength="255" autocomplete="email"')
    password = field('password', 'Password', 'password', attrs=PASSWORD + ' autocomplete="new-password"') + PASSWORD_HELP
    if page == 'register':
        title, description = 'Join the cat club', 'Your photos, a few whiskers, and a place to belong.'
        content = form(page, token, username + email + password, 'Create account')
        links = '<p>Already part of the club? <a href="/?page=login">Log in</a></p>'
    elif page == 'login':
        title, description = 'Welcome back', 'Your cozy corner is waiting for you.'
        content = form(page, token, username + field('password', 'Password', 'password', attrs='required autocomplete="current-password"'), 'Log in')
        links = '<a href="/?page=forgot">Forgot your password?</a><p>New around here? <a href="/?page=register">Join the cat club</a></p>'
    elif page == 'forgot':
        title, description = 'Let’s get you back in', 'We’ll email you a link to choose a new password.'
        content = form(page, token, email, 'Send reset link')
        links = '<a href="/?page=login">Back to login</a>'
    elif page == 'reset':
        title, description = 'A fresh start', 'Choose a new password for your cozy corner.'
        content = form(page, token, password, 'Save new password', f'<input type="hidden" name="token" value="{e(values.get("token", ""))}">')
        links = '<a href="/?page=login">Back to login</a>'
    else:
        title, description = 'You’ve got happy mail', 'One little click, and you’re part of the club.'
        content = ('<div class="centered-card"><img class="empty-cat" width="80" height="80" src="/cat-cartoon.png" alt="A friendly illustrated cat">'
                   '<h2>Check your inbox</h2><p>Follow the confirmation link in your email before logging in.</p></div>')
        links = '<a href="/?page=login">Back to login</a>'
    return ('<section class="auth-wrap">' + heading(title, description)
            + f'<div class="card auth-card">{content}<div class="auth-links">{links}</div></div></section>')


def profile(user, token):
    sections = [('Username', 'username', field('username', 'Username', value=user['username'], attrs=USER_ATTRS), 'Update username'), ('Email', 'email', field('email', 'Email', 'email', user['email'], 'required maxlength="255"') + field('current_password', 'Current password', 'password', attrs='required') + '<p class="form-help">Your current email stays active until you confirm the new address.</p>', 'Verify new email'), ('Password', 'password', field('current_password', 'Current password', 'password', attrs='required') + field('new_password', 'New password', 'password', attrs=PASSWORD) + PASSWORD_HELP, 'Update password'), ('Notifications', 'notify', '<label class="checkbox-label"><input type="checkbox" name="notify_on_comment" value="1" ' + ('checked' if user['notify_on_comment'] else '') + '> Email me when someone comments on my image</label>', 'Save preference')]
    return '<section class="profile-wrap">' + heading('Your cozy corner', 'A few small settings to make this place yours.') + ''.join((f'<section class="profile-section card"><h2>{title}</h2>' + form('profile', token, content, button, f'<input type="hidden" name="action" value="{action}">') + '</section>' for title, action, content, button in sections)) + '</section>'

def gallery(images, page, pages, token, user):
    cards = []
    for image in images:
        ident = image['id']
        likes = f'''<button class="like-btn {('liked' if image['liked'] else '')}" data-id="{ident}">💞 <span class="like-count">{image['like_count']}</span></button>''' if user else f"<span>💞 {image['like_count']}</span>"
        comments = ''.join((f"""<div class="comment"><span class="author">{e(c['username'])}</span> {e(c['content'])}</div>""" for c in image['comments']))
        comment_form = f'<form class="comment-form" data-id="{ident}"><input name="content" placeholder="Say something nice..." maxlength="500" required><button class="btn btn-ghost">Post</button></form>' if user else ''
        cards.append(f"""<article class="gallery-card" id="img-{ident}"><img src="/uploads/{e(image['path'])}" alt="Image by {e(image['username'])}"><div class="meta"><span>{e(image['username'])}</span>{likes}</div><div class="comments"><div class="comment-list">{comments}</div>{comment_form}</div></article>""")
    pagination = ''.join((f'<a href="/?page=home&p={i}">{i}</a>' for i in range(max(1, page - 2), min(pages, page + 2) + 1)))
    return '<section class="gallery-wrap">' + heading('The little gallery', 'Made with imagination. Finished with whiskers.') + ('' if images else '<div class="card gallery-empty centered-card"><img class="empty-cat" width="80" height="80" src="/cat-cartoon.png" alt="A friendly illustrated cat"><h2>A little empty, a little cozy</h2><p>The first lovely creation could be yours.</p><a class="btn btn-primary" href="/?page=editor">Create your first photo</a></div>') + '<div class="gallery-grid">' + ''.join(cards) + '</div>' + f'<div class="pagination" id="pagination">{pagination}</div>' + f'<div id="gallery-config" data-csrf="{e(token)}" data-logged-in="{str(bool(user)).lower()}" data-page="{page}" data-pages="{pages}"></div>' + '<div id="scroll-sentinel" style="height:1px"></div><p id="scroll-loader" style="display:none">Loading...</p>' + '<button id="scroll-retry" class="btn btn-ghost" style="display:none">Could not load images. Retry</button>' + '<script src="/js/gallery.js"></script></section>'

def editor(overlays, images, token, preview=''):
    thumbs = ''.join((f'''<button type="button" class="overlay-thumb" data-id="{o['id']}" title="{e(o['name'])}"><img src="/overlays/{e(o['path'])}" alt="{e(o['name'])}"></button>''' for o in overlays))
    photos = ''.join((f"""<div class="thumb-item"><img src="/uploads/{e(i['path'])}" alt="Your image">""" + form('delete-image', token, f'''<input type="hidden" name="image_id" value="{i['id']}">''', 'Delete').replace('class="btn btn-primary"', 'class="del-btn"') + '</div>' for i in images))
    return '<section class="studio-wrap">' + heading('The whisker studio', 'Take a photo, add a little cat magic, and make it yours.') + f'''<div class="editor-wrap"><div class="editor-main card"><div id="preview-wrap"><div class="camera-placeholder" id="camera-placeholder"><span aria-hidden="true">📷</span><h2>Your next lovely photo</h2><p>Use your camera or upload a favorite picture.</p></div><video id="webcam" autoplay playsinline muted style="display:none"></video><canvas id="canvas-preview" data-preview="{e('/uploads/' + preview if preview else '')}"></canvas></div><div class="capture-actions"><button class="btn btn-primary" id="btn-capture" disabled>📷 Capture</button><button class="btn btn-ghost" id="btn-retake" style="display:none">↩ Retake</button></div><form id="capture-form" method="post" action="/?page=capture" style="display:none">{csrf(token)}<input type="hidden" name="image_data" id="image_data"><input type="hidden" name="stickers" id="stickers_data"></form><details class="upload-panel"><summary>Choose a photo from your device</summary><input type="file" id="file-input" accept="image/png,image/jpeg,image/webp"></details><p class="editor-help">Add a sticker to enable capture. Drag to move, pull a corner to resize, or double-click to remove.</p></div><aside class="editor-side"><div class="card"><h2>A little cat magic</h2><p class="section-copy">Pick a sticker. Make it purr-sonal.</p><div class="overlay-list">{thumbs}</div></div><div class="card"><h2>Your creations</h2><p class="section-copy">Your lovely little collection.</p><div class="thumb-grid">{photos or "<p class=empty-note>Your first creation will appear here.</p>"}</div></div></aside></div><script src="/js/editor.js"></script></section>'''
