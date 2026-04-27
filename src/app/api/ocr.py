import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

router = APIRouter(tags=["ocr"])


def _save_uploaded_pdf(upload: UploadFile, input_path: str) -> None:
    with Path(input_path).open("wb") as output_file:
        shutil.copyfileobj(upload.file, output_file)


def _run_ocr(
    input_path: str,
    output_path: str,
    *,
    language: str | None,
    deskew: bool,
    force_ocr: bool,
    optimize: int | None,
) -> None:
    import ocrmypdf

    options: dict[str, Any] = {
        "deskew": deskew,
        "force_ocr": force_ocr,
    }
    if language:
        options["language"] = language
    if optimize is not None:
        options["optimize"] = optimize

    ocrmypdf.ocr(input_path, output_path, **options)


@router.post("/ocr")
async def post_ocr(
    file: UploadFile = File(...),
    language: str | None = Query(default=None, min_length=2, max_length=32),
    deskew: bool = Query(default=False),
    force_ocr: bool = Query(default=False),
    optimize: int | None = Query(default=None, ge=0, le=3),
) -> FileResponse:
    has_pdf_filename = bool(file.filename and file.filename.lower().endswith(".pdf"))
    if file.content_type != "application/pdf" and not has_pdf_filename:
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF.")

    temp_dir = tempfile.mkdtemp(prefix="ocr-api-")
    input_path = os.path.join(temp_dir, "input.pdf")
    output_path = os.path.join(temp_dir, "output.pdf")

    try:
        await file.seek(0)
        await asyncio.to_thread(_save_uploaded_pdf, file, input_path)
        await asyncio.to_thread(
            _run_ocr,
            input_path,
            output_path,
            language=language,
            deskew=deskew,
            force_ocr=force_ocr,
            optimize=optimize,
        )
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(
            status_code=500, detail=f"OCR processing failed: {exc}"
        ) from exc
    finally:
        await file.close()

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename="ocr-output.pdf",
        background=BackgroundTask(shutil.rmtree, temp_dir, True),
    )
