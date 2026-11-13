FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PRESENCE_DATA_DIR=/tmp/presence \
    PRESENCE_EXPORT_MODE=download \
    PRESENCE_CV_THREADS=1 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1

WORKDIR /app
COPY requirements-cloud.lock.txt ./
RUN pip install --no-cache-dir -r requirements-cloud.lock.txt
COPY pyproject.toml main.py ./
COPY presence_cv ./presence_cv
COPY config ./config
COPY models ./models
RUN pip install --no-cache-dir --no-deps ".[cloud]" \
    && python main.py setup-models \
    && useradd --create-home presence

USER presence
EXPOSE 10000
CMD ["sh", "-c", "exec python -m uvicorn presence_cv.api:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
