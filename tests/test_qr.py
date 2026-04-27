from fastapi.testclient import TestClient

from app.main import app


def test_qr_endpoint_returns_qr_list(monkeypatch) -> None:
    def fake_extract(_input_path: str) -> list[str]:
        return ["hello", "https://example.com"]

    monkeypatch.setattr("app.api.qr._extract_qr_codes", fake_extract)

    client = TestClient(app)
    response = client.post(
        "/qr",
        files={"file": ("sample.pdf", b"%PDF-1.4\n", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json() == {"qr_codes": ["hello", "https://example.com"]}


def test_qr_endpoint_empty_when_no_qr_found(monkeypatch) -> None:
    def fake_empty(_input_path: str) -> list[str]:
        return []

    monkeypatch.setattr("app.api.qr._extract_qr_codes", fake_empty)

    client = TestClient(app)
    response = client.post(
        "/qr",
        files={"file": ("sample.pdf", b"%PDF-1.4\n", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json() == {"qr_codes": []}


def test_qr_endpoint_does_not_fail_when_extractor_raises(monkeypatch) -> None:
    def bad_extract(_input_path: str) -> list[str]:
        raise RuntimeError("decode failed")

    monkeypatch.setattr("app.api.qr._extract_qr_codes", bad_extract)

    client = TestClient(app)
    response = client.post(
        "/qr",
        files={"file": ("sample.pdf", b"%PDF-1.4\n", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json() == {"qr_codes": []}


def test_qr_endpoint_rejects_non_pdf_upload() -> None:
    client = TestClient(app)
    response = client.post(
        "/qr",
        files={"file": ("note.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file must be a PDF."
