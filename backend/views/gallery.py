"""Gallery HTML rendering."""
from .common import e, field, form, PASSWORD, PASSWORD_HELP, USER_ATTRS

def gallery(images, page, pages, token, user):
    cards = []
    for image in images:
        ident = image['id']
        likes = f'''<button class="like-btn {('liked' if image['liked'] else '')}" data-id="{ident}">💞 <span class="like-count">{image['like_count']}</span></button>''' if user else f"<span>💞 {image['like_count']}</span>"
        comments = ''.join((f"""<div class="comment"><span class="author">{e(c['username'])}</span> {e(c['content'])}</div>""" for c in image['comments']))
        comment_form = f'<form class="comment-form" data-id="{ident}"><input name="content" placeholder="Say something nice..." maxlength="500" required><button class="btn btn-ghost">Post</button></form>' if user else ''
        cards.append(f"""<article class="gallery-card" id="img-{ident}"><img src="/uploads/{e(image['path'])}" alt="Image by {e(image['username'])}"><div class="meta"><span>{e(image['username'])}</span>{likes}</div><div class="comments"><div class="comment-list">{comments}</div>{comment_form}</div></article>""")
    pagination = ''.join((f'<a href="/?page=home&p={i}">{i}</a>' for i in range(max(1, page - 2), min(pages, page + 2) + 1)))
    return '<h1>🐱 Galerrry</h1>' + ('' if images else '<p>No photos yet. <a href="/?page=editor">Be the first to post!</a></p>') + '<div class="gallery-grid">' + ''.join(cards) + '</div>' + f'<div class="pagination" id="pagination">{pagination}</div>' + f'<div id="gallery-config" data-csrf="{e(token)}" data-logged-in="{str(bool(user)).lower()}" data-page="{page}" data-pages="{pages}"></div>' + '<div id="scroll-sentinel" style="height:1px"></div><p id="scroll-loader" style="display:none">Loading...</p>' + '<button id="scroll-retry" class="btn btn-ghost" style="display:none">Could not load images. Retry</button>' + '<script src="/js/gallery.js"></script>'
