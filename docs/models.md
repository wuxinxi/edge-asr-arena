# 模型选型清单

[返回 README](../README.md) · [架构设计](architecture.md) · [评测总体](evaluation.md)

入选标准：**HuggingFace 趋势榜/高下载量 + 可在 PC 端侧（Apple Silicon M1/M2/M4）本地运行 + 开源权重**。按 2026 年 10 月调研结果筛选，最终接入前需逐模型验证。

## 入选模型总览

| 模型 key | 模型名 | 参数量 | 下载大小 | 许可证 | 语言 | 流式 | Mac 适配 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `whisper-turbo` | OpenAI Whisper large-v3-turbo | 809M | ~1.6GB | MIT | 99 语言 | 离线 | whisper.cpp / mlx-whisper / faster-whisper |
| `whisper-large-v3` | OpenAI Whisper large-v3 | 1.55B | ~3.1GB | MIT | 99 语言 | 离线 | 同上，生态基线 |
| `qwen3-asr-0.6b` | Qwen3-ASR-0.6B-hf | 0.6B | ~1.56GB | Apache 2.0 | 52 语言+22 中文方言 | **统一流式/离线** | transformers v5.13+, mlx-audio |
| `qwen3-asr-1.7b` | Qwen3-ASR-1.7B-hf | 1.7B | ~4.08GB | Apache 2.0 | 52 语言+22 中文方言 | **统一流式/离线** | 同上 |
| `sensevoice-small` | FunAudioLLM/SenseVoiceSmall | 234M | ~460MB | 开源(Apache-like) | 中/英/日/韩/粤 | 离线(可流式) | FunASR, CPU 实时 |
| `paraformer-large` | paraformer-zh-large | 220M | ~840MB | 开源 | 中文为主 | 离线 | FunASR, CPU 最快 |
| `paraformer-streaming` | paraformer-zh-streaming | 220M | ~840MB | 开源 | 中文为主 | **流式** | FunASR, 低延迟 |
| `fun-asr-nano` | Fun-ASR-Nano | 800M | ~3.2GB | 开源 | 中文/英/日+7方言 | 离线 | FunASR, LLM 解码 |
| `fun-asr-mlt-nano` | Fun-ASR-MLT-Nano | 800M | ~3.2GB | 开源 | 31 语言多语言版 | 离线/流式 | FunASR, 多语言 |
| `whisper-base` | OpenAI Whisper base | 74M | ~145MB | MIT | 99 语言 | 离线 | faster-whisper, 极轻量对照 |

## 选型理由

### Whisper 系列（生态基线）

- **large-v3-turbo**：月下载 872 万次，是当前端侧 ASR 事实标准。解码器从 32 层剪到 4 层，速度约 large-v3 的 8 倍，精度损失很小。Mac 上有 whisper.cpp（CoreML）、mlx-whisper、faster-whisper 三套成熟运行时。
- **large-v3**：月下载 550 万次，作为精度上限基线对照。
- 注：Whisper small/medium 中文 CER 约 15-20%，中文弱项，且尺寸梯度已由 FunASR 的 220M/234M 覆盖，故不纳入。

### Qwen3-ASR（中文+方言趋势新星）

- 2026 年 1 月发布，Apache 2.0，月下载已达 429 万且快速攀升。
- **52 语言含 22 种中文方言**，这是 Whisper 系列的弱项，也是本评测"方言"维度的核心模型。
- **统一流式/离线推理路径**，一个模型两种模式，满足用户"流式+离线都要"的需求。
- 0.6B 仅 1.56GB，1.7B 4.08GB，均可在笔记本运行。

### FunASR 系（中文 CPU 极速 + 流式）

- **SenseVoiceSmall**：234M，中文 CER 7.81%，CPU 上约 20× 实时，额外输出语言识别、情感标签（开心/悲伤/愤怒/中性）和音频事件（笑声/掌声/咳嗽）。直接命中"情感与特殊发音"维度。
- **Paraformer-large**：220M，CPU 约 22× 实时，支持字级时间戳和热词定制。命中"数字/编号/热词"维度。
- **Paraformer-streaming**：Paraformer 的流式版本，220M，低延迟中文流式。补流式维度——目前仅 Qwen3-ASR 支持流式，这个提供第二个流式参照。
- **Fun-ASR-Nano**：800M，LLM-ASR 架构，中文 CER 8.06%，支持 7 大方言和 26 种口音。与 SenseVoice/Paraformer 同属 FunASR 生态但路线不同（非自回归 vs LLM 自回归），测端侧 Mac 上 LLM-ASR 的速度代价。
- **Fun-ASR-MLT-Nano**：Fun-ASR-Nano 的 31 语言多语言版，补多语言维度，区别于纯中文的 Fun-ASR-Nano。

