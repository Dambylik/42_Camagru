"""Front controller: routes, sessions, transactions and error responses."""
import os
import secrets
import pymysql
from . import db as database, security, views
from .http import Request, Problem
from .models.users import UserModel
from .controllers.auth import AuthController
from .controllers.gallery import GalleryController
from .controllers.editor import EditorController


def dispatch(request):
    auth = AuthController(request)
    gallery = GalleryController(request)
    editor = EditorController(request)
    if request.method == 'POST':
        expected = os.environ.get('APP_URL', 'http://localhost:8000').rstrip('/')
        if request.origin and request.origin.rstrip('/') != expected:
            raise Problem('Invalid request origin.', 403)
        supplied = request.data.get('_csrf_token', '')
        if not security.TOKEN.fullmatch(supplied) or not secrets.compare_digest(supplied, request.session['csrf_token']):
            raise Problem('Invalid CSRF token.', 403)
        routes = {'register': auth.register, 'login': auth.login, 'logout': auth.logout, 'forgot': auth.forgot, 'reset': auth.reset, 'profile': auth.profile, 'capture': editor.capture, 'delete-image': editor.delete, 'like-ajax': gallery.interaction, 'comment-ajax': gallery.interaction}
    else:
        routes = {'home': gallery.gallery, 'gallery-json': gallery.gallery, 'editor': editor.editor, 'confirm': auth.confirm, 'confirm-email': auth.confirm_email, 'reset': auth.reset, 'profile': auth.profile}
        if request.page in ('login', 'register', 'forgot', 'register-done'):
            return auth.show()
    if request.page not in routes:
        raise Problem('Page not found.', 404)
    return routes[request.page]()

def handle(request):
    connection = database.connect()
    request.db = database.Database(connection)
    try:
        request.sid, request.session = security.session(request.db, request.cookie)
        if request.session['user_id']:
            request.user = UserModel(request.db).find_by('id', request.session['user_id'])
            if not request.user or request.user['session_version'] != request.session['session_version']:
                request.sid = security.rotate(request.db, request.session)
                request.user = None
        connection.commit()
        try:
            result = dispatch(request)
            connection.commit()
        except (Problem, pymysql.IntegrityError) as error:
            connection.rollback()
            if isinstance(error, pymysql.IntegrityError):
                error = Problem('Username or email already taken.')
            request.message, request.error = (error.message, True)
            if request.page in ('like-ajax', 'comment-ajax'):
                result = request.json({'error': error.message}, error.status)
            elif error.status == 401:
                result = request.redirect('login')
            elif request.page in ('register', 'login', 'forgot'):
                status = 200 if error.status == 400 else error.status
                result = request.html(views.auth(request.page, request.session['csrf_token'], request.data), status)
            elif request.page == 'profile' and request.user:
                status = 200 if error.status == 400 else error.status
                result = request.html(views.profile(request.user, request.session['csrf_token']), status)
            else:
                result = request.html(views.error(), error.status)
        status, headers, body = result
        secure = '; Secure' if os.environ.get('APP_URL', '').startswith('https://') else ''
        headers.append(('Set-Cookie', f'camagru_session={request.sid}; Path=/; HttpOnly; SameSite=Lax{secure}'))
        return (status, headers, body)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
