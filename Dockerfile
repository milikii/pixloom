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
ENV PIXLOOM_MODELS_DIR=/data/models
ENV PIXLOOM_INPUT_DIR=/data/input
ENV PIXLOOM_OUTPUT_DIR=/data/output
ENV PIXLOOM_LOGS_DIR=/data/logs
ENV PIXLOOM_DB_PATH=/data/state/pixloom.sqlite3

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
RUN mkdir -p /app/bundled-models
COPY models/APISR_4x_int8.onnx models/realesr-general-x4v3.pth models/up2x-latest-denoise3x.pth models/up3x-latest-denoise3x.pth models/SPAN_pretrain.pth models/RealESRGAN_x4plus_anime_6B.pth models/RealPLKSR_4x.pth models/4x-UltraSharp.pth models/4x_NMKD-Siax_200k.pth models/4x_foolhardy_Remacri.pth models/RealESRGAN_x4plus.pth /app/bundled-models/
COPY models/DAT2_4x_pretrain.pth models/HAT-L-4x.pth /app/bundled-models/
COPY models/DRCT_X4.pth /app/bundled-models/
COPY models/DRCT-L_X4.pth /app/bundled-models/
COPY models/GFPGANv1.4.pth /app/bundled-models/
COPY models/codeformer.pth /app/bundled-models/
COPY models/facelib /app/bundled-models/facelib
COPY --from=frontend-builder /build/frontend/out /app/frontend-out
RUN mkdir -p /data

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "backend.pixloom_api.main:app", "--host", "0.0.0.0", "--port", "7860"]
