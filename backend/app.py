"""Camagru page actions: account, gallery and editor (the controller layer)."""

import json
import os
import secrets
from pathlib import Path
import pymysql
from . import database, security, views, mail, imaging
from .security import Problem

ROOT = Path(__file__).resolve().parent.parent / "public"


def require_user(request):
    if not request["user"]:
        raise Problem("Please log in.", 401)


def html(request, body, status=200):
    text = views.layout(
        request["page"].title(),
        body,
        request["session"]["csrf_token"],
        request["user"],
        request["message"],
        request["error"],
    )
    return (status, [("Content-Type", "text/html; charset=utf-8")], text.encode())


def redirect(page):
    return (303, [("Location", "/?page=" + page)], b"")


def json_response(result, status=200):
    return (
        status,
        [("Content-Type", "application/json")],
        json.dumps(result, default=str).encode(),
    )


def show(request):
    return html(
        request, views.auth(request["page"], request["session"]["csrf_token"], {})
    )


# Account actions


def register(request):
    username = request["data"].get("username", "").strip()
    email = request["data"].get("email", "").strip()
    password = request["data"].get("password", "")
    security.check_username(username)
    security.check_email(email)
    security.check_password(password)
    if database.users_find_by(
        request["connection"], "username", username
    ) or database.users_find_by(request["connection"], "email", email):
        security.fail("Username or email already taken.")
    token = secrets.token_hex(32)
    database.users_create(
        request["connection"],
        (username, email, security.password_hash(password), token),
    )
    mail.send_link(email, "Confirm your Camagru account", "confirm", token)
    return redirect("register-done")


def confirm(request):
    token = request["query"].get("token", "")
    if not security.TOKEN.fullmatch(token):
        security.fail("Invalid confirmation link.")
    _, count = database.users_confirm(request["connection"], (token,))
    if not count:
        security.fail("This confirmation link is invalid or has expired.")
    request["message"] = "Email confirmed! You can now log in."
    return html(request, views.auth("login", request["session"]["csrf_token"], {}))


def login(request):
    user = database.users_find_by(
        request["connection"], "username", request["data"].get("username", "").strip()
    )
    if not user or not security.password_matches(
        request["data"].get("password", ""), user["password"]
    ):
        security.fail("Invalid username or password.")
    if not user["is_verified"]:
        security.fail("Please confirm your email address before logging in.")
    request["sid"] = security.rotate(request["connection"], request["session"], user)
    request["user"] = user
    return redirect("home")


def logout(request):
    request["sid"] = security.rotate(request["connection"], request["session"])
    request["user"] = None
    return redirect("login")


def forgot(request):
    email = request["data"].get("email", "").strip()
    security.check_email(email)
    user = database.users_find_by(request["connection"], "email", email)
    if user:
        token = secrets.token_hex(32)
        database.users_set_reset_token(request["connection"], (token, user["id"]))
        mail.send_link(email, "Reset your Camagru password", "reset", token)
    request["message"] = (
        "If that email is registered you will receive a reset link shortly."
    )
    return html(request, views.auth("forgot", request["session"]["csrf_token"], {}))


def reset(request):
    token = (request["data"] if request["method"] == "POST" else request["query"]).get(
        "token", ""
    )
    if not security.TOKEN.fullmatch(token):
        security.fail("Invalid reset link.")
    user = database.users_find_reset_token(request["connection"], (token,))
    if not user:
        security.fail("This reset link is invalid or has expired.")
    if request["method"] == "GET":
        return html(
            request,
            views.auth("reset", request["session"]["csrf_token"], {"token": token}),
        )
    password = request["data"].get("password", "")
    security.check_password(password)
    change_password(request, user["id"], password)
    request["sid"] = security.rotate(request["connection"], request["session"])
    request["user"] = None
    request["message"] = "Password updated! You can now log in."
    return html(request, views.auth("login", request["session"]["csrf_token"], {}))


def change_password(request, user_id, password):
    database.users_update_password(
        request["connection"], (security.password_hash(password), user_id)
    )


