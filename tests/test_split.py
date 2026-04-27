import io
import zipfile

from fastapi.testclient import TestClient

from app.main import app


def test_split_endpoint_returns_zip(monkeypatch) -> None:
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("page_1.pdf", b"%PDF-1.4 stub")
    zip_bytes = zip_buf.getvalue()

    def fake_split_pdf_to_zip(input_path: str, zip_path: str) -> None:
        with open(zip_path, "wb") as out:
            out.write(zip_bytes)

    monkeypatch.setattr("app.api.split._split_pdf_to_zip", fake_split_pdf_to_zip)

    client = TestClient(app)
    response = client.post(
        "/split",
        files={"file": ("sample.pdf", b"%PDF-1.4\n", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/zip")
    assert response.content == zip_bytes


def test_split_endpoint_rejects_non_pdf_upload() -> None:
    client = TestClient(app)
    response = client.post(
        "/split",
        files={"file": ("note.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file must be a PDF."


def test_split_endpoint_returns_400_when_pdf_has_no_pages(monkeypatch) -> None:
    from app.api.split import _EmptyPdfError

    def empty_pdf(_input_path: str, _zip_path: str) -> None:
        raise _EmptyPdfError()

    monkeypatch.setattr("app.api.split._split_pdf_to_zip", empty_pdf)

    client = TestClient(app)
    response = client.post(
        "/split",
        files={"file": ("sample.pdf", b"%PDF-1.4\n", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "PDF has no pages."


def test_split_endpoint_returns_500_on_split_failure(monkeypatch) -> None:
    def failing_split(_input_path: str, _zip_path: str) -> None:
        raise RuntimeError("split failed")

    monkeypatch.setattr("app.api.split._split_pdf_to_zip", failing_split)

    client = TestClient(app)
    response = client.post(
        "/split",
        files={"file": ("sample.pdf", b"%PDF-1.4\n", "application/pdf")},
    )

    assert response.status_code == 500
    assert "PDF split failed: split failed" in response.json()["detail"]
