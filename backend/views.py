"""HTML rendering with explicit escaping (PHP equivalent: htmlspecialchars)."""
from html import escape


def e(value):
    return escape(str(value), quote=True)


def csrf(token):
    return f'<input type="hidden" name="_csrf_token" value="{e(token)}">'


def field(name, label, kind='text', value='', attrs=''):
    return (f'<div class="form-group"><label>{e(label)}'
            f'<input type="{kind}" name="{name}" value="{e(value)}" {attrs}></label></div>')


PASSWORD = 'required minlength="8" maxlength="72" pattern="(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{8,}"'
PASSWORD_HELP = '<small>8+ characters, uppercase, digit, special character; at most 72 UTF-8 bytes.</small>'
USER_ATTRS = 'required minlength="3" maxlength="30" pattern="[A-Za-z0-9_]{3,30}"'


def form(page, token, content, button, extra=''):
    return (f'<form method="post" action="/?page={page}">{csrf(token)}{extra}{content}'
            f'<button class="btn btn-primary" type="submit">{e(button)}</button></form>')


def layout(title, body, token, user=None, message='', error=False):
    nav = '<a href="/?page=home">Galerrry</a>'
    if user:
        nav += ('<a href="/?page=editor">📷 Studio</a><span class="spacer"></span>'
                f'<a href="/?page=profile">{e(user["username"])}</a>'
                + form('logout', token, '', 'Log out'))
    else:
        nav += '<span class="spacer"></span><a href="/?page=login">Log in</a><a href="/?page=register">Register</a>'
    notice = f'<div role="status" class="alert alert-{"error" if error else "success"}">{e(message)}</div>' if message else ''
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{e(title)} — Camagrrru</title><link rel="stylesheet" href="/css/app.css">'
            '<link rel="icon" href="/cat-cartoon.png"></head><body><nav>'
            '<a class="brand" href="/"><img src="/cat-cartoon.png" alt="" class="brand-logo">Camagrrru</a>'
            f'{nav}</nav><main>{notice}{body}</main><footer>Camagrrru · Made with Python 🐾</footer></body></html>')


def auth(page, token, values):
    username = field('username', 'Username', value=values.get('username', ''), attrs=USER_ATTRS)
    email = field('email', 'Email', 'email', values.get('email', ''), 'required maxlength="255"')
    password = field('password', 'Password', 'password', attrs=PASSWORD) + PASSWORD_HELP
    if page == 'register':
        title, content = 'Join Camagrrru', form(page, token, username + email + password, 'Register')
        content += '<a href="/?page=login">Already registered? Log in</a>'
    elif page == 'login':
        title = 'Log in'
        content = form(page, token, username + field('password', 'Password', 'password', attrs='required'), 'Log in')
        content += '<div class="auth-links"><a href="/?page=forgot">Forgot your password?</a><a href="/?page=register">Register</a></div>'
    elif page == 'forgot':
        title, content = 'Reset your password', form(page, token, email, 'Send reset link')
    elif page == 'reset':
        title = 'Choose a new password'
        content = form(page, token, password, 'Set new password',
                       f'<input type="hidden" name="token" value="{e(values.get("token", ""))}">')
    else:
        title, content = 'Check your email', '<p>Open the confirmation email and follow its link before logging in.</p>'
    return f'<div class="auth-wrap"><h1>{title}</h1><div class="card">{content}</div></div>'


def profile(user, token):
    sections = [
        ('Username', 'username', field('username', 'Username', value=user['username'], attrs=USER_ATTRS), 'Update username'),
        ('Email', 'email', field('email', 'Email', 'email', user['email'], 'required maxlength="255"')
         + field('current_password', 'Current password', 'password', attrs='required')
         + '<p>Your current email stays active until you confirm the new address.</p>', 'Verify new email'),
        ('Password', 'password', field('current_password', 'Current password', 'password', attrs='required')
         + field('new_password', 'New password', 'password', attrs=PASSWORD) + PASSWORD_HELP, 'Update password'),
        ('Notifications', 'notify', '<label><input type="checkbox" name="notify_on_comment" value="1" '
         + ('checked' if user['notify_on_comment'] else '') + '> Email me when someone comments on my image</label>', 'Save preference'),
    ]
    return '<h1>Edit profile</h1>' + ''.join(
        f'<section class="profile-section card"><h2>{title}</h2>'
        + form('profile', token, content, button, f'<input type="hidden" name="action" value="{action}">')
        + '</section>' for title, action, content, button in sections)


