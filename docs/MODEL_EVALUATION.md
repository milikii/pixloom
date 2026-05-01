# Pixloom Model Evaluation

Last updated: 2026-05-01

Hardware target: Intel Core i7-8700, 6 cores / 12 threads, 32 GB RAM, 1 TB SSD,
CPU-only Docker runtime.

This document separates model reputation from local acceptance. A model is not
operator-ready until its source, license, file format, backend compatibility, CPU
runtime, memory behavior, and output quality are recorded here.

## Status Legend

- `installed`: model file is present under `models/`
- `downloadable`: source appears stable enough to download automatically
- `manual-source`: source requires manual download or license confirmation
- `needs-backend`: model needs a backend or pipeline Pixloom does not yet implement
- `tested`: completed local CPU smoke test
- `accepted`: suitable to expose to normal operators

## Recommended Operator Set

UI ordering should stay conservative for CPU-only NAS usage:

1. natural photo default
2. stable photo baseline
3. sharp illustration / AI-art style
4. anime / line-art baseline
5. fast smoke test

Each UI entry must expose style, speed class, local acceptance status, and one
operator warning before submission.

### 1. Natural Photo Default

**4x Remacri**
Status: `manual-source`, planned P0 evaluation
Expected file: `models/4x_foolhardy_Remacri.pth`
Backend target: Spandrel / ESRGAN
UI label: `照片自然 - 4x Remacri`
Speed class: `普通偏慢`
Style: `自然`
Stability: `待本机验收`

Use this when the source is a real photo and the current output feels too sharp. It
should be the first candidate for portraits, family photos, travel photos, and mixed
phone images where natural texture matters more than crisp edges.

Tradeoff: usually softer than UltraSharp. If the source is a compressed web image with
hard edges, it may look less punchy.

### 2. Stable Photo Baseline

**Real-ESRGAN 4x Photo**
Status: `downloadable`, planned P0 evaluation
Expected file: `models/RealESRGAN_x4plus.pth`
Backend target: Spandrel / Real-ESRGAN
UI label: `照片通用 - Real-ESRGAN 4x`
Speed class: `普通`
Style: `通用照片`
Stability: `待本机验收`

Use this as the official general-photo baseline. It is the safe reference point when
comparing community ESRGAN models.

Tradeoff: may still sharpen edges more than desired on portraits or already-clean
phone photos.

### 3. Sharp Style / AI Art

**4x UltraSharp**
Status: `manual-source`, planned P0 evaluation
Expected file: `models/4x-UltraSharp.pth`
Backend target: Spandrel / ESRGAN
UI label: `锐化插画 - 4x UltraSharp`
Speed class: `普通偏慢`
Style: `锐利`
Stability: `待本机验收`

Use this for AI images, compressed web images, crisp illustrations, and pictures where
you intentionally want stronger edge contrast.

Tradeoff: not recommended as the default photo model. It can make skin, hair edges,
and small textures look over-processed.

### 4. Anime / Illustration Baseline

**Real-ESRGAN 4x Anime 6B**
Status: `installed`, previously smoke-tested
Current file: `models/RealESRGAN_x4plus_anime_6B.pth`
Backend target: Spandrel / Real-ESRGAN
UI label: `动漫插画 - Real-ESRGAN Anime 6B`
Speed class: `较快`
Style: `动漫/线稿`
Stability: `已实机跑通`

Use this for anime, illustration, line art, and flat-color images. It is small and
practical on CPU.

Tradeoff: real photos can look too hard or artificial.

### 5. Fast Smoke Test

**Real-ESRGAN General 4x v3**
Status: `installed`, previously smoke-tested
Current file: `models/realesr-general-x4v3.pth`
Backend target: Spandrel / Real-ESRGAN
UI label: `快速试跑 - Real-ESRGAN General v3`
Speed class: `较快`
Style: `快速通用`
Stability: `已实机跑通`

Use this to confirm the app, queue, and output path are working before running heavier
models. It is useful for debugging and quick checks.

Tradeoff: lower quality ceiling than heavier models.

## Expanded Evaluation Track

### Anime And Line Preservation

**APISR**
Status: `manual-source`, `needs-backend`
Purpose: anime production-style image/video restoration

Why test it: APISR is specifically designed around anime production artifacts, including
distorted hand-drawn lines and color artifacts. It is a strong candidate for old anime
stills, compressed anime screenshots, and line-sensitive material.

Risk: APISR is not a drop-in Spandrel model entry. It ships its own inference code and
model zoo, so it should be evaluated as a separate anime restoration backend.

**Real-CUGAN**
Status: `manual-source`, `needs-backend` until file format and Spandrel support are verified
Purpose: anime, manga, compressed animation frames, line cleanup

Why test it: strong reputation for anime line preservation and denoise variants.

Risk: many Real-CUGAN distributions target separate command-line runtimes or NCNN builds.
Do not assume a downloaded model can load through current Spandrel code.

### Lightweight Newer Candidates

**SPAN**
Status: `manual-source`, planned compatibility test
Purpose: faster general/anime/AI-art super-resolution

Why test it: newer lightweight architecture that may fit CPU better than heavy
Transformer models.

Risk: the exact `.pth` file must match a Spandrel-supported architecture and scale.

**RealPLKSR**
Status: `manual-source`, planned compatibility test
Purpose: lightweight photo/general upscaling

Why test it: promising quality/speed tradeoff for CPU-class hardware.

Risk: source, filename, and Spandrel compatibility must be confirmed before exposing.

### Research-Quality Heavy Models

**HAT / DAT / Omni-SR**
Status: `manual-source`, high-risk CPU evaluation
Purpose: quality ceiling tests, difficult blur/detail reconstruction

Why test them: they represent stronger academic or Transformer-style reconstruction
families.

Risk: pure CPU processing may be too slow for NAS operator use. These should be tested
with a strict timing matrix and never become defaults without measured results.

### Face Restoration

**CodeFormer**
Status: `downloadable`, `needs-backend`
Purpose: face restoration with adjustable fidelity

Why test it: useful when a photo has small or degraded faces that normal upscalers distort.

Risk: this is face restoration, not normal super-resolution. It should be a separate
post-process mode, not another item in the core upscale dropdown.

**GFPGAN v1.4**
Status: `downloadable`, `needs-backend`
Purpose: faster face restoration baseline

Why test it: mature face restoration baseline with broad community usage.

Risk: same product-boundary issue as CodeFormer; it changes what the app promises.

## Timing Matrix Template

Record each local CPU run here before accepting a model:

| Model | Input | Input size | Output size | Tile | Elapsed | Peak memory | Result | Notes |
|---|---|---:|---:|---:|---:|---:|---|---|
| TBD | TBD | TBD | TBD | 256 | TBD | TBD | TBD | TBD |

## Operator Copy Template

Each model shown in the UI should provide:

- Best for: plain Chinese image categories
- Avoid when: one sentence on bad fits
- Speed: fast / normal / slow / very slow on i7-8700
- Style: natural / sharp / anime / face repair / experimental
- Risk: stable / experimental / needs manual confirmation
