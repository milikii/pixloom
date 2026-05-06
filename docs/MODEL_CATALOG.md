# Pixloom Model Catalog

Last updated: 2026-05-06

This file lists every model currently tracked by Pixloom.

Star meaning:

- `★★★★★` first pick in its group
- `★★★★☆` strong fallback
- `★★★☆☆` utility / baseline / smoke test
- `★★☆☆☆` slow specialist
- `★☆☆☆☆` experiment only

## Overview

| ID | Visible | Group | Stars | Backend | Scale | Chinese Name |
|---|---|---|---|---|---:|---|
| `span-4x` | yes | 照片主力 | `★★★★★` | `spandrel` | 4 | `SPAN 4x` |
| `realplksr-4x` | yes | 照片主力 | `★★★★★` | `spandrel` | 4 | `RealPLKSR 4x` |
| `4x-nmkd-siax-200k` | yes | 照片主力 | `★★★★☆` | `spandrel` | 4 | `照片修复 - 4x NMKD-Siax` |
| `4x-ultrasharp` | yes | 照片主力 | `★★★★☆` | `spandrel` | 4 | `锐化插画 - 4x UltraSharp` |
| `hat-l-4x` | yes | 照片高质量慢跑 | `★★☆☆☆` | `spandrel` | 4 | `质量上限 - HAT-L 4x` |
| `apisr-4x-int8` | yes | 动漫/线稿 | `★★★★★` | `onnxruntime` | 4 | `APISR 4x` |
| `real-cugan-up3x-denoise3x` | yes | 动漫/线稿 | `★★★★★` | `spandrel` | 3 | `动漫修复 - Real-CUGAN 3x 去噪` |
| `realesrgan-x4plus-anime` | yes | 动漫/线稿 | `★★★★☆` | `spandrel` | 4 | `动漫插画 - Real-ESRGAN Anime 6B` |
| `codeformer` | yes | 人脸修复 | `★★★★★` | `custom` | 1 | `CodeFormer` |
| `gfpgan-v14` | yes | 人脸修复 | `★★★★☆` | `custom` | 1 | `GFPGAN v1.4` |
| `realesr-general-x4v3` | yes | 快速试跑 | `★★★☆☆` | `spandrel` | 4 | `快速试跑 - Real-ESRGAN General v3` |
| `4x-remacri` | yes | 经典旧将 | `★★★★☆` | `spandrel` | 4 | `照片自然 - 4x Remacri` |
| `realesrgan-x4plus` | yes | 经典旧将 | `★★★☆☆` | `spandrel` | 4 | `照片通用 - Real-ESRGAN 4x` |
| `dat2-4x-pretrain` | no | 照片高质量慢跑 | `★☆☆☆☆` | `spandrel` | 4 | `DAT2 4x 预训练版` |
| `omnisr-4x-df2k` | no | 照片高质量慢跑 | `★☆☆☆☆` | `spandrel` | 4 | `OmniSR 4x DF2K` |
| `omnisr-x4-div2k` | no | 照片高质量慢跑 | `★☆☆☆☆` | `spandrel` | 4 | `OmniSR X4 DIV2K` |

## Detailed Notes

### `SPAN 4x`

- Visible: yes
- Group: `照片主力`
- Stars: `★★★★★`
- Backend: `spandrel`
- Scale: `4`
- Best fit: 适合日常照片、通用图和想替换老 ESRGAN 的主力任务。
- Warning: 属于新一代轻量主力，但比快速试跑模型更慢；不适合做人脸专项修复。
- Sharp review: 🌟 轻量化新架构的黑马。速度显著优于传统 ESRGAN，画质持平甚至超越。在 i7-8700 纯 CPU 环境下，它是速度与质量的甜蜜点。

### `RealPLKSR 4x`

