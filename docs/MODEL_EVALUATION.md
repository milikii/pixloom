# Pixloom Model Evaluation

Last updated: 2026-05-06

Hardware target: Intel Core i7-8700, 6 cores / 12 threads, 32 GB RAM, 1 TB SSD,
CPU-only Docker runtime.

This document separates model reputation from local acceptance. A model is not
operator-ready until its source, license, file format, backend compatibility, CPU
runtime, memory behavior, and output quality are recorded here.

Runtime rule:

- `installed` or `downloaded` does not automatically mean UI-visible.
- Only models explicitly accepted for daily operator use should appear in the
  primary WebUI dropdown.
- Other local model files belong to the evaluation pool until their acceptance state
  is promoted.

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
6. slow quality-ceiling option
7. anime denoise specialist

Each UI entry must expose style, speed class, local acceptance status, and one
operator warning before submission.

## Current Local Inventory Snapshot

As of 2026-05-01, the local `models/` directory currently contains:

| File | Size | SHA256 | Current exposure |
|---|---:|---|---|
| `4x-UltraSharp.pth` | `66961958` bytes | `a5812231fc936b42af08a5edba784195495d303d5b3248c24489ef0c4021fe01` | operator-visible |
| `4x_NMKD-Siax_200k.pth` | `66957746` bytes | `560424d9f68625713fc47e9e7289a98aabe1d744e1cd6a9ae5a35e9957fd127e` | operator-visible |
| `4x_foolhardy_Remacri.pth` | `67025055` bytes | `e1a73bd89c2da1ae494774746398689048b5a892bd9653e146713f9df8bca86a` | operator-visible |
| `APISR_4x_int8.onnx` | `4717802` bytes | `fda363437f2391042c108a5342c01749c1e61287215c2529d67c1af8ea1f2e77` | operator-visible |
| `GFPGANv1.4.pth` | `348632874` bytes | `e2cd4703ab14f4d01fd1383a8a8b266f9a5833dacee8e6a79d3bf21a1b6be5ad` | operator-visible |
| `DAT2_4x_pretrain.pth` | `140333139` bytes | `05b5c17bb5d1939ec0ec6b9368368d82d8c45b80c134e370f798efec0aeec395` | evaluation-only |
| `DRCT_X4.pth` | `245582817` bytes | `fe104903aa8fe897b85605a733c8c7907e40c02f066e53c6cbac2f3f0c838dd9` | operator-visible |
| `DRCT-L_X4.pth` | `485570697` bytes | `a99044c0275699d1a296ae21b8f322fa8c65d7b9be2213ee2a3dcc280ab8d64b` | operator-visible |
| `HAT-L-4x.pth` | `165774123` bytes | `5992bd38522f2b8faf11ea4bd8ee08de92465bb66892166576999afc36d60043` | operator-visible |
| `RealESRGAN_x4plus.pth` | `67040989` bytes | `4fa0d38905f75ac06eb49a7951b426670021be3018265fd191d2125df9d682f1` | operator-visible |
| `RealESRGAN_x4plus_anime_6B.pth` | `17938799` bytes | `f872d837d3c90ed2e05227bed711af5671a6fd1c9f7d7e91c911a61f155e99da` | operator-visible |
| `RealPLKSR_4x.pth` | `29678402` bytes | `7d67b22f0c5b60f4167d94e89b7b56f74bdf994bb8fb199769b9d945c681a1ae` | operator-visible |
| `SPAN_pretrain.pth` | `9016540` bytes | `234ac9facfdce987dab59ef6cd8129dd88903a16b6d34eeddd639b81f6695b18` | operator-visible |
| `codeformer.pth` | `376637898` bytes | `1009e537e0c2a07d4cabce6355f53cb66767cd4b4297ec7a4a64ca4b8a5684b7` | operator-visible |
| `realesr-general-x4v3.pth` | `4885111` bytes | `8dc7edb9ac80ccdc30c3a5dca6616509367f05fbc184ad95b731f05bece96292` | operator-visible |
| `up2x-latest-denoise3x.pth` | `5147249` bytes | `0a14739f3f5fcbd74ec3ce2806d13a47916c916b20afe4a39d95f6df4ca6abd8` | operator-visible |
| `up3x-latest-denoise3x.pth` | `5154161` bytes | `39f1e6e90d50e5528a63f4ba1866bad23365a737cbea22a80769b2ec4c1c3285` | operator-visible |

If the accepted set is smaller than the ideal five-slot ordering, the primary
dropdown should shrink to the trusted subset rather than show unaccepted placeholders.

The remaining non-operator files above are tracked as evaluation-only local assets.
They are present on disk and represented in code/docs, but they remain outside the
main submission flow until explicitly accepted.

