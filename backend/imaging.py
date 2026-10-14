"""Server-side image decoding and composition (PHP equivalent: GD)."""

import base64
import binascii
import io
import json
import math
from pathlib import Path
from PIL import Image, UnidentifiedImageError

MAX_BYTES = 5 * 1024 * 1024


def compose(data_url, sticker_json, overlays, root):
    prefix = "data:image/png;base64,"
    if not data_url.startswith(prefix):
        raise ValueError("Invalid image data.")
    try:
        # PHP: base64_decode($value, true); json_decode($json, true) parses stickers.
        raw = base64.b64decode(data_url[len(prefix) :], validate=True)
        stickers = json.loads(sticker_json)
    except (ValueError, binascii.Error):
        raise ValueError("Invalid image or sticker data.") from None
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("Image must be at most 5 MB.")
    if not isinstance(stickers, list) or not 1 <= len(stickers) <= 20:
        raise ValueError("Pick between one and twenty overlays.")
    try:
        # PHP GD extension: imagecreatefromstring(), imagesx(), imagesy().
        with Image.open(io.BytesIO(raw), formats=["PNG"]) as base:
            if max(base.size) > 4000 or base.width * base.height > 16000000:
                raise ValueError("Image dimensions must be at most 4000 x 4000.")
            base.load()
            # PHP GD: imagecreatetruecolor() + imagecopyresampled();
            # imagesavealpha() configures alpha preservation.
            out = base.convert("RGBA").resize((600, 600), Image.Resampling.LANCZOS)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValueError("Could not decode the image.") from None
    allowed = {int(item["id"]): item["path"] for item in overlays}
    for sticker in stickers:
        if not isinstance(sticker, dict):
            raise ValueError("Invalid overlay.")
        try:
            values = [sticker[k] for k in ("id", "x", "y", "w", "h")]
            if any(
                isinstance(v, bool)
                or not isinstance(v, (int, float))
                or not math.isfinite(v)
                for v in values
            ):
                raise ValueError()
            ident, x, y, width, height = map(int, values)
            if ident not in allowed or not (
                0 <= x < 600
                and 0 <= y < 600
                and 1 <= width <= 600
                and 1 <= height <= 600
            ):
                raise ValueError()
            # PHP: basename() extracts the filename from a path.
            path = Path(root) / "overlays" / Path(allowed[ident]).name
            with Image.open(path, formats=["PNG"]) as overlay:
                layer = overlay.convert("RGBA").resize(
                    (width, height), Image.Resampling.LANCZOS
                )
                # PHP GD: imagecopy() with alpha blending enabled.
                # Equivalent capability; resampling/compositing need not produce identical pixels.
                out.alpha_composite(layer, dest=(x, y))
        except (KeyError, TypeError, ValueError, OSError, UnidentifiedImageError):
            raise ValueError("Pick a valid overlay and position.") from None
    result = io.BytesIO()
    # PHP GD: imagepng(); output buffering can collect the encoded bytes.
    out.save(result, format="PNG")
    return result.getvalue()