def gallery(images, page, pages, token, user):
    cards = []
    for image in images:
        ident = image['id']
        likes = (f'<button class="like-btn {"liked" if image["liked"] else ""}" data-id="{ident}">'
                 f'💞 <span class="like-count">{image["like_count"]}</span></button>') if user else f'<span>💞 {image["like_count"]}</span>'
        comments = ''.join(f'<div class="comment"><span class="author">{e(c["username"])}</span> {e(c["content"])}</div>' for c in image['comments'])
        comment_form = (f'<form class="comment-form" data-id="{ident}">'
                        '<input name="content" placeholder="Say something nice..." maxlength="500" required>'
                        '<button class="btn btn-ghost">Post</button></form>') if user else ''
        cards.append(f'<article class="gallery-card" id="img-{ident}"><img src="/uploads/{e(image["path"])}" alt="Image by {e(image["username"])}">'
                     f'<div class="meta"><span>{e(image["username"])}</span>{likes}</div>'
                     f'<div class="comments"><div class="comment-list">{comments}</div>{comment_form}</div></article>')
    pagination = ''.join(f'<a href="/?page=home&p={i}">{i}</a>' for i in range(max(1,page-2), min(pages,page+2)+1))
    return ('<h1>🐱 Galerrry</h1>' + ('' if images else '<p>No photos yet. <a href="/?page=editor">Be the first to post!</a></p>')
            + '<div class="gallery-grid">' + ''.join(cards) + '</div>'
            + f'<div class="pagination" id="pagination">{pagination}</div>'
            + f'<div id="gallery-config" data-csrf="{e(token)}" data-logged-in="{str(bool(user)).lower()}" data-page="{page}" data-pages="{pages}"></div>'
            + '<div id="scroll-sentinel" style="height:1px"></div><p id="scroll-loader" style="display:none">Loading...</p>'
            + '<button id="scroll-retry" class="btn btn-ghost" style="display:none">Could not load images. Retry</button>'
            + '<script src="/js/gallery.js"></script>')


def editor(overlays, images, token, preview=''):
    thumbs = ''.join(f'<div class="overlay-thumb" data-id="{o["id"]}" title="{e(o["name"])}">'
                     f'<img src="/overlays/{e(o["path"])}" alt="{e(o["name"])}"></div>' for o in overlays)
    photos = ''.join(f'<div class="thumb-item"><img src="/uploads/{e(i["path"])}" alt="Your image">'
                     + form('delete-image', token, f'<input type="hidden" name="image_id" value="{i["id"]}">', 'Delete').replace('class="btn btn-primary"','class="del-btn"')
                     + '</div>' for i in images)
    return ('<h1>📷 Studio</h1><div class="editor-wrap"><div class="editor-main"><div id="preview-wrap">'
            '<video id="webcam" autoplay playsinline muted style="display:none"></video>'
            f'<canvas id="canvas-preview" data-preview="{e("/uploads/" + preview if preview else "")}"></canvas></div>'
            '<div style="display:flex;gap:.5rem;flex-wrap:wrap"><button class="btn btn-primary" id="btn-capture" disabled>📷 Capture</button>'
            '<button class="btn btn-ghost" id="btn-retake" style="display:none">↩ Retake</button></div>'
            f'<form id="capture-form" method="post" action="/?page=capture" style="display:none">{csrf(token)}'
            '<input type="hidden" name="image_data" id="image_data"><input type="hidden" name="stickers" id="stickers_data"></form>'
            '<details><summary>Or upload a photo instead</summary><input type="file" id="file-input" accept="image/png,image/jpeg,image/webp"></details>'
            '<p>Select an overlay before capture. Drag to move, use corners to resize, double-click to remove.</p></div>'
            f'<aside class="editor-side"><div class="card"><h2>Cat overlays</h2><div class="overlay-list">{thumbs}</div></div>'
            f'<div class="card"><h2>Your photos</h2><div class="thumb-grid">{photos}</div></div></aside></div>'
            '<script src="/js/editor.js"></script>')