def profile(request):
    require_user(request)
    if request["method"] == "POST":
        action = request["data"].get("action", "")
        user_id = request["user"]["id"]
        if action == "username":
            username = request["data"].get("username", "").strip()
            security.check_username(username)
            database.users_update_username(request["connection"], (username, user_id))
        elif action == "notify":
            database.users_update_notifications(
                request["connection"],
                (int(request["data"].get("notify_on_comment") == "1"), user_id),
            )
        elif action in ("email", "password"):
            if not security.password_matches(
                request["data"].get("current_password", ""), request["user"]["password"]
            ):
                security.fail("Current password is incorrect.")
            if action == "password":
                password = request["data"].get("new_password", "")
                security.check_password(password)
                change_password(request, user_id, password)
                request["user"] = database.users_find_by(
                    request["connection"], "id", user_id
                )
                request["sid"] = security.rotate(
                    request["connection"], request["session"], request["user"]
                )
            else:
                email = request["data"].get("email", "").strip()
                security.check_email(email)
                if database.users_find_by(request["connection"], "email", email):
                    security.fail("Email already registered.")
                token = secrets.token_hex(32)
                database.users_request_email_change(
                    request["connection"], (email, security.token_hash(token), user_id)
                )
                mail.send_link(
                    email, "Confirm your new Camagru email", "confirm-email", token
                )
                request["message"] = "Check your new email to confirm the change."
        else:
            security.fail("Invalid profile action.")
        request["user"] = database.users_find_by(request["connection"], "id", user_id)
        request["message"] = request["message"] or "Preferences updated."
    return html(
        request, views.profile(request["user"], request["session"]["csrf_token"])
    )


def confirm_email(request):
    token = request["query"].get("token", "")
    if not security.TOKEN.fullmatch(token):
        security.fail("Invalid confirmation link.")
    user = database.users_find_email_change(
        request["connection"], (security.token_hash(token),)
    )
    if not user:
        security.fail("This confirmation link is invalid or has expired.")
    database.users_confirm_email_change(request["connection"], (user["id"],))
    if request["user"] and request["user"]["id"] == user["id"]:
        request["sid"] = security.rotate(request["connection"], request["session"])
        request["user"] = None
    request["message"] = "Email updated. Please log in again."
    return html(request, views.auth("login", request["session"]["csrf_token"], {}))


# Gallery actions

def gallery(request):
    page = security.number(request["query"].get("p", "1"))
    images = database.images_paginate(request["connection"], ((page - 1) * 5,))
    total = database.images_count(request["connection"])["n"]
    for image in images:
        image["comments"] = database.comments_by_image(
            request["connection"], (image["id"],)
        )
        image["liked"] = bool(
            request["user"]
            and database.images_has_liked(
                request["connection"], (request["user"]["id"], image["id"])
            )
        )
    pages = (total + 4) // 5
    if request["page"] == "gallery-json":
        return json_response({"images": images, "page": page, "pages": pages})
    return html(
        request,
        views.gallery(
            images, page, pages, request["session"]["csrf_token"], request["user"]
        ),
    )


def interaction(request):
    require_user(request)
    image_id = security.number(request["data"].get("image_id"))
    image = database.images_find_for_update(request["connection"], (image_id,))
    if not image:
        security.fail("Image not found.", 404)
    user_id = request["user"]["id"]
    if request["page"] == "like-ajax":
        liked = database.images_has_liked(request["connection"], (user_id, image_id))
        if liked:
            database.images_unlike(request["connection"], (user_id, image_id))
        else:
            database.images_like(request["connection"], (user_id, image_id))
        count = database.images_like_count(request["connection"], (image_id,))["n"]
        return json_response({"liked": not bool(liked), "count": count})
    content = request["data"].get("content", "").strip()
    if not 1 <= len(content) <= 500:
        security.fail("Comment must contain 1–500 characters.")
    database.comments_create(request["connection"], (image_id, user_id, content))
    owner = database.users_find_by(request["connection"], "id", image["user_id"])
    if owner["notify_on_comment"]:
        mail.send(
            owner["email"],
            "New comment on your Camagru image",
            f"{request['user']['username']} commented:\n\n{content}",
        )
    return json_response({"username": request["user"]["username"], "content": content})


# Editor actions


def editor(request):
    require_user(request)
    overlays = database.overlays_all(request["connection"])
    images = database.images_by_user(request["connection"], (request["user"]["id"],))
    preview = request["query"].get("preview", "")
    if preview and (not any((i["path"] == preview for i in images))):
        preview = ""
    return html(
        request,
        views.editor(overlays, images, request["session"]["csrf_token"], preview),
    )


