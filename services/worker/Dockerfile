FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /usr/local/bin/

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1

WORKDIR /repo
COPY libs/shared libs/shared
COPY services/worker services/worker

WORKDIR /repo/services/worker
RUN uv sync --no-dev

CMD ["uv", "run", "python", "-m", "app.worker"]
