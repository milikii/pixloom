ARG NODE_IMAGE=swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/node:22-bookworm-slim
ARG PYTHON_IMAGE=python:3.11-slim

FROM ${NODE_IMAGE} AS frontend-builder

WORKDIR /build/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIXLOOM_FRONTEND_DIST=/app/frontend-out
ENV PIXLOOM_BUNDLED_MODELS_DIR=/app/bundled-models

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install --index-url https://download.pytorch.org/whl/cpu torch==2.11.0 torchvision==0.26.0 \
    && pip install -r /tmp/requirements.txt

COPY app /app/app
COPY backend /app/backend
COPY models /app/bundled-models
COPY --from=frontend-builder /build/frontend/out /app/frontend-out

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "backend.pixloom_api.main:app", "--host", "0.0.0.0", "--port", "7860"]
