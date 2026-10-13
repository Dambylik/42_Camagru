"""End-to-end tests against the running Python app; deletes only its own fixtures."""
import base64
import http.cookiejar
import io
import json
import re
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, '/app')
from backend.db import connect, Database
from backend.security import password_matches
from PIL import Image

BASE = 'http://localhost:8000'
checks = 0


def check(value, message):
    global checks
    assert value, message
    checks += 1


def messages_to(address):
    data = json.load(urllib.request.urlopen('http://mailpit:8025/api/v1/messages?limit=200'))
    return [message for message in data['messages']
            if any(recipient['Address'] == address for recipient in message['To'])]


def notifications(address):
    return sum(message['Subject'] == 'New comment on your Camagru image'
               for message in messages_to(address))


class Browser:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.csrf = ''

    def request(self, page='home', data=None, token=True):
        if data is not None:
            data = dict(data)
            if token:
                data['_csrf_token'] = self.csrf
        request = urllib.request.Request(BASE + '/?page=' + page,
                    urllib.parse.urlencode(data).encode() if data is not None else None)
        try:
            response = self.opener.open(request, timeout=20)
        except urllib.error.HTTPError as error:
            response = error
        body = response.read().decode()
        match = re.search(r'name="_csrf_token" value="([a-f0-9]+)"',body)
        if match:
            self.csrf = match.group(1)
        return response.status, body


