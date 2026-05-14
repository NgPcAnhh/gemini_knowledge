# syntax=docker/dockerfile:1.7

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_INPUT=1
ENV PIP_DEFAULT_TIMEOUT=1000
ENV PIP_RETRIES=20

WORKDIR /app

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install \
      --retries 20 \
      --timeout 1000 \
      --prefer-binary \
      --progress-bar off \
      -r requirements.txt

COPY . .

CMD ["python"]