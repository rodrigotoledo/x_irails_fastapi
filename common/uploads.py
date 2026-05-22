import uuid
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError


UPLOAD_ROOT = Path(__file__).resolve().parents[1] / "uploads"
AVATAR_DIR = UPLOAD_ROOT / "avatars"
MAX_AVATAR_BYTES = 5 * 1024 * 1024
AVATAR_SIZE = (400, 400)
ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def save_avatar_upload(file: UploadFile) -> str:
    extension = ALLOWED_CONTENT_TYPES.get(file.content_type or "")
    if extension is None:
        raise ValueError("Avatar must be a JPEG, PNG, or WebP image")

    content = file.file.read(MAX_AVATAR_BYTES + 1)
    if len(content) > MAX_AVATAR_BYTES:
        raise ValueError("Avatar must be 5MB or smaller")

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.webp"
    path = AVATAR_DIR / filename

    try:
        with Image.open(BytesIO(content)) as image:
            image = image.convert("RGB")
            image.thumbnail(AVATAR_SIZE)
            background = Image.new("RGB", AVATAR_SIZE, (255, 255, 255))
            left = (AVATAR_SIZE[0] - image.width) // 2
            top = (AVATAR_SIZE[1] - image.height) // 2
            background.paste(image, (left, top))
            background.save(path, "WEBP", quality=85, method=6)
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Avatar must be a valid image") from exc

    return f"/uploads/avatars/{filename}"
