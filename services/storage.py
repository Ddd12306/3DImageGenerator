import mimetypes
import uuid
import base64
from pathlib import Path
from urllib.parse import urlparse

import httpx

from config import OUTPUT_DIR, UPLOAD_DIR


def _extension_from_mime(mime_type: str | None, fallback: str = ".png") -> str:
    if not mime_type:
        return fallback
    return mimetypes.guess_extension(mime_type.split(";")[0].strip()) or fallback


def _safe_suffix(filename: str | None, mime_type: str | None) -> str:
    if filename:
        suffix = Path(filename).suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            return suffix
    return _extension_from_mime(mime_type)


def save_upload(user_id: int, image_bytes: bytes, filename: str | None, mime_type: str | None) -> str:
    suffix = _safe_suffix(filename, mime_type)
    rel_path = Path("uploads") / str(user_id) / f"{uuid.uuid4().hex}{suffix}"
    abs_path = UPLOAD_DIR.parent / rel_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_bytes(image_bytes)
    return rel_path.as_posix()


async def save_remote_output(user_id: int, source_url: str) -> tuple[str | None, str | None]:
    parsed = urlparse(source_url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        suffix = ".png"

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(source_url)
        response.raise_for_status()

    mime_type = response.headers.get("content-type", "").split(";")[0] or _mime_from_suffix(suffix)
    rel_path = Path("outputs") / str(user_id) / f"{uuid.uuid4().hex}{suffix}"
    abs_path = OUTPUT_DIR.parent / rel_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_bytes(response.content)
    return rel_path.as_posix(), mime_type


def save_base64_output(user_id: int, b64_json: str, mime_type: str = "image/png") -> tuple[str, str]:
    if "," in b64_json and b64_json.strip().startswith("data:"):
        header, b64_json = b64_json.split(",", 1)
        mime_type = header.removeprefix("data:").split(";", 1)[0] or mime_type

    suffix = _extension_from_mime(mime_type)
    rel_path = Path("outputs") / str(user_id) / f"{uuid.uuid4().hex}{suffix}"
    abs_path = OUTPUT_DIR.parent / rel_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_bytes(base64.b64decode(b64_json))
    return rel_path.as_posix(), mime_type


def resolve_data_path(relative_path: str) -> Path:
    base = OUTPUT_DIR.parent.resolve()
    path = (base / relative_path).resolve()
    if not str(path).startswith(str(base)):
        raise ValueError("非法文件路径")
    return path


def _mime_from_suffix(suffix: str) -> str:
    return mimetypes.types_map.get(suffix, "image/png")
