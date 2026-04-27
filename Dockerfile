FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# OCRmyPDF requires Tesseract/Ghostscript and related PDF/image utilities.
# libzbar0: runtime library for pyzbar (QR decoding).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ghostscript \
        tesseract-ocr \
        qpdf \
        pngquant \
        unpaper \
        libzbar0 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip \
    && pip install .

RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid 1000 --create-home --shell /usr/sbin/nologin app \
    && chown -R 1000:1000 /app

USER 1000:1000

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
