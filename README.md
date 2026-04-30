# Pixloom

Pixloom is a self-hosted NAS image upscaling WebUI. It runs as a small Docker Compose service with a Gradio interface and CPU-only inference.

The first release is intentionally narrow:

- upload one image
- choose an installed model
- run CPU upscaling
- preview the output
- download the result

Pixloom is not a ComfyUI replacement and does not expose a workflow graph.

## Directory Layout

```text
.
├── compose.yml
├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py
│   ├── config.py
│   ├── inference.py
│   ├── model_registry.py
│   └── spandrel_backend.py
├── models/
├── input/
├── output/
└── logs/
```

Runtime data is persisted in:

- `models/`: model files placed manually
- `input/`: uploaded source images
- `output/`: generated upscaled images
- `logs/`: reserved for runtime logs

## Model Files

Pixloom v1 does not download models automatically. Place model files in `models/` with these names:

```text
models/RealESRGAN_x4plus.pth
models/RealESRGAN_x4plus_anime_6B.pth
models/realesr-general-x4v3.pth
models/4x-UltraSharp.pth
models/4x_foolhardy_Remacri.pth
```

Only enabled models with existing files appear in the WebUI.

## Start

```bash
docker compose up -d --build
```

Open the app through the host reverse proxy, or locally on the NAS:

```text
http://127.0.0.1:7860
```

The default Compose file binds the port to loopback only:

```yaml
ports:
  - "127.0.0.1:7860:7860"
```

Do not expose this port directly to the public internet.

## Stop

```bash
docker compose down
```

## Rebuild After Code Changes

```bash
docker compose build
docker compose up -d
```

## View Logs

```bash
docker compose logs -f --tail=120 upscale-webui
```

## Runtime Limits

The service defaults to:

- max input side: `2048px`
- max output side: `8192px`
- tile size: `256`
- tile overlap: `16`

Override these with environment variables in `compose.yml`:

```yaml
environment:
  PIXLOOM_MAX_INPUT_SIDE: "2048"
  PIXLOOM_MAX_OUTPUT_SIDE: "8192"
  PIXLOOM_TILE_SIZE: "256"
  PIXLOOM_TILE_OVERLAP: "16"
```

## Optional Gradio Auth

Pixloom can enable Gradio's built-in basic auth:

```yaml
environment:
  GRADIO_AUTH_USER: "your-user"
  GRADIO_AUTH_PASS: "your-password"
```

This is only a fallback for local or LAN-only use. Public access should be protected at nginx or a unified authentication layer.

## nginx Reverse Proxy Example

Host nginx should own HTTPS, public hostname, upload size limits, proxy timeout, and login.

```nginx
server {
    listen 443 ssl http2;
    server_name upscale.example.com;

    client_max_body_size 50m;

    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 1800s;
        proxy_send_timeout 1800s;
    }
}
```

Add Basic Auth, Authelia, OAuth2 Proxy, or the existing NAS login layer in nginx.

## Tests

```bash
pytest -v
```

The test suite uses fake models and generated tiny images. It does not require real model downloads.

## Manual Acceptance Test

Record one real NAS test after placing at least one model in `models/`:

```text
Date: 2026-04-30
Device: Debian 13 x86_64, Docker CPU-only
Input file: input/image-dabc1f26-17ef-4e44-91e9-2b55b44c6da0-0.png
Input size: 1402x1122
Model: Real-ESRGAN 4x Anime
Output format: PNG
Elapsed time: 92.11s
Output size: 5608x4488
Output path: output/20260430-031033-809102_image-dabc1f26-17ef-4e44-91e9-2b55b44c6da0-0_realesrgan-x4plus-anime_4x.png
Result notes: CPU-only upscale completed successfully and the output file was written under output/
```

Acceptance criteria:

- phone browser opens the WebUI
- one image uploads successfully
- at least one installed model appears
- CPU upscaling completes
- preview renders
- download file is available
- output file exists under `output/`
- container restart does not remove model or output files
