import asyncio
import io
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

router = APIRouter(tags=["split"])


class _EmptyPdfError(Exception):
    """Raised when the PDF has zero pages (caller maps to HTTP 400)."""


def _save_uploaded_pdf(upload: UploadFile, input_path: str) -> None:
    with Path(input_path).open("wb") as output_file:
        shutil.copyfileobj(upload.file, output_file)


def _split_pdf_to_zip(input_path: str, zip_path: str) -> None:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(input_path)
    try:
        page_count = len(pdf)
        if page_count == 0:
            raise _EmptyPdfError()

        pad = len(str(page_count))
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for i in range(page_count):
                new_doc = pdfium.PdfDocument.new()
                try:
                    new_doc.import_pages(pdf, [i])
                    buf = io.BytesIO()
                    new_doc.save(buf)
                    name = f"page_{i + 1:0{pad}d}.pdf"
                    zf.writestr(name, buf.getvalue())
                finally:
                    try:
                        new_doc.close()
                    except Exception:
                        pass
    finally:
        try:
            pdf.close()
        except Exception:
            pass


@router.post("/split")
async def post_split(file: UploadFile = File(...)) -> FileResponse:
    has_pdf_filename = bool(file.filename and file.filename.lower().endswith(".pdf"))
    if file.content_type != "application/pdf" and not has_pdf_filename:
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF.")

    temp_dir = tempfile.mkdtemp(prefix="ocr-api-split-")
    input_path = os.path.join(temp_dir, "input.pdf")
    zip_path = os.path.join(temp_dir, "split-pages.zip")

    try:
        await file.seek(0)
        await asyncio.to_thread(_save_uploaded_pdf, file, input_path)
        try:
            await asyncio.to_thread(_split_pdf_to_zip, input_path, zip_path)
        except _EmptyPdfError as exc:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise HTTPException(status_code=400, detail="PDF has no pages.") from exc
    except HTTPException:
        raise
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(
            status_code=500, detail=f"PDF split failed: {exc}"
        ) from exc
    finally:
        await file.close()

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="split-pages.zip",
        background=BackgroundTask(shutil.rmtree, temp_dir, True),
    )
