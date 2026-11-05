# syntax=docker/dockerfile:1
#
# Local development image for the API. The UI is served by Vite in its own
# container (see docker-compose.yml), so there is no build step for the frontend
# here and no static hosting in FastAPI.
#
# The process runs as uid 10001: nothing in this image needs root.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.7.12 /uv /uvx /usr/local/bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    MIGRATIONS_DIR=/app/migrations

RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /app --shell /usr/sbin/nologin app

WORKDIR /app
COPY --chown=app:app backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-install-project && chown -R app:app /app/.venv
COPY --chown=app:app backend/src ./src
COPY --chown=app:app backend/tests ./tests
COPY --chown=app:app backend/migrations ./migrations
COPY --chown=app:app backend/entrypoint.sh /entrypoint.sh
RUN uv sync --frozen && chmod +x /entrypoint.sh && chown -R app:app /app

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"]

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "relay.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