## Local Runtime Smoke Results (2026-05-01)

The following smoke run used the current Python runtime on a generated `8x6` sample
image. This is **not** the final quality acceptance pass. It only answers:

- can the current runtime load the weight?
- can it complete one tiny upscale call?
- does it immediately fail due to backend/runtime mismatch?

| Model id | Backend | Result | Elapsed | Next step |
|---|---|---|---:|---|
| `4x-remacri` | `spandrel` | `ok` | `3.104s` | quality acceptance on real photos |
| `realesrgan-x4plus` | `spandrel` | `ok` | `0.247s` | quality acceptance on real photos |
| `4x-ultrasharp` | `spandrel` | `ok` | `0.204s` | quality acceptance on web/AI/illustration inputs |
| `4x-nmkd-siax-200k` | `spandrel` | `ok` | `0.530s` | decide whether to keep as registry-tracked evaluation model |
| `realesrgan-x4plus-anime` | `spandrel` | `ok` | `0.175s` | already operator-visible; keep real acceptance notes current |
| `realesr-general-x4v3` | `spandrel` | `ok` | `0.051s` | already operator-visible; keep smoke-test role |
| `span-4x` | `spandrel` | `ok` | `0.115s` | evaluate on real images before enabling |
| `realplksr-4x` | `spandrel` | `ok` | `0.290s` | evaluate on real images before enabling |
| `dat2-4x-pretrain` | `spandrel` | `ok` | `0.819s` | keep disabled; research/quality-ceiling testing only |
| `drct-4x` | `spandrel` | `ok` | `2.661s` | add to slow quality-ceiling operator set beside HAT-L |
| `drct-l-4x` | `spandrel` | `ok` | `1.013s` | keep visible with very-slow warning; use for upper-bound comparisons only |
| `hat-l-4x` | `spandrel` | `ok` | `2.984s` | operator-visible opt-in; keep CPU-slow warning explicit |
| `apisr-4x-int8` | `onnxruntime` | `backend-not-implemented` | n/a | add ONNX path before evaluation |
| `real-cugan-up2x-denoise3x` | `spandrel` | `ok` | `0.045s` | expose as the 2x anime precision option |
| `real-cugan-up3x-denoise3x` | `spandrel` | `ok` | `0.061s` | operator-visible anime denoise specialist; remind users it is 3x, not 4x |
| `codeformer` | `custom` | `backend-not-implemented` | n/a | add face-restoration path before evaluation |
| `gfpgan-v14` | `custom` | `backend-not-implemented` | n/a | add face-restoration path before evaluation |

### 1. Natural Photo Default

**4x Remacri**
Status: `accepted`, first-wave operator set
Current file: `models/4x_foolhardy_Remacri.pth`
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

Local runtime note (2026-05-01):
- current Pixloom runtime successfully produced `output/20260501-122545-811888_1777260396442_4x-remacri_4x.png`
- this confirms file/load/runtime compatibility on a real local image, but not yet the
  final subjective quality decision

### 2. Stable Photo Baseline

**Real-ESRGAN 4x Photo**
Status: `accepted`, first-wave operator set
Current file: `models/RealESRGAN_x4plus.pth`
Backend target: Spandrel / Real-ESRGAN
UI label: `照片通用 - Real-ESRGAN 4x`
Speed class: `普通`
Style: `通用照片`
Stability: `待本机验收`

Use this as the official general-photo baseline. It is the safe reference point when
comparing community ESRGAN models.

Tradeoff: may still sharpen edges more than desired on portraits or already-clean
phone photos.

Local runtime note (2026-05-01):
- current Pixloom runtime successfully produced `output/20260501-122936-050407_1777260396442_realesrgan-x4plus_4x.png`
- this confirms file/load/runtime compatibility on a real local image, but not yet the
  final subjective quality decision

### 3. Sharp Style / AI Art

**4x UltraSharp**
Status: `accepted`, first-wave operator set
Current file: `models/4x-UltraSharp.pth`
Backend target: Spandrel / ESRGAN
UI label: `锐化插画 - 4x UltraSharp`
Speed class: `普通偏慢`
Style: `锐利`
Stability: `待本机验收`

Use this for AI images, compressed web images, crisp illustrations, and pictures where
you intentionally want stronger edge contrast.

Tradeoff: not recommended as the default photo model. It can make skin, hair edges,
and small textures look over-processed.

Local runtime note (2026-05-01):
- current Pixloom runtime successfully produced `output/20260501-123334-120636_1777260396442_4x-ultrasharp_4x.png`
- this confirms file/load/runtime compatibility on a real local image, but not yet the
  final subjective quality decision

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

