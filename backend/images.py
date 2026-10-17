"""Image validation and resizing."""

from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError


def prepare_image(data: bytes, max_side: int, max_upload_mb: int = 10) -> tuple[bytes, str]:
    if len(data) > max_upload_mb * 1024 * 1024:
        raise ValueError("Photo is too large, please choose a smaller image")
    try:
        with Image.open(BytesIO(data)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
            output = BytesIO()
            image.save(output, format="JPEG", quality=80, optimize=True)
            return output.getvalue(), "image/jpeg"
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("Photo format not supported, please take a new photo") from exc