### VibeVoice-ASR-BitNet（纯 CPU 实时对照）

- 微软研究院出品，MIT 许可证，2026 年 7 月发布。原始 7B 模型通过 BitNet/GGUF 量化压缩到 1.58GB。
- **纯 CPU 实时**：3 线程 RTF 0.77，比 whisper.cpp 快 1.6-2.3×，不需要 MPS/GPU。
- 通过 llama.cpp 运行，无 Python 依赖，一个二进制文件即可。
- 中文 Fleurs-zh WER 8.35%，不如 SenseVoice(5.56%) 和 FunASR(7.00%)，但比 Whisper 小版本好。
- 定位：测"无 GPU 纯 CPU 环境下的极限速度"，和 FunASR 系（Python 环境、中文更强）形成对照。

## 设备策略（Mac Apple Silicon）

| 模型 | 自动策略 | 说明 |
| --- | --- | --- |
| whisper-turbo / large-v3 | MPS(mlx-whisper) 或 CPU(faster-whisper) | 优先 mlx-whisper；CPU 路径用 faster-whisper int8 |
| qwen3-asr-0.6b | MPS / bfloat16 | transformers 原生，macOS 14+ |
| qwen3-asr-1.7b | MPS / bfloat16 | 同上，内存约 5-6GB |
| sensevoice-small | CPU | FunASR 原生 CPU，MPS 支持待验证 |
| paraformer-large | CPU | FunASR, CPU 已足够快 |
| paraformer-streaming | CPU | FunASR, 流式低延迟 |
| fun-asr-nano | MPS 或 CPU | LLM 解码，CPU 上较慢；MPS 路径待验证 |
| fun-asr-mlt-nano | MPS 或 CPU | 同 Fun-ASR-Nano |
| whisper-base | **CPU** | faster-whisper int8，极低内存开销 |

## 暂不纳入的模型

| 模型 | 原因 |
| --- | --- |
| VibeVoice-ASR (7B) | 官方全量权重高达 17.3GB，远超端侧 Mac 存储承受范围，违背轻量端侧选型定位 |
| Voxtral Mini 4B Realtime | 4B 参数需 16GB GPU，端侧 Mac 吃力；且主要面向服务端流式 API |
| Cohere Transcribe 2B | 仓库 gated 需申请；无自动语言检测、无时间戳；GGUF 量化版可后续补 |
| Granite Speech 4.1 2B | 6 语言无中文；企业向 |
| Kyutai STT | 英法双语，无中文 |
| Parakeet TDT 0.6B v3 | 25 种欧洲语言，中文不支持；在中文场景评测中价值有限，后续如需多语言扩展再补 |
| MOSS-Transcribe-Diarize | 说话人分离是独立任务，后续可作为 diarization 扩展 |

## 环境规划

与 TTS arena 一致，每个模型族独立 venv：

| 环境名 | Python | 对应模型 | 主要依赖 |
| --- | --- | --- | --- |
| `whisper` | 3.12 | whisper-turbo, whisper-large-v3 | faster-whisper, mlx-whisper, whisper.cpp(binding) |
| `qwen3asr` | 3.12 | qwen3-asr-0.6b/1.7b | transformers>=5.13, torch, mlx-audio(可选) |
| `funasr` | 3.11 | sensevoice-small, paraformer-large, paraformer-streaming, fun-asr-nano, fun-asr-mlt-nano | funasr, torch |
| `vibevoice` | 系统/无需venv | vibevoice-asr-bitnet | llama.cpp 二进制，GGUF 模型文件 |

## 新增模型入口

与 TTS arena 相同：在 `config.py` 注册元数据，在 `model_files.py` 配置必要权重，新增 worker 适配器并在 `factory.py` 注册，在 `model_profiles.py` 定义支持的控制项（是否支持流式、是否支持热词、是否支持时间戳）。

接入后验证：权重加载 → 单音频转写 → 指标计算 → 失败原因记录。不能用模拟文本替代真实推理。
