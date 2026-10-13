"""Auth request handling: coordinate models and views."""
import secrets
from .. import security, views
from .base import BaseController


class AuthController(BaseController):
    def show(self):
        return self.request.html(views.auth(self.request.page, self.request.session["csrf_token"], {}))

    def register(self):
        username = self.request.data.get('username', '').strip()
        email = self.request.data.get('email', '').strip()
        password = self.request.data.get('password', '')
        self.check_username(username)
        self.check_email(email)
        self.check_password(password)
        if self.get_user('username', username) or self.get_user('email', email):
            self.fail('Username or email already taken.')
        token = secrets.token_hex(32)
        self.users.create((username, email, security.password_hash(password), token))
        self.email_link(email, 'Confirm your Camagru account', 'confirm', token)
        return self.request.redirect('register-done')

    def confirm(self):
        token = self.request.query.get('token', '')
        if not security.TOKEN.fullmatch(token):
            self.fail('Invalid confirmation link.')
        _, count = self.users.confirm((token,))
        if not count:
            self.fail('This confirmation link is invalid or has expired.')
        self.request.message = 'Email confirmed! You can now log in.'
        return self.request.html(views.auth('login', self.request.session['csrf_token'], {}))

    def login(self):
        user = self.get_user('username', self.request.data.get('username', '').strip())
        if not user or not security.password_matches(self.request.data.get('password', ''), user['password']):
            self.fail('Invalid username or password.')
        if not user['is_verified']:
            self.fail('Please confirm your email address before logging in.')
        self.request.sid = security.rotate(self.request.db, self.request.session, user)
        self.request.user = user
        return self.request.redirect('home')

    def logout(self):
        self.request.sid = security.rotate(self.request.db, self.request.session)
        self.request.user = None
        return self.request.redirect('login')

    def forgot(self):
        email = self.request.data.get('email', '').strip()
        self.check_email(email)
        user = self.get_user('email', email)
        if user:
            token = secrets.token_hex(32)
            self.users.set_reset_token((token, user['id']))
            self.email_link(email, 'Reset your Camagru password', 'reset', token)
        self.request.message = 'If that email is registered you will receive a reset link shortly.'
        return self.request.html(views.auth('forgot', self.request.session['csrf_token'], {}))

    def reset(self):
        token = (self.request.data if self.request.method == 'POST' else self.request.query).get('token', '')
        if not security.TOKEN.fullmatch(token):
            self.fail('Invalid reset link.')
        user = self.users.find_reset_token((token,))
        if not user:
            self.fail('This reset link is invalid or has expired.')
        if self.request.method == 'GET':
            return self.request.html(views.auth('reset', self.request.session['csrf_token'], {'token': token}))
        password = self.request.data.get('password', '')
        self.check_password(password)
        self.change_password(user['id'], password)
        self.request.sid = security.rotate(self.request.db, self.request.session)
        self.request.user = None
        self.request.message = 'Password updated! You can now log in.'
        return self.request.html(views.auth('login', self.request.session['csrf_token'], {}))

    def change_password(self, ident, password):
        self.users.update_password((security.password_hash(password), ident))

    def profile(self):
        self.require_user()
        if self.request.method == 'POST':
            action = self.request.data.get('action', '')
            ident = self.request.user['id']
            if action == 'username':
                name = self.request.data.get('username', '').strip()
                self.check_username(name)
                self.users.update_username((name, ident))
            elif action == 'notify':
                self.users.update_notifications((int(self.request.data.get('notify_on_comment') == '1'), ident))
            elif action in ('email', 'password'):
                if not security.password_matches(self.request.data.get('current_password', ''), self.request.user['password']):
                    self.fail('Current password is incorrect.')
                if action == 'password':
                    password = self.request.data.get('new_password', '')
                    self.check_password(password)
                    self.change_password(ident, password)
                    self.request.user = self.get_user('id', ident)
                    self.request.sid = security.rotate(self.request.db, self.request.session, self.request.user)
                else:
                    email = self.request.data.get('email', '').strip()
                    self.check_email(email)
                    if self.get_user('email', email):
                        self.fail('Email already registered.')
                    token = secrets.token_hex(32)
                    self.users.request_email_change((email, security.token_hash(token), ident))
                    self.email_link(email, 'Confirm your new Camagru email', 'confirm-email', token)
                    self.request.message = 'Check your new email to confirm the change.'
            else:
                self.fail('Invalid profile action.')
            self.request.user = self.get_user('id', ident)
            self.request.message = self.request.message or 'Preferences updated.'
        return self.request.html(views.profile(self.request.user, self.request.session['csrf_token']))

    def confirm_email(self):
        token = self.request.query.get('token', '')
        if not security.TOKEN.fullmatch(token):
            self.fail('Invalid confirmation link.')
        user = self.users.find_email_change((security.token_hash(token),))
        if not user:
            self.fail('This confirmation link is invalid or has expired.')
        self.users.confirm_email_change((user['id'],))
        if self.request.user and self.request.user['id'] == user['id']:
            self.request.sid = security.rotate(self.request.db, self.request.session)
            self.request.user = None
        self.request.message = 'Email updated. Please log in again.'
        return self.request.html(views.auth('login', self.request.session['csrf_token'], {}))