- Visible: yes
- Group: `照片主力`
- Stars: `★★★★★`
- Backend: `spandrel`
- Scale: `4`
- Best fit: 适合真实照片、风景、建筑和想用 2024 新架构替代老模型的主力任务。
- Warning: 更偏真实照片纹理重建，不是动漫专用；比快速试跑更慢，但应当优先于老 ESRGAN 尝试。
- Sharp review: 照片纹理重建的专家。对真实照片的细节还原能力强，但 CPU 推理速度中等偏慢。建议留给少量精品图慢慢跑。

### `照片修复 - 4x NMKD-Siax`

- Visible: yes
- Group: `照片主力`
- Stars: `★★★★☆`
- Backend: `spandrel`
- Scale: `4`
- Best fit: 适合压缩较重、带噪点或质量偏差的日常图片。
- Warning: CPU 推理偏慢，但在 NAS 环境下可用。处理压缩图时去噪能力强于 UltraSharp。
- Sharp review: 🥈 去噪领域的隐藏BOSS。应对劣质源（过度压缩、带噪点的1080p图像）比 UltraSharp 更稳。纹理密集型写实图片的可靠选择。

### `质量上限 - HAT-L 4x`

- Visible: yes
- Group: `照片高质量慢跑`
- Stars: `★★☆☆☆`
- Backend: `spandrel`
- Scale: `4`
- Best fit: 适合追求细节上限的照片和通用图片，但更适合少量慢跑任务。
- Warning: CPU 推理明显更慢，不适合大批量或手机上频繁试错。
- Sharp review: 🏆 多项超分基准测试霸榜的 Transformer 模型。能「理解」图像全局结构，修复极其模糊的边缘。代价：纯 CPU 慢到令人发指，只适合真爱。

### `锐化插画 - 4x UltraSharp`

- Visible: yes
- Group: `照片主力`
- Stars: `★★★★☆`
- Backend: `spandrel`
- Scale: `4`
- Best fit: 适合 AI 图、插画、压缩网图，也适合想要更强锐度的风景和建筑照片。
- Warning: 锐化更强，人物皮肤和近景小纹理可能偏硬；不适合想保留柔和自然感的照片。
- Sharp review: 🏆 老牌强将，但不是退休干部。AI 插画、CG 和高反差风景放大依然很能打，日常使用频率完全配得上主力席位。

### `APISR 4x`

- Visible: yes
- Group: `动漫/线稿`
- Stars: `★★★★★`
- Backend: `onnxruntime`
- Scale: `4`
- Best fit: 适合压缩较重的动漫、二次元图和希望保住线条结构的主力任务。
- Warning: ONNX 动漫修复模型，适合压缩较重的二次元图片；不适合真实照片。
- Sharp review: 🌟 二次元视频/图像超分的新晋神级模型。专门针对被过度压缩的动漫图像训练，识别和修复失真线条的能力极强。

### `动漫修复 - Real-CUGAN 3x 去噪`

- Visible: yes
- Group: `动漫/线稿`
- Stars: `★★★★★`
- Backend: `spandrel`
- Scale: `3`
- Best fit: 适合动漫、漫画、压缩动画帧和希望顺手做去噪的二次元图片。
- Warning: 这是 3x 模型，不是 4x；真实照片通常不如照片模型自然。
- Sharp review: 🏆 B站开源镇馆之宝。对线条保护和色块平滑的处理至今难逢敌手，甚至能修复画师原画的作画瑕疵。二次元/线稿类图像的终极选择。

### `动漫插画 - Real-ESRGAN Anime 6B`

- Visible: yes
- Group: `动漫/线稿`
- Stars: `★★★★☆`
- Backend: `spandrel`
- Scale: `4`
- Best fit: 适合动漫、插画、线稿和二次元风格图片。
- Warning: 处理真实照片时可能边缘偏硬，不一定最自然。
- Sharp review: 二次元专用，体积小跑得快。线条保护不错但别拿去跑真实照片。适合作为动漫批量处理的兜底选项。

### `CodeFormer`