def main():
    conn = connect()
    conn.autocommit(True)
    db = Database(conn)
    suffix = secrets.token_hex(6)
    names = ['py_test_' + suffix, 'py_other_' + suffix]
    password = 'OldPassword1!'
    a, b, anon = Browser(), Browser(), Browser()
    files = []
    try:
        status, body = anon.request()
        check(status == 200 and body.startswith('<!DOCTYPE html>'), 'Public gallery / doctype')
        status, body = anon.request('editor')
        check('Log in' in body and 'id="canvas-preview"' not in body, 'Anonymous editor restriction')
        status, _ = anon.request('like-ajax', {'image_id':1}, token=False)
        check(status == 403, 'Missing CSRF rejected')
        status, _ = anon.request('like-ajax', {'image_id':1,'_csrf_token':'é'}, token=False)
        check(status == 403, 'Non-ASCII CSRF rejected without exception')
        for browser, name in ((a,names[0]),(b,names[1])):
            browser.request('register')
            status, _ = browser.request('register', {'username':name,'email':name+'@example.com','password':'weak'})
            check(status == 400, 'Weak password rejected on server')
            status, body = browser.request('register', {'username':name,'email':name+'@example.com','password':password})
            check(status == 200 and 'Check your email' in body, 'Registration and delivery')
            user = db.one('SELECT * FROM users WHERE username=%s',(name,))
            check(user and user['notify_on_comment'] == 1 and user['password'] != password, 'Hash/default preferences')
            check(password_matches(password,user['password'].replace('$2b$','$2y$')), 'Legacy PHP bcrypt compatibility')
            status, body = browser.request('login', {'username':name,'password':password})
            check(status == 400 and 'confirm your email' in body, 'Unverified login blocked')
            status, body = browser.request('confirm&token=' + user['verify_token'])
            check(status == 200 and 'Email confirmed' in body, 'Confirmation')
            status, _ = browser.request('confirm&token=' + user['verify_token'])
            check(status == 400, 'Confirmation token consumed')
            status, _ = browser.request('login', {'username':name,'password':"blahblah' OR 1='1"})
            check(status == 400, 'SQL injection rejected')
            status, body = browser.request('login', {'username':name,'password':password})
            check(status == 200 and 'Log out' in body, 'Confirmed login')
        owner = db.one('SELECT * FROM users WHERE username=%s',(names[0],))
        other = db.one('SELECT * FROM users WHERE username=%s',(names[1],))
        a.request('editor')
        buffer = io.BytesIO()
        Image.new('RGB',(600,600),'white').save(buffer,format='PNG')
        image_data = 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()
        overlay = db.one('SELECT * FROM overlays ORDER BY id LIMIT 1')
        sticker = {'id':overlay['id'],'x':10,'y':20,'w':100,'h':100}
        status, _ = a.request('capture', {'image_data':image_data,'stickers':'[]'})
        check(status == 400, 'Overlay mandatory')
        status, _ = a.request('capture', {'image_data':'data:image/png;base64,YmFk','stickers':json.dumps([sticker])})
        check(status == 400, 'Invalid image rejected')
        status, _ = a.request('capture', {'image_data':image_data,'stickers':json.dumps([dict(sticker,id=99999999)])})
        check(status == 400, 'Unknown sticker rejected')
        for index in range(6):
            status, body = a.request('capture', {'image_data':image_data,'stickers':json.dumps([sticker] * (1 + index % 2))})
            check(status == 200 and 'id="canvas-preview"' in body, 'Server image composition')
        images = db.all('SELECT * FROM images WHERE user_id=%s ORDER BY id',(owner['id'],))
        files = [i['path'] for i in images]
        with Image.open('/app/public/uploads/' + images[0]['path']) as composed:
            check(composed.size == (600,600) and composed.convert('RGB').tobytes() != Image.new('RGB',(600,600),'white').tobytes(), 'Saved pixels contain overlay')
        status, body = anon.request('gallery-json')
        feed = json.loads(body)
        check(status == 200 and len(feed['images']) == 5 and feed['pages'] >= 2, 'Five-image pagination')
        status, body = anon.request('gallery-json&p=2')
        check(status == 200 and len(json.loads(body)['images']) >= 1, 'Next gallery page')
        ident = images[-1]['id']
        b.request('home')
        status, _ = b.request('delete-image', {'image_id':ident})
        check(status == 403 and db.one('SELECT id FROM images WHERE id=%s',(ident,)), 'Ownership enforced')
        status, body = b.request('like-ajax', {'image_id':ident})
        check(status == 200 and json.loads(body)['liked'], 'Like')
        status, body = b.request('like-ajax', {'image_id':ident})
        check(status == 200 and not json.loads(body)['liked'], 'Unlike')
        xss = "<script>alert('THE GAME')</script>"
        before = notifications(owner['email'])
        status, _ = b.request('comment-ajax', {'image_id':ident,'content':xss})
        check(status == 200, 'Comment stored')
        check(notifications(owner['email']) == before+1, 'Actual comment email delivered')
        status, body = anon.request('home')
        check(xss not in body and '&lt;script&gt;' in body, 'HTML escaping')
        status, _ = a.request('profile', {'action':'notify'})
        check(status == 200 and db.one('SELECT notify_on_comment FROM users WHERE id=%s',(owner['id'],))['notify_on_comment'] == 0, 'Disable notifications')
        status, _ = b.request('comment-ajax', {'image_id':ident,'content':'Notification disabled test'})
        check(status == 200, 'Comment with notifications disabled')
        check(notifications(owner['email']) == before+1, 'No email when preference disabled')
        a.request('profile')
        status, _ = a.request('profile', {'action':'email','email':'new_'+names[0]+'@example.com','current_password':'wrong'})
        check(status == 400, 'Email requires current password')
        status, _ = a.request('profile', {'action':'email','email':'new_'+names[0]+'@example.com','current_password':password})
        changed = db.one('SELECT * FROM users WHERE id=%s',(owner['id'],))
        check(status == 200 and changed['email'] == owner['email'] and changed['pending_email'], 'Email waits for confirmation')
        status, _ = a.request('profile', {'action':'password','current_password':password,'new_password':'NewPassword2!'})
        check(status == 200, 'Profile password update')
        changed = db.one('SELECT * FROM users WHERE id=%s',(owner['id'],))
        check(changed['email_change_token'] is None, 'Password change invalidates pending email')
        c = Browser()
        c.request('login')
        c.request('login', {'username':names[0],'password':'NewPassword2!'})
        a.request('forgot')
        status, _ = a.request('forgot', {'email':owner['email']})
        check(status == 200, 'Reset email delivered')
        token = db.one('SELECT reset_token FROM users WHERE id=%s',(owner['id'],))['reset_token']
        db.execute('UPDATE users SET reset_expires_at=DATE_SUB(NOW(),INTERVAL 1 HOUR) WHERE id=%s',(owner['id'],))
        status, _ = a.request('reset&token='+token)
        check(status == 400, 'Expired reset token rejected')
        a.request('forgot', {'email':owner['email']})
        token = db.one('SELECT reset_token FROM users WHERE id=%s',(owner['id'],))['reset_token']
        a.request('reset&token='+token)
        status, _ = a.request('reset', {'token':token,'password':'FinalPassword3!'})
        check(status == 200, 'Reset password')
        status, _ = a.request('reset&token='+token)
        check(status == 400, 'Reset token single use')
        status, body = c.request('profile')
        check('id="canvas-preview"' not in body and 'Forgot your password?' in body, 'Old session revoked')
        a.request('login')
        status, _ = a.request('login', {'username':names[0],'password':'NewPassword2!'})
        check(status == 400, 'Old password rejected')
        status, _ = a.request('login', {'username':names[0],'password':'FinalPassword3!'})
        check(status == 200, 'New password accepted')
        email = 'confirmed_'+names[0]+'@example.com'
        status, _ = a.request('profile', {'action':'email','email':email,'current_password':'FinalPassword3!'})
        check(status == 200, 'Email change request')
        message = next(item for item in messages_to(email) if item['Subject']=='Confirm your new Camagru email')
        detail = json.load(urllib.request.urlopen('http://mailpit:8025/api/v1/message/'+message['ID']))
        token = re.search(r'page=confirm-email&token=([a-f0-9]+)',detail['Text']).group(1)
        status, _ = a.request('confirm-email&token='+token)
        check(status == 200 and db.one('SELECT email FROM users WHERE id=%s',(owner['id'],))['email']==email, 'Confirmed email applied')
        status, _ = a.request('confirm-email&token='+token)
        check(status == 400, 'Email change token single use')
        a.request('login')
        a.request('login', {'username':names[0],'password':'FinalPassword3!'})
        status, _ = a.request('delete-image', {'image_id':ident})
        check(status == 200 and not db.one('SELECT id FROM images WHERE id=%s',(ident,)), 'Owner deletion')
        status, body = a.request('logout', {})
        check(status == 200 and 'Forgot your password?' in body, 'Logout')
        status, body = a.request('profile')
        check('Forgot your password?' in body, 'Protected page after logout')
        print(f'Passed {checks} Python HTTP/database/security checks.')
    finally:
        for name in names:
            user = db.one('SELECT id FROM users WHERE username=%s',(name,))
            if user:
                files.extend(i['path'] for i in db.all('SELECT path FROM images WHERE user_id=%s',(user['id'],)))
                db.execute('DELETE FROM sessions WHERE user_id=%s',(user['id'],))
                db.execute('DELETE FROM users WHERE id=%s',(user['id'],))
        for name in set(files):
            (Path('/app/public/uploads') / name).unlink(missing_ok=True)
        conn.close()


if __name__ == '__main__':
    main()
