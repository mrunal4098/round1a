FROM --platform=linux/amd64 python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (none yet; add tesseract later)
RUN apt-get update && apt-get install -y --no-install-recommends fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

COPY assets/fonts /app/fonts
COPY requirements.txt .
RUN pip install --disable-pip-version-check -r requirements.txt

COPY app ./app

ENTRYPOINT ["python","-m","app.main"]
