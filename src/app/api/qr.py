import asyncio
import os
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(tags=["qr"])


def _save_uploaded_pdf(upload: UploadFile, input_path: str) -> None:
    with Path(input_path).open("wb") as output_file:
        shutil.copyfileobj(upload.file, output_file)


def _extract_qr_codes(input_path: str) -> list[str]:
    """Return decoded QR text for each code found, or an empty list on any failure.

    Heavy deps are imported here so the app can load in environments where zbar
    is not installed (e.g. dev machines); those runs simply yield [].
    """
    try:
        import pypdfium2 as pdfium
        from pyzbar.pyzbar import ZBarSymbol, decode
    except Exception:  # pragma: no cover - import when libzbar missing
        return []

    results: list[str] = []
    try:
        pdf = pdfium.PdfDocument(input_path)
    except Exception:
        return []
    try:
        for i in range(len(pdf)):
            page = pdf[i]
            try:
                render = page.render(scale=2.0)
                try:
                    image = render.to_pil()
                    for sym in decode(image, symbols=[ZBarSymbol.QRCODE]):
                        results.append(sym.data.decode("utf-8", errors="replace"))
                except Exception:
                    pass
                finally:
                    render.close()
            except Exception:
                pass
            finally:
                try:
                    page.close()
                except Exception:
                    pass
    except Exception:
        return []
    finally:
        try:
            pdf.close()
        except Exception:
            pass
    return results


@router.post("/qr")
async def post_qr(file: UploadFile = File(...)) -> dict[str, list[str]]:
    has_pdf_filename = bool(file.filename and file.filename.lower().endswith(".pdf"))
    if file.content_type != "application/pdf" and not has_pdf_filename:
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF.")

    temp_dir = tempfile.mkdtemp(prefix="ocr-api-qr-")
    input_path = os.path.join(temp_dir, "input.pdf")
    try:
        try:
            await file.seek(0)
            await asyncio.to_thread(_save_uploaded_pdf, file, input_path)
        except Exception:
            return {"qr_codes": []}

        try:
            results = await asyncio.to_thread(_extract_qr_codes, input_path)
        except Exception:
            results = []
        return {"qr_codes": results}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        await file.close()
