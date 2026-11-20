"""Хранение файлов чеков на диске. Тип определяется по содержимому, а не по имени файла."""

from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings

MAX_RECEIPT_BYTES = 5 * 1024 * 1024  # 5 МБ

# (начало файла, MIME-тип, расширение)
_SIGNATURES = [
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
    (b"%PDF-", "application/pdf", ".pdf"),
]


def detect_type(data: bytes) -> tuple[str, str] | None:
    """(MIME-тип, расширение) для JPEG, PNG или PDF; для остального None."""
    for signature, mime, extension in _SIGNATURES:
        if data.startswith(signature):
            return mime, extension
    return None


def _directory() -> Path:
    directory = Path(get_settings().upload_dir) / "receipts"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_receipt(data: bytes, extension: str) -> str:
    """Сохраняет файл под случайным именем и возвращает это имя."""
    name = f"{uuid4().hex}{extension}"
    (_directory() / name).write_bytes(data)
    return name


def receipt_path(name: str) -> Path:
    # Имя берётся из базы, но на всякий случай не даём выйти из папки чеков.
    return _directory() / Path(name).name


def delete_receipt(name: str | None) -> None:
    if name:
        receipt_path(name).unlink(missing_ok=True)
