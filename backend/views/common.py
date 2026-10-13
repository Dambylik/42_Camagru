"""HTML rendering with explicit escaping (PHP equivalent: htmlspecialchars)."""
from html import escape

def e(value):
    return escape(str(value), quote=True)

def csrf(token):
    return f'<input type="hidden" name="_csrf_token" value="{e(token)}">'

def field(name, label, kind='text', value='', attrs=''):
    return f'<div class="form-group"><label>{e(label)}<input type="{kind}" name="{name}" value="{e(value)}" {attrs}></label></div>'
PASSWORD = 'required minlength="8" maxlength="72" pattern="(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{8,}"'
PASSWORD_HELP = '<small class="form-help">8+ characters, uppercase, digit, special character; at most 72 UTF-8 bytes.</small>'
USER_ATTRS = 'required minlength="3" maxlength="30" pattern="[A-Za-z0-9_]{3,30}"'

def form(page, token, content, button, extra=''):
    return f'<form method="post" action="/?page={page}">{csrf(token)}{extra}{content}<button class="btn btn-primary" type="submit">{e(button)}</button></form>'

def layout(title, body, token, user=None, message='', error=False):
    nav = '<a href="/?page=home">Galerrry</a>'
    if user:
        nav += f"""<a href="/?page=editor">📷 Studio</a><span class="spacer"></span><a href="/?page=profile">{e(user['username'])}</a>""" + form('logout', token, '', 'Log out')
    else:
        nav += '<span class="spacer"></span><a href="/?page=login">Log in</a><a href="/?page=register">Register</a>'
    notice = f"""<div role="status" class="alert alert-{('error' if error else 'success')}">{e(message)}</div>""" if message else ''
    return f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)} — Camagrrru</title><link rel="stylesheet" href="/css/app.css"><link rel="icon" href="/cat-cartoon.png"></head><body><nav><a class="brand" href="/"><img src="/cat-cartoon.png" alt="" class="brand-logo">Camagrrru</a>{nav}</nav><main>{notice}{body}</main><footer>Camagrrru · Made with Python 🐾</footer></body></html>'


def error():
    return '<h1>Request could not be completed</h1><a href="/?page=home">Return to gallery</a>'
