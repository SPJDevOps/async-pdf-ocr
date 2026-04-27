# async-pdf-ocr

Async HTTP API for OCRmyPDF: minimal async-first FastAPI service with Docker/Kubernetes-friendly deployment.

## Requirements

- Python 3.13

## Quickstart

1. Create and activate a virtual environment:

   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

3. Configure environment:

   ```bash
   cp .env.example .env
   ```

4. Run the API:

   ```bash
   uvicorn app.main:app --reload
   ```

5. Verify health endpoint:

   ```bash
   curl http://127.0.0.1:8000/health
   ```

## Docker (Local)

Build the image:

```bash
docker build -t async-pdf-ocr:local .
```

Run the container:

```bash
docker run --rm -p 8000:8000 --name async-pdf-ocr async-pdf-ocr:local
```

Verify container health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

## OCR Endpoint

Process a PDF with OCRmyPDF:

```bash
curl -X POST "http://127.0.0.1:8000/ocr?language=eng&deskew=true&force_ocr=false&optimize=1" \
  -F "file=@/path/to/input.pdf" \
  --output ocr-output.pdf
```

### Supported query params

- `language` (optional string): OCR language code, e.g. `eng`
- `deskew` (optional bool, default `false`)
- `force_ocr` (optional bool, default `false`)
- `optimize` (optional int `0-3`)

## QR Code Endpoint

Scan a PDF for QR codes and return the decoded text for each (JSON). If none are found or scanning cannot run, the response is an empty list (HTTP 200). The container image includes `libzbar0` for QR decoding; on bare-metal installs, install your platform’s `zbar` library if `pyzbar` cannot load it.

```bash
curl -X POST "http://127.0.0.1:8000/qr" -F "file=@/path/to/input.pdf"
```

## Tests

Run tests with:

```bash
pytest
```

## Project Structure

- `src/app/main.py` - FastAPI app creation and router wiring
- `src/app/config.py` - environment-driven settings
- `src/app/api/health.py` - async health endpoint
- `src/app/api/ocr.py` - OCR upload endpoint
- `src/app/api/qr.py` - QR code scan upload endpoint
- `tests/test_health.py` - baseline health test
