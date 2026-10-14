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
    expected_prefix = "data:image/png;base64,"
    if not data_url.startswith(expected_prefix):
        raise ValueError("Invalid image data.")

    try:
        image_text = data_url[len(expected_prefix) :]
        image_bytes = base64.b64decode(image_text, validate=True)
        sticker_list = json.loads(sticker_json)
    except (ValueError, binascii.Error):
        raise ValueError("Invalid image or sticker data.") from None

    if not image_bytes or len(image_bytes) > MAX_BYTES:
        raise ValueError("Image must be at most 5 MB.")

    if not isinstance(sticker_list, list) or not 1 <= len(sticker_list) <= 20:
        raise ValueError("Pick between one and twenty overlays.")

    try:
        with Image.open(io.BytesIO(image_bytes), formats=["PNG"]) as original_image:
            image_width, image_height = original_image.size
            if (
                max(image_width, image_height) > 4000
                or image_width * image_height > 16000000
            ):
                raise ValueError("Image dimensions must be at most 4000 x 4000.")
            original_image.load()
            final_image = original_image.convert("RGBA")
            final_image = final_image.resize(
                (600, 600), Image.Resampling.LANCZOS
            )
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValueError("Could not decode the image.") from None

    allowed_overlay_paths = {}
    for overlay in overlays:
        overlay_id = int(overlay["id"])
        allowed_overlay_paths[overlay_id] = overlay["path"]

    for sticker in sticker_list:
        if not isinstance(sticker, dict):
            raise ValueError("Invalid overlay.")

        try:
            sticker_id = sticker["id"]
            x_position = sticker["x"]
            y_position = sticker["y"]
            sticker_width = sticker["w"]
            sticker_height = sticker["h"]
            sticker_values = [
                sticker_id,
                x_position,
                y_position,
                sticker_width,
                sticker_height,
            ]

            for value in sticker_values:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError()
                if not math.isfinite(value):
                    raise ValueError()

            sticker_id = int(sticker_id)
            x_position = int(x_position)
            y_position = int(y_position)
            sticker_width = int(sticker_width)
            sticker_height = int(sticker_height)

            if sticker_id not in allowed_overlay_paths:
                raise ValueError()
            if not (0 <= x_position < 600 and 0 <= y_position < 600):
                raise ValueError()
            if not (1 <= sticker_width <= 600 and 1 <= sticker_height <= 600):
                raise ValueError()

            overlay_filename = Path(allowed_overlay_paths[sticker_id]).name
            overlay_path = Path(root) / "overlays" / overlay_filename

            with Image.open(overlay_path, formats=["PNG"]) as overlay_image:
                overlay_image = overlay_image.convert("RGBA")
                overlay_image = overlay_image.resize(
                    (sticker_width, sticker_height), Image.Resampling.LANCZOS
                )
                final_image.alpha_composite(
                    overlay_image, dest=(x_position, y_position)
                )
        except (KeyError, TypeError, ValueError, OSError, UnidentifiedImageError):
            raise ValueError("Pick a valid overlay and position.") from None

    result = io.BytesIO()
    final_image.save(result, format="PNG")
    return result.getvalue()
