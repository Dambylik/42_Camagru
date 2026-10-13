"""Application routes: native Python, explicit SQL and HTML, no framework."""
import json
import os
import secrets
from pathlib import Path
import pymysql
from . import db as database, security, views, mail, imaging

ROOT = Path(__file__).resolve().parent.parent / 'public'


class Problem(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status


class Request:
    def __init__(self, method, page, query, data, cookie, origin):
        self.method, self.page, self.query, self.data = method, page, query, data
        self.cookie, self.origin = cookie, origin
        self.sid, self.session, self.user = '', None, None
        self.db = None
        self.message, self.error = '', False

    def html(self, body, status=200):
        text = views.layout(self.page.title(), body, self.session['csrf_token'],
                            self.user, self.message, self.error)
        return status, [('Content-Type', 'text/html; charset=utf-8')], text.encode()

    def redirect(self, page):
        return 303, [('Location', '/?page=' + page)], b''

    def json(self, result, status=200):
        return status, [('Content-Type', 'application/json')], json.dumps(result, default=str).encode()

    def require_user(self):
        if not self.user:
            raise Problem('Please log in.', 401)

    def fail(self, message, status=400):
        raise Problem(message, status)

    def number(self, value):
        try:
            result = int(value)
            if not 0 < result <= 2147483647:
                raise ValueError()
            return result
        except (TypeError, ValueError):
            self.fail('Invalid number.')

    def get_user(self, column, value):
        # Column names come exclusively from callers in this module.
        assert column in ('id', 'email', 'username')
        return self.db.one('SELECT * FROM users WHERE ' + column + ' = %s', (value,))

    def email_link(self, email, title, page, token):
        url = os.environ.get('APP_URL', 'http://localhost:8000').rstrip('/')
        mail.send(email, title, f'Follow this link:\n{url}/?page={page}&token={token}\n\nIf you did not request this, ignore this email.')

    def check_email(self, email):
        if len(email) > 254 or not security.EMAIL.fullmatch(email):
            self.fail('Invalid email address.')
        local, domain = email.rsplit('@',1)
        labels = domain.split('.')
        if (len(local) > 64 or local.startswith('.') or local.endswith('.') or '..' in local
                or len(labels) < 2 or any(not label or len(label) > 63
                    or label.startswith('-') or label.endswith('-') for label in labels)):
            self.fail('Invalid email address.')

    def check_username(self, username):
        if not security.USERNAME.fullmatch(username):
            self.fail('Username must be 3–30 characters (letters, digits, underscore).')

    def check_password(self, password):
        if not security.strong(password):
            self.fail('Password must be at least 8 characters and include an uppercase letter, a digit, and a special character (maximum 72 UTF-8 bytes).')

    def register(self):
        username = self.data.get('username', '').strip()
        email = self.data.get('email', '').strip()
        password = self.data.get('password', '')
        self.check_username(username)
        self.check_email(email)
        self.check_password(password)
        if self.get_user('username', username) or self.get_user('email', email):
            self.fail('Username or email already taken.')
        token = secrets.token_hex(32)
        self.db.execute('INSERT INTO users (username,email,password,verify_token,verify_expires_at) '
                        'VALUES (%s,%s,%s,%s,DATE_ADD(NOW(), INTERVAL 24 HOUR))',
                        (username,email,security.password_hash(password),token))
        self.email_link(email, 'Confirm your Camagru account', 'confirm', token)
        return self.redirect('register-done')

    def confirm(self):
        token = self.query.get('token', '')
        if not security.TOKEN.fullmatch(token):
            self.fail('Invalid confirmation link.')
        _, count = self.db.execute('UPDATE users SET is_verified=1,verify_token=NULL,verify_expires_at=NULL '
                                  'WHERE verify_token=%s AND verify_expires_at>NOW()', (token,))
        if not count:
            self.fail('This confirmation link is invalid or has expired.')
        self.message = 'Email confirmed! You can now log in.'
        return self.html(views.auth('login', self.session['csrf_token'], {}))

    def login(self):
        user = self.get_user('username', self.data.get('username', '').strip())
        if not user or not security.password_matches(self.data.get('password', ''), user['password']):
            self.fail('Invalid username or password.')
        if not user['is_verified']:
            self.fail('Please confirm your email address before logging in.')
        self.sid = security.rotate(self.db, self.session, user)
        self.user = user
        return self.redirect('home')

    def logout(self):
        self.sid = security.rotate(self.db, self.session)
        self.user = None
        return self.redirect('login')

    def forgot(self):
        email = self.data.get('email', '').strip()
        self.check_email(email)
        user = self.get_user('email', email)
        if user:
            token = secrets.token_hex(32)
            self.db.execute('UPDATE users SET reset_token=%s,reset_expires_at=DATE_ADD(NOW(),INTERVAL 1 HOUR) WHERE id=%s',
                            (token, user['id']))
            self.email_link(email, 'Reset your Camagru password', 'reset', token)
        self.message = 'If that email is registered you will receive a reset link shortly.'
        return self.html(views.auth('forgot', self.session['csrf_token'], {}))

    def reset(self):
        token = (self.data if self.method == 'POST' else self.query).get('token', '')
        if not security.TOKEN.fullmatch(token):
            self.fail('Invalid reset link.')
        user = self.db.one('SELECT * FROM users WHERE reset_token=%s AND reset_expires_at>NOW() FOR UPDATE', (token,))
        if not user:
            self.fail('This reset link is invalid or has expired.')
        if self.method == 'GET':
            return self.html(views.auth('reset', self.session['csrf_token'], {'token': token}))
        password = self.data.get('password', '')
        self.check_password(password)
        self.change_password(user['id'], password)
        self.sid = security.rotate(self.db, self.session)
        self.user = None
        self.message = 'Password updated! You can now log in.'
        return self.html(views.auth('login', self.session['csrf_token'], {}))

    def change_password(self, ident, password):
        self.db.execute('UPDATE users SET password=%s,session_version=session_version+1,reset_token=NULL,reset_expires_at=NULL,'
                        'pending_email=NULL,email_change_token=NULL,email_change_expires_at=NULL WHERE id=%s',
                        (security.password_hash(password), ident))

    def profile(self):
        self.require_user()
        if self.method == 'POST':
            action = self.data.get('action', '')
            ident = self.user['id']
            if action == 'username':
                name = self.data.get('username', '').strip()
                self.check_username(name)
                self.db.execute('UPDATE users SET username=%s WHERE id=%s', (name,ident))
            elif action == 'notify':
                self.db.execute('UPDATE users SET notify_on_comment=%s WHERE id=%s',
                                (int(self.data.get('notify_on_comment') == '1'), ident))
            elif action in ('email', 'password'):
                if not security.password_matches(self.data.get('current_password', ''), self.user['password']):
                    self.fail('Current password is incorrect.')
                if action == 'password':
                    password = self.data.get('new_password', '')
                    self.check_password(password)
                    self.change_password(ident, password)
                    self.user = self.get_user('id', ident)
                    self.sid = security.rotate(self.db, self.session, self.user)
                else:
                    email = self.data.get('email', '').strip()
                    self.check_email(email)
                    if self.get_user('email', email):
                        self.fail('Email already registered.')
                    token = secrets.token_hex(32)
                    self.db.execute('UPDATE users SET pending_email=%s,email_change_token=%s,'
                                    'email_change_expires_at=DATE_ADD(NOW(),INTERVAL 1 HOUR) WHERE id=%s',
                                    (email,security.token_hash(token),ident))
                    self.email_link(email,'Confirm your new Camagru email','confirm-email',token)
                    self.message = 'Check your new email to confirm the change.'
            else:
                self.fail('Invalid profile action.')
            self.user = self.get_user('id', ident)
            self.message = self.message or 'Preferences updated.'
        return self.html(views.profile(self.user, self.session['csrf_token']))

    def confirm_email(self):
        token = self.query.get('token', '')
        if not security.TOKEN.fullmatch(token):
            self.fail('Invalid confirmation link.')
        user = self.db.one('SELECT * FROM users WHERE email_change_token=%s AND email_change_expires_at>NOW() FOR UPDATE',
                           (security.token_hash(token),))
        if not user:
            self.fail('This confirmation link is invalid or has expired.')
        self.db.execute('UPDATE users SET email=pending_email,pending_email=NULL,email_change_token=NULL,'
                        'email_change_expires_at=NULL,reset_token=NULL,reset_expires_at=NULL,'
                        'session_version=session_version+1 WHERE id=%s', (user['id'],))
        if self.user and self.user['id'] == user['id']:
            self.sid = security.rotate(self.db, self.session)
            self.user = None
        self.message = 'Email updated. Please log in again.'
        return self.html(views.auth('login',self.session['csrf_token'],{}))

    def gallery(self):
        page = self.number(self.query.get('p','1'))
        images = self.db.all('SELECT i.*,u.username,(SELECT COUNT(*) FROM likes l WHERE l.image_id=i.id) AS like_count '
                             'FROM images i JOIN users u ON u.id=i.user_id ORDER BY i.created_at DESC,i.id DESC LIMIT 5 OFFSET %s',
                             ((page-1)*5,))
        total = self.db.one('SELECT COUNT(*) AS n FROM images')['n']
        for image in images:
            image['comments'] = self.db.all('SELECT c.content,u.username FROM comments c JOIN users u ON u.id=c.user_id '
                                             'WHERE c.image_id=%s ORDER BY c.id', (image['id'],))
            image['liked'] = bool(self.user and self.db.one('SELECT 1 FROM likes WHERE user_id=%s AND image_id=%s',
                                                           (self.user['id'],image['id'])))
        pages = (total + 4)//5
        if self.page == 'gallery-json':
            return self.json({'images':images,'page':page,'pages':pages})
        return self.html(views.gallery(images,page,pages,self.session['csrf_token'],self.user))

    def interaction(self):
        self.require_user()
        ident = self.number(self.data.get('image_id'))
        image = self.db.one('SELECT * FROM images WHERE id=%s FOR UPDATE', (ident,))
        if not image:
            self.fail('Image not found.',404)
        uid = self.user['id']
        if self.page == 'like-ajax':
            liked = self.db.one('SELECT 1 FROM likes WHERE user_id=%s AND image_id=%s', (uid,ident))
            if liked:
                self.db.execute('DELETE FROM likes WHERE user_id=%s AND image_id=%s', (uid,ident))
            else:
                self.db.execute('INSERT INTO likes (user_id,image_id) VALUES (%s,%s)', (uid,ident))
            count = self.db.one('SELECT COUNT(*) AS n FROM likes WHERE image_id=%s', (ident,))['n']
            return self.json({'liked':not bool(liked),'count':count})
        content = self.data.get('content','').strip()
        if not 1 <= len(content) <= 500:
            self.fail('Comment must contain 1–500 characters.')
        self.db.execute('INSERT INTO comments (image_id,user_id,content) VALUES (%s,%s,%s)', (ident,uid,content))
        owner = self.get_user('id',image['user_id'])
        if owner['notify_on_comment']:
            # The subject requires notification for every comment, including the owner's.
            mail.send(owner['email'],'New comment on your Camagru image',
                      f'{self.user["username"]} commented:\n\n{content}')
        return self.json({'username':self.user['username'],'content':content})

    def editor(self):
        self.require_user()
        overlays = self.db.all('SELECT * FROM overlays ORDER BY id')
        images = self.db.all('SELECT * FROM images WHERE user_id=%s ORDER BY id DESC', (self.user['id'],))
        preview = self.query.get('preview','')
        if preview and not any(i['path'] == preview for i in images):
            preview = ''
        return self.html(views.editor(overlays,images,self.session['csrf_token'],preview))

    def capture(self):
        self.require_user()
        try:
            raw = imaging.compose(self.data.get('image_data',''),self.data.get('stickers','[]'),
                                  self.db.all('SELECT * FROM overlays'),ROOT)
        except ValueError as error:
            self.fail(str(error))
        name = secrets.token_hex(16) + '.png'
        path = ROOT / 'uploads' / name
        path.write_bytes(raw)
        try:
            self.db.execute('INSERT INTO images (user_id,path) VALUES (%s,%s)', (self.user['id'],name))
            self.db.connection.commit()
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return self.redirect('editor&preview=' + name)

    def delete(self):
        self.require_user()
        ident = self.number(self.data.get('image_id'))
        image = self.db.one('SELECT * FROM images WHERE id=%s FOR UPDATE', (ident,))
        if not image or image['user_id'] != self.user['id']:
            self.fail('You can delete only your own photos.',403)
        self.db.execute('DELETE FROM images WHERE id=%s', (ident,))
        self.db.connection.commit()
        (ROOT / 'uploads' / Path(image['path']).name).unlink(missing_ok=True)
        return self.redirect('editor')

    def dispatch(self):
        if self.method == 'POST':
            expected = os.environ.get('APP_URL','http://localhost:8000').rstrip('/')
            if self.origin and self.origin.rstrip('/') != expected:
                self.fail('Invalid request origin.',403)
            supplied = self.data.get('_csrf_token','')
            if not security.TOKEN.fullmatch(supplied) or not secrets.compare_digest(supplied,self.session['csrf_token']):
                self.fail('Invalid CSRF token.',403)
            routes = {'register':self.register,'login':self.login,'logout':self.logout,
                      'forgot':self.forgot,'reset':self.reset,'profile':self.profile,
                      'capture':self.capture,'delete-image':self.delete,
                      'like-ajax':self.interaction,'comment-ajax':self.interaction}
        else:
            routes = {'home':self.gallery,'gallery-json':self.gallery,'editor':self.editor,
                      'confirm':self.confirm,'confirm-email':self.confirm_email,
                      'reset':self.reset,'profile':self.profile}
            if self.page in ('login','register','forgot','register-done'):
                return self.html(views.auth(self.page,self.session['csrf_token'],{}))
        if self.page not in routes:
            self.fail('Page not found.',404)
        return routes[self.page]()


def handle(request):
    connection = database.connect()
    request.db = database.Database(connection)
    try:
        request.sid, request.session = security.session(request.db,request.cookie)
        if request.session['user_id']:
            request.user = request.get_user('id',request.session['user_id'])
            if not request.user or request.user['session_version'] != request.session['session_version']:
                request.sid = security.rotate(request.db,request.session)
                request.user = None
        # Persist initial/rotated sessions even when input validation fails.
        connection.commit()
        try:
            result = request.dispatch()
            connection.commit()
        except (Problem, pymysql.IntegrityError) as error:
            connection.rollback()
            if isinstance(error,pymysql.IntegrityError):
                error = Problem('Username or email already taken.')
            request.message, request.error = error.message, True
            if request.page in ('like-ajax','comment-ajax'):
                result = request.json({'error':error.message},error.status)
            elif error.status == 401:
                result = request.redirect('login')
            elif request.page in ('register','login','forgot'):
                result = request.html(views.auth(request.page,request.session['csrf_token'],request.data),error.status)
            elif request.page == 'profile' and request.user:
                result = request.html(views.profile(request.user,request.session['csrf_token']),error.status)
            else:
                result = request.html('<h1>Request could not be completed</h1><a href="/?page=home">Return to gallery</a>',error.status)
        status, headers, body = result
        secure = '; Secure' if os.environ.get('APP_URL','').startswith('https://') else ''
        headers.append(('Set-Cookie',f'camagru_session={request.sid}; Path=/; HttpOnly; SameSite=Lax{secure}'))
        return status, headers, body
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
