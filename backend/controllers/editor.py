"""Editor request handling: coordinate models and views."""
import secrets
from pathlib import Path
from .. import views, imaging
from .base import BaseController

ROOT = Path(__file__).resolve().parents[2] / "public"


class EditorController(BaseController):
    def editor(self):
        self.require_user()
        overlays = self.overlays.all()
        images = self.images.by_user((self.request.user['id'],))
        preview = self.request.query.get('preview', '')
        if preview and (not any((i['path'] == preview for i in images))):
            preview = ''
        return self.request.html(views.editor(overlays, images, self.request.session['csrf_token'], preview))

    def capture(self):
        self.require_user()
        try:
            raw = imaging.compose(self.request.data.get('image_data', ''), self.request.data.get('stickers', '[]'), self.overlays.all(), ROOT)
        except ValueError as error:
            self.fail(str(error))
        name = secrets.token_hex(16) + '.png'
        path = ROOT / 'uploads' / name
        path.write_bytes(raw)
        try:
            self.images.create((self.request.user['id'], name))
            self.request.db.connection.commit()
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return self.request.redirect('editor&preview=' + name)

    def delete(self):
        self.require_user()
        ident = self.number(self.request.data.get('image_id'))
        image = self.images.find_for_update((ident,))
        if not image or image['user_id'] != self.request.user['id']:
            self.fail('You can delete only your own photos.', 403)
        self.images.delete((ident,))
        self.request.db.connection.commit()
        (ROOT / 'uploads' / Path(image['path']).name).unlink(missing_ok=True)
        return self.request.redirect('editor')