- Visible: yes
- Group: `人脸修复`
- Stars: `★★★★★`
- Backend: `custom`
- Scale: `1`
- Best fit: 适合老照片、小脸、压缩严重的人像修复，偏保真路线。
- Warning: 这是人脸修复，不是通用超分；没有明显人脸时请不要选它。
- Sharp review: 🌟 人脸保真度很强。可在“更像原图”和“更清晰”之间折中，AI 假面感低于老一代模型。

### `GFPGAN v1.4`

- Visible: yes
- Group: `人脸修复`
- Stars: `★★★★☆`
- Backend: `custom`
- Scale: `1`
- Best fit: 适合普通人像和低质量脸部修复，偏速度路线。
- Warning: 这是人脸修复，不是通用超分；没有明显人脸时请不要选它。
- Sharp review: 🛡️ 老牌人脸修复，速度比 CodeFormer 更友好，适合作为轻量兜底选项。

### `快速试跑 - Real-ESRGAN General v3`

- Visible: yes
- Group: `快速试跑`
- Stars: `★★★☆☆`
- Backend: `spandrel`
- Scale: `4`
- Best fit: 适合先快速试跑，确认上传、队列和输出路径是否正常。
- Warning: 速度更友好，但细节上限通常低于更重的模型。
- Sharp review: 轻量级试跑选手。画质不顶尖但胜在快，CPU 上也能跑得动。适合先验证整条链路是否正常。

### `照片自然 - 4x Remacri`

- Visible: yes
- Group: `经典旧将`
- Stars: `★★★★☆`
- Backend: `spandrel`
- Scale: `4`
- Best fit: 适合真实照片、人物、旅行照和想保留自然观感的混合图片。
- Warning: 通常更柔和，追求极致锐利或二次元线条时不如专用模型。
- Sharp review: 稳，但不惊艳。照片修复的老黄牛，不会翻车但也不会给你惊喜。适合批量跑图，不求极致，只求不翻。

### `照片通用 - Real-ESRGAN 4x`

- Visible: yes
- Group: `经典旧将`
- Stars: `★★★☆☆`
- Backend: `spandrel`
- Scale: `4`
- Best fit: 适合照片、压缩过的日常图片和多数通用场景。
- Warning: 细节会更自然，但插画和线稿不一定最锐利。
- Sharp review: Real-ESRGAN 官方出品，通用性最强的照片模型。对压缩图片的修复稳定，但细节上限不如 UltraSharp。适合不知道选什么时无脑选。

### `DAT2 4x 预训练版`

- Visible: no
- Group: `照片高质量慢跑`
- Stars: `★☆☆☆☆`
- Backend: `spandrel`
- Scale: `4`
- Best fit: 实验模型，只适合做少量对比测试，不适合作为 DAT 系列的正式画质代表。
- Warning: 这是 pretrain 预训练权重，不是社区常用的 fine-tuned 成品版；画质判断容易失真，CPU 也非常慢。
- Sharp review: 别把它当 DAT 正式代表。这个 pretrain 版更像研究样本，能跑不等于该拿来做结论；想认真评 DAT，得换成 fine-tuned 社区版。

### `OmniSR 4x DF2K`

- Visible: no
- Group: `照片高质量慢跑`
- Stars: `★☆☆☆☆`
- Backend: `spandrel`
- Scale: `4`
- Best fit: 实验模型，适合极模糊原图的重建对比测试。
- Warning: 轻量化全向自注意力模型，纯 CPU 偏慢但画质天花板高。
- Sharp review: 全向自注意力路线。极模糊原图的重建很能打，但当前更适合做研究样本，不适合默认交给手机端操作。

### `OmniSR X4 DIV2K`

- Visible: no
- Group: `照片高质量慢跑`
- Stars: `★☆☆☆☆`
- Backend: `spandrel`
- Scale: `4`
- Best fit: 实验模型，适合极模糊原图的重建对比测试。
- Warning: safetensors 版，CPU 需耐心。
- Sharp review: 和 DF2K 版定位类似。可以留在本地评估池，但没必要放进默认主流程。