def capture(request):
    require_user(request)
    try:
        image_bytes = imaging.compose(
            request["data"].get("image_data", ""),
            request["data"].get("stickers", "[]"),
            database.overlays_all(request["connection"]),
            ROOT,
        )
    except ValueError as error:
        security.fail(str(error))
    filename = secrets.token_hex(16) + ".png"
    upload_path = ROOT / "uploads" / filename
    upload_path.write_bytes(image_bytes)
    try:
        database.images_create(request["connection"], (request["user"]["id"], filename))
        request["connection"].commit()
    except Exception:
        upload_path.unlink(missing_ok=True)
        raise
    return redirect("editor&preview=" + filename)


def delete(request):
    require_user(request)
    image_id = security.number(request["data"].get("image_id"))
    image = database.images_find_for_update(request["connection"], (image_id,))
    if not image or image["user_id"] != request["user"]["id"]:
        security.fail("You can delete only your own photos.", 403)
    database.images_delete(request["connection"], (image_id,))
    request["connection"].commit()
    (ROOT / "uploads" / Path(image["path"]).name).unlink(missing_ok=True)
    return redirect("editor")


# Routing and request lifecycle


def dispatch(request):
    if request["method"] == "POST":
        expected = os.environ.get("APP_URL", "http://localhost:8000").rstrip("/")
        if request["origin"] and request["origin"].rstrip("/") != expected:
            raise Problem("Invalid request origin.", 403)
        supplied = request["data"].get("_csrf_token", "")
        if not security.TOKEN.fullmatch(supplied) or not secrets.compare_digest(
            supplied, request["session"]["csrf_token"]
        ):
            raise Problem("Invalid CSRF token.", 403)
        routes = {
            "register": register,
            "login": login,
            "logout": logout,
            "forgot": forgot,
            "reset": reset,
            "profile": profile,
            "capture": capture,
            "delete-image": delete,
            "like-ajax": interaction,
            "comment-ajax": interaction,
        }
    else:
        routes = {
            "home": gallery,
            "gallery-json": gallery,
            "editor": editor,
            "confirm": confirm,
            "confirm-email": confirm_email,
            "reset": reset,
            "profile": profile,
        }
        if request["page"] in ("login", "register", "forgot", "register-done"):
            return show(request)
    if request["page"] not in routes:
        raise Problem("Page not found.", 404)
    return routes[request["page"]](request)


def handle(method, page, query, data, cookie, origin):
    connection = database.connect()
    request = dict(
        method=method,
        page=page,
        query=query,
        data=data,
        cookie=cookie,
        origin=origin,
        connection=connection,
        sid="",
        session=None,
        user=None,
        message="",
        error=False,
    )
    try:
        request["sid"], request["session"] = security.session(
            connection, request["cookie"]
        )
        if request["session"]["user_id"]:
            request["user"] = database.users_find_by(
                connection, "id", request["session"]["user_id"]
            )
            if (
                not request["user"]
                or request["user"]["session_version"]
                != request["session"]["session_version"]
            ):
                request["sid"] = security.rotate(connection, request["session"])
                request["user"] = None
        connection.commit()
        try:
            result = dispatch(request)
            connection.commit()
        except (Problem, pymysql.IntegrityError) as error:
            connection.rollback()
            if isinstance(error, pymysql.IntegrityError):
                error = Problem("Username or email already taken.")
            request["message"], request["error"] = (error.message, True)
            if request["page"] in ("like-ajax", "comment-ajax"):
                result = json_response({"error": error.message}, error.status)
            elif error.status == 401:
                result = redirect("login")
            elif request["page"] in ("register", "login", "forgot"):
                status = 200 if error.status == 400 else error.status
                result = html(
                    request,
                    views.auth(
                        request["page"],
                        request["session"]["csrf_token"],
                        request["data"],
                    ),
                    status,
                )
            elif request["page"] == "profile" and request["user"]:
                status = 200 if error.status == 400 else error.status
                result = html(
                    request,
                    views.profile(request["user"], request["session"]["csrf_token"]),
                    status,
                )
            else:
                result = html(request, views.error(), error.status)
        status, headers, body = result
        secure = (
            "; Secure" if os.environ.get("APP_URL", "").startswith("https://") else ""
        )
        headers.append(
            (
                "Set-Cookie",
                f"camagru_session={request['sid']}; Path=/; HttpOnly; "
                f"SameSite=Lax{secure}",
            )
        )
        return (status, headers, body)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
