"""Auth HTML rendering."""
from .common import e, field, form, PASSWORD, PASSWORD_HELP, USER_ATTRS

def auth(page, token, values):
    username = field('username', 'Username', value=values.get('username', ''), attrs=USER_ATTRS)
    email = field('email', 'Email', 'email', values.get('email', ''), 'required maxlength="255"')
    password = field('password', 'Password', 'password', attrs=PASSWORD) + PASSWORD_HELP
    if page == 'register':
        title, content = ('Join Camagrrru', form(page, token, username + email + password, 'Register'))
        content += '<a href="/?page=login">Already registered? Log in</a>'
    elif page == 'login':
        title = 'Log in'
        content = form(page, token, username + field('password', 'Password', 'password', attrs='required'), 'Log in')
        content += '<div class="auth-links"><a href="/?page=forgot">Forgot your password?</a><a href="/?page=register">Register</a></div>'
    elif page == 'forgot':
        title, content = ('Reset your password', form(page, token, email, 'Send reset link'))
    elif page == 'reset':
        title = 'Choose a new password'
        content = form(page, token, password, 'Set new password', f'''<input type="hidden" name="token" value="{e(values.get('token', ''))}">''')
    else:
        title, content = ('Check your email', '<p>Open the confirmation email and follow its link before logging in.</p>')
    return f'<div class="auth-wrap"><h1>{title}</h1><div class="card">{content}</div></div>'
