# Quilt API on Railway (ADR-012). Build context is the repo root; see railway.json.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /bin/uv
WORKDIR /app
COPY api/pyproject.toml api/uv.lock api/
RUN cd api && uv sync --frozen --no-dev --no-install-project
COPY api api
ENV PATH=/app/api/.venv/bin:$PATH PYTHONUNBUFFERED=1
CMD ["sh", "-c", "uvicorn api.index:app --host 0.0.0.0 --port ${PORT:-8000}"]
