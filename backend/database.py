"""MariaDB connection and parameterized queries (the data/model layer)."""
import os
import pymysql

def connect():
    return pymysql.connect(host=os.environ.get('DB_HOST', 'db'), database=os.environ.get('DB_NAME', 'camagru'), user=os.environ['DB_USER'], password=os.environ['DB_PASSWORD'], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor, connect_timeout=5, read_timeout=10, write_timeout=10, autocommit=False)

def fetch_all(connection, sql, values=()):
    with connection.cursor() as cursor:
        cursor.execute(sql, values)
        return cursor.fetchall()


def fetch_one(connection, sql, values=()):
    rows = fetch_all(connection, sql, values)
    return rows[0] if rows else None


def execute(connection, sql, values=()):
    with connection.cursor() as cursor:
        cursor.execute(sql, values)
        return cursor.lastrowid, cursor.rowcount


# Users

def users_find_by(connection, column, value):
    if column not in ('id', 'email', 'username'):
        raise ValueError('Unsupported user lookup')
    return fetch_one(connection, 'SELECT * FROM users WHERE ' + column + ' = %s', (value,))

def users_create(connection, values):
    return execute(connection, 'INSERT INTO users (username,email,password,verify_token,verify_expires_at) VALUES (%s,%s,%s,%s,DATE_ADD(NOW(), INTERVAL 24 HOUR))', values)

def users_confirm(connection, values):
    return execute(connection, 'UPDATE users SET is_verified=1,verify_token=NULL,verify_expires_at=NULL WHERE verify_token=%s AND verify_expires_at>NOW()', values)

def users_set_reset_token(connection, values):
    return execute(connection, 'UPDATE users SET reset_token=%s,reset_expires_at=DATE_ADD(NOW(),INTERVAL 1 HOUR) WHERE id=%s', values)

def users_find_reset_token(connection, values):
    return fetch_one(connection, 'SELECT * FROM users WHERE reset_token=%s AND reset_expires_at>NOW() FOR UPDATE', values)

def users_update_password(connection, values):
    return execute(connection, 'UPDATE users SET password=%s,session_version=session_version+1,reset_token=NULL,reset_expires_at=NULL,pending_email=NULL,email_change_token=NULL,email_change_expires_at=NULL WHERE id=%s', values)

def users_update_username(connection, values):
    return execute(connection, 'UPDATE users SET username=%s WHERE id=%s', values)

def users_update_notifications(connection, values):
    return execute(connection, 'UPDATE users SET notify_on_comment=%s WHERE id=%s', values)

def users_request_email_change(connection, values):
    return execute(connection, 'UPDATE users SET pending_email=%s,email_change_token=%s,email_change_expires_at=DATE_ADD(NOW(),INTERVAL 1 HOUR) WHERE id=%s', values)

def users_find_email_change(connection, values):
    return fetch_one(connection, 'SELECT * FROM users WHERE email_change_token=%s AND email_change_expires_at>NOW() FOR UPDATE', values)

def users_confirm_email_change(connection, values):
    return execute(connection, 'UPDATE users SET email=pending_email,pending_email=NULL,email_change_token=NULL,email_change_expires_at=NULL,reset_token=NULL,reset_expires_at=NULL,session_version=session_version+1 WHERE id=%s', values)


# Images

def images_paginate(connection, values):
    return fetch_all(connection, 'SELECT i.*,u.username,(SELECT COUNT(*) FROM likes l WHERE l.image_id=i.id) AS like_count FROM images i JOIN users u ON u.id=i.user_id ORDER BY i.created_at DESC,i.id DESC LIMIT 5 OFFSET %s', values)

def images_count(connection):
    return fetch_one(connection, 'SELECT COUNT(*) AS n FROM images')

def images_has_liked(connection, values):
    return fetch_one(connection, 'SELECT 1 FROM likes WHERE user_id=%s AND image_id=%s', values)

def images_find_for_update(connection, values):
    return fetch_one(connection, 'SELECT * FROM images WHERE id=%s FOR UPDATE', values)

def images_unlike(connection, values):
    return execute(connection, 'DELETE FROM likes WHERE user_id=%s AND image_id=%s', values)

def images_like(connection, values):
    return execute(connection, 'INSERT INTO likes (user_id,image_id) VALUES (%s,%s)', values)

def images_like_count(connection, values):
    return fetch_one(connection, 'SELECT COUNT(*) AS n FROM likes WHERE image_id=%s', values)

def images_by_user(connection, values):
    return fetch_all(connection, 'SELECT * FROM images WHERE user_id=%s ORDER BY id DESC', values)

def images_create(connection, values):
    return execute(connection, 'INSERT INTO images (user_id,path) VALUES (%s,%s)', values)

def images_delete(connection, values):
    return execute(connection, 'DELETE FROM images WHERE id=%s', values)


# Comments

def comments_by_image(connection, values):
    return fetch_all(connection, 'SELECT c.content,u.username FROM comments c JOIN users u ON u.id=c.user_id WHERE c.image_id=%s ORDER BY c.id', values)

def comments_create(connection, values):
    return execute(connection, 'INSERT INTO comments (image_id,user_id,content) VALUES (%s,%s,%s)', values)


# Overlays

def overlays_all(connection):
    return fetch_all(connection, 'SELECT * FROM overlays ORDER BY id')


# Sessions

def sessions_expire(connection, values):
    return execute(connection, 'DELETE FROM sessions WHERE expires_at < %s', values)

def sessions_find(connection, values):
    return fetch_one(connection, 'SELECT * FROM sessions WHERE id = %s AND expires_at >= %s FOR UPDATE', values)

def sessions_create_anonymous(connection, values):
    return execute(connection, 'INSERT INTO sessions (id, csrf_token, expires_at) VALUES (%s,%s,%s)', values)

def sessions_delete(connection, values):
    return execute(connection, 'DELETE FROM sessions WHERE id = %s', values)

def sessions_create_authenticated(connection, values):
    return execute(connection, 'INSERT INTO sessions (id,user_id,session_version,csrf_token,expires_at) VALUES (%s,%s,%s,%s,%s)', values)
