from app.core.config import get_settings
from app.services import receipts

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20
JPEG = b"\xff\xd8\xff\xe0" + b"0" * 20
PDF = b"%PDF-1.7\n" + b"0" * 20


def test_detect_type_by_content():
    assert receipts.detect_type(PNG) == ("image/png", ".png")
    assert receipts.detect_type(JPEG) == ("image/jpeg", ".jpg")
    assert receipts.detect_type(PDF) == ("application/pdf", ".pdf")


def test_unknown_content_is_rejected():
    assert receipts.detect_type(b"hello world") is None
    assert receipts.detect_type(b"") is None
    # скрипт с «безобидным» именем — всё равно не картинка
    assert receipts.detect_type(b"<script>alert(1)</script>") is None


def test_save_and_delete(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path))
    name = receipts.save_receipt(PNG, ".png")
    assert name.endswith(".png")
    assert receipts.receipt_path(name).read_bytes() == PNG
    receipts.delete_receipt(name)
    assert not receipts.receipt_path(name).exists()
    receipts.delete_receipt(name)  # повторное удаление не падает
    receipts.delete_receipt(None)


def test_receipt_path_cannot_leave_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path))
    assert receipts.receipt_path("../../etc/passwd").parent == tmp_path / "receipts"
