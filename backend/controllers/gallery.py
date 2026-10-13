"""Gallery request handling: coordinate models and views."""
from .. import views, mail
from .base import BaseController


class GalleryController(BaseController):
    def gallery(self):
        page = self.number(self.request.query.get('p', '1'))
        images = self.images.paginate(((page - 1) * 5,))
        total = self.images.count()['n']
        for image in images:
            image['comments'] = self.comments.by_image((image['id'],))
            image['liked'] = bool(self.request.user and self.images.has_liked((self.request.user['id'], image['id'])))
        pages = (total + 4) // 5
        if self.request.page == 'gallery-json':
            return self.request.json({'images': images, 'page': page, 'pages': pages})
        return self.request.html(views.gallery(images, page, pages, self.request.session['csrf_token'], self.request.user))

    def interaction(self):
        self.require_user()
        ident = self.number(self.request.data.get('image_id'))
        image = self.images.find_for_update((ident,))
        if not image:
            self.fail('Image not found.', 404)
        uid = self.request.user['id']
        if self.request.page == 'like-ajax':
            liked = self.images.has_liked((uid, ident))
            if liked:
                self.images.unlike((uid, ident))
            else:
                self.images.like((uid, ident))
            count = self.images.like_count((ident,))['n']
            return self.request.json({'liked': not bool(liked), 'count': count})
        content = self.request.data.get('content', '').strip()
        if not 1 <= len(content) <= 500:
            self.fail('Comment must contain 1–500 characters.')
        self.comments.create((ident, uid, content))
        owner = self.get_user('id', image['user_id'])
        if owner['notify_on_comment']:
            mail.send(owner['email'], 'New comment on your Camagru image', f"{self.request.user['username']} commented:\n\n{content}")
        return self.request.json({'username': self.request.user['username'], 'content': content})