### Additional Downloaded Files Pending Integration

**4x_NMKD-Siax_200k**
Status: `installed`, pending registry/integration decision
Current file: `models/4x_NMKD-Siax_200k.pth`
Purpose: stronger handling of compressed or noisy real-world images

Local runtime note (2026-05-01):
- current Pixloom runtime successfully produced `output/20260501-123726-964290_1777260396442_4x-nmkd-siax-200k_4x.png`
- this confirms file/load/runtime compatibility on a real local image, but not yet the
  final subjective quality decision

**SPAN 4x pretrain**
Status: `installed`, pending registry/integration decision
Current file: `models/SPAN_pretrain.pth`
Purpose: representative lightweight SPAN-family evaluation weight

Local runtime note (2026-05-01):
- current Pixloom runtime successfully produced `output/20260501-124201-153803_1777260396442_span-4x_4x.png`
- this confirms file/load/runtime compatibility on a real local image, but not yet the
  final subjective quality decision

**RealPLKSR 4x**
Status: `installed`, pending local acceptance
Current file: `models/RealPLKSR_4x.pth`
Purpose: lightweight photo/general upscaling candidate already represented by the
disabled `realplksr-4x` registry entry

Local runtime note (2026-05-01):
- current Pixloom runtime successfully produced `output/20260501-124224-385938_1777260396442_realplksr-4x_4x.png`
- this confirms file/load/runtime compatibility on a real local image, but not yet the
  final subjective quality decision

**DAT2 4x pretrain**
Status: `installed`, pending registry/integration decision
Current file: `models/DAT2_4x_pretrain.pth`
Purpose: representative DAT-family quality-ceiling evaluation weight

Local runtime note (2026-05-01):
- current Pixloom runtime successfully produced real-image outputs such as
  `output/20260501-124539-441454_1777260396442_dat2-4x-pretrain_4x.png`
- this confirms the weight does run on the current CPU path, but it remains a
  long-run candidate rather than a fast interactive acceptance step

**CodeFormer**
Status: `installed`, `needs-backend`
Current file: `models/codeformer.pth`
Purpose: face restoration with adjustable fidelity

**GFPGAN v1.4**
Status: `installed`, `needs-backend`
Current file: `models/GFPGANv1.4.pth`
Purpose: faster face restoration baseline

**Real-CUGAN up3x latest denoise3x**
Status: `installed`, `tested`, `accepted`
Current file: `models/up3x-latest-denoise3x.pth`
Purpose: anime line preservation and denoise-focused 3x operator track

Current note:
- current runtime now loads this weight through the Spandrel path
- a tiny runtime check completed successfully at `24x18` output in `0.061s`
- UI label is `动漫修复 - Real-CUGAN 3x 去噪`
- keep the 3x scale warning visible so operators do not confuse it with the 4x set

**APISR 4x int8 ONNX**
Status: `installed`, `needs-backend`
Current file: `models/APISR_4x_int8.onnx`
Purpose: APISR-family anime restoration evaluation weight in ONNX form

**OmniSR 4x DF2K**
Status: `installed`, pending registry/integration decision
Current file: `models/OmniSR_4x_DF2K.pth`
Purpose: lightweight Omni-SR evaluation weight sourced from the DF2K release

Current note:
- tiny smoke run on the current runtime errored; do not prioritize this weight for
  near-term promotion

**OmniSR X4 DIV2K safetensors**
Status: `installed`, pending registry/integration decision
Current file: `models/OmniSR_X4_DIV2K.safetensors`
Purpose: alternate Omni-SR weight in safetensors format for local inspection

**HAT-L 4x**
Status: `installed`, `tested`, `accepted`
Current file: `models/HAT-L-4x.pth`
Purpose: heavyweight HAT-family quality-ceiling operator option

Current note:
- current runtime loads and upscales successfully on tiny local samples
- UI label is `质量上限 - HAT-L 4x`
- keep this in the operator set only as an explicit slow option; do not market it as
  a default or phone-friendly choice

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
Status: `manual-source`, `tested`, `accepted`
Purpose: anime, manga, compressed animation frames, line cleanup

Why test it: strong reputation for anime line preservation and denoise variants.

Current decision: the locally stored `up3x-latest-denoise3x.pth` weight does load
through the current Spandrel path, so it is now promoted into the operator-visible
set. Keep reminding users that this entry is a 3x specialist, not a 4x general model.

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

Risk: pure CPU processing may be too slow for NAS operator use. HAT is now exposed as
an explicit slow option because the user asked for it, but it still should not become
the default without stronger real-image timing evidence. DAT and Omni-SR remain in the
evaluation bucket.

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
