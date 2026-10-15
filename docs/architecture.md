# 架构设计与流程图

[返回 README](../README.md) · [模型选型](models.md) · [评测总体](evaluation.md)

本文档描述 edge-asr-arena 的系统组件、请求链路、批次执行流和数据存储结构。架构对齐 edge-tts-arena 的后端/前端分离模式，但 worker 抽象从「文本→音频」改为「音频→文本」。

## 系统总览

```mermaid
flowchart TB
    subgraph FE["前端 (Vue 3/Vite/TailwindCSS)"]
        UI1[场景选型页]
        UI2[能力探索页<br/>录音/上传音频]
        UI3[评测配置页]
        UI4[结果分析页<br/>CER/WER 图表]
        UI5[转写对比页<br/>A/B 差异高亮]
        UI6[历史管理页]
    end

    subgraph BE["后端 (FastAPI)"]
        API[REST API 路由]
        JOB[批次调度器<br/>串行推理锁]
        METRIC[指标计算引擎<br/>CER/WER/对齐]
        STORE[结果存储<br/>.run.json + 音频]
        SYS[系统监控<br/>RSS/采样]
    end

    subgraph Workers["模型 Worker 进程 (.venvs/独立环境)"]
        W1[Whisper worker]
        W2[Qwen3-ASR worker]
        W3[FunASR worker<br/>SenseVoice/Paraformer/Nano]
        W4[VibeVoice worker<br/>llama.cpp/GGUF]
    end

    subgraph Assets["资产目录"]
        CK[checkpoints/<br/>模型权重]
        TS[testset/<br/>自录音频+参考转写]
        OUT[outputs/<br/>转写结果+指标]
    end

    UI1 & UI2 & UI3 & UI4 & UI5 & UI6 -->|HTTP/WebSocket| API
    API --> JOB
    JOB -->|串行调用| Workers
    Workers -->|转写文本+时间戳| API
    API --> METRIC
    METRIC -->|CER/WER| STORE
    SYS -->|采样 RSS| JOB
    STORE --> OUT
    Workers -.->|加载| CK
    JOB -.->|读取音频| TS
    FE -.->|播放原始音频| OUT
```

## 核心请求链路

### 离线转写评测批次

```mermaid
sequenceDiagram
    participant U as 用户(浏览器)
    participant API as FastAPI
    participant JOB as 批次调度器
    participant W as 模型 Worker
    participant M as 指标引擎
    participant S as 存储

    U->>API: POST /api/asr/compare/jobs<br/>{models, testset, repeats, mode:offline}
    API->>JOB: 创建批次 job_id
    JOB-->>U: 202 Accepted + job_id

    loop 每个 (模型 × 音频 × 次数)
        JOB->>W: 加载模型(首次) + 转写音频
        W-->>JOB: {text, timestamps, lang, elapsed, rss_peak}
        JOB->>M: 对比参考转写 → CER/WER
        M-->>JOB: {cer, wer, errors: {sub,del,ins}}
        JOB->>S: 写入 .run.json
    end

    JOB-->>U: WebSocket 推送进度
    U->>API: GET /api/asr/compare/jobs/{job_id}
    API-->>U: 完整结果 + 图表数据
```

### 流式 ASR 评测

```mermaid
sequenceDiagram
    participant U as 用户
    participant API as FastAPI
    participant W as 流式 Worker
    participant MIC as 模拟音频流

    U->>API: WS /api/asr/stream<br/>{model, chunk_size_ms, delay_ms}
    API->>W: 初始化流式会话

    loop 按 chunk 推送音频
        MIC->>API: 发送音频帧 (如 100ms)
        API->>W: feed_audio(chunk)
        W-->>API: 部分转写文本(增量)
        API-->>U: WS 推送 {text, is_final, ttf_ms}
    end

    W-->>API: 最终结果 {final_text, total_latency}
    API->>M: 与参考转写对齐
    API-->>U: 流式评测报告
```

## 批次执行流

```mermaid
flowchart LR
    A[选择模型列表] --> B[选择测试集维度<br/>如:噪声/CER]
    B --> C[选择重复次数<br/>1/2/3/5]
    C --> D[选择模式<br/>离线/流式]
    D --> E[创建批次<br/>任务队列:模型×音频×次数]
    E --> F{串行执行}
    F --> G[加载模型<br/>独立 venv]
    G --> H[读取音频文件]
    H --> I[转写推理]
    I --> J[采样 RSS]
    J --> K[计算 CER/WER]
    K --> L[写入 .run.json]
    L --> M{还有任务?}
    M -->|是| F
    M -->|否| N[批次完成]
    N --> O[前端展示图表+对比]
```

## 目录结构

```
edge-asr-arena/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── core/
│   │   │   ├── config.py        # 模型注册表
│   │   │   ├── model_files.py   # 必要权重文件校验
│   │   │   ├── model_profiles.py # 支持的控制项
│   │   │   └── metrics.py       # CER/WER/对齐
│   │   ├── adapters/
│   │   │   ├── factory.py       # worker 注册
│   │   │   └── base.py          # ASRWorker 抽象基类
│   │   ├── workers/
│   │   │   ├── whisper.py
│   │   │   ├── qwen3_asr.py
│   │   │   ├── funasr.py
│   │   │   └── vibevoice.py
│   │   └── api/
│   │       ├── routes_compare.py
│   │       ├── routes_runs.py
│   │       └── routes_stream.py
│   └── requirements.txt
├── frontend/                    # Vue 3/Vite/TailwindCSS, 对齐 tts-arena
├── checkpoints/                 # 模型权重 (git-ignored)
├── testset/                     # 自录测试音频 + 参考转写
│   ├── 01-mandarin/
│   ├── 02-english/
│   ├── 04-code-switch/
│   ├── 05-dialect/
│   ├── 06-noise/
│   ├── 07-farfield/
│   ├── 08-numbers/
│   ├── 09-emotion/
│   └── manifest.json           # 每条音频:路径/参考文本/SNR/说话人/时长
├── outputs/                     # 转写结果 (git-ignored)
├── scripts/
│   ├── setup_env.sh
│   ├── setup_models.py
│   ├── download.sh
│   └── model_requirements/
├── docs/
│   ├── architecture.md         # 本文档
│   ├── models.md
│   ├── evaluation.md
│   └── specs/                  # 10 份评测需求规格
└── README.md
```

## 数据模型

### `.run.json`（单条转写记录）

```json
{
  "run_id": "whisper-turbo_20261013_001",
  "model_key": "whisper-large-v3-turbo",
  "mode": "offline",
  "audio_file": "testset/06-noise/cafe_snr10_003.wav",
  "reference_text": "请明天下午三点前把报告发给我",
  "hypothesis_text": "请明天下午3点前把报告发给我",
  "language": "zh",
  "timestamps": [...],
  "metrics": {
    "cer": 0.023,
    "wer": 0.0,
    "substitutions": 0,
    "deletions": 0,
    "insertions": 0
  },
  "elapsed_ms": 1240,
  "audio_duration_ms": 3200,
  "rtf": 0.387,
  "memory_peak_mb": 1420,
  "device": "mps",
  "precision": "float16",
  "retry_attempt": 0,
  "status": "success"
}
```

### 流式记录额外字段

```json
{
  "stream_chunks": [
    {"offset_ms": 0, "text": "", "ttfb_ms": null},
    {"offset_ms": 300, "text": "请明天", "ttfb_ms": 312},
    {"offset_ms": 600, "text": "请明天下午", "ttfb_ms": null}
  ],
  "first_token_ms": 312,
  "chunk_interval_ms": 300
}
```

## 关键设计决策

1. **串行推理锁**：与 TTS arena 一致，所有模型转写在同一进程锁内串行执行，避免 MPS/CPU 资源争抢导致指标失真。
2. **独立 venv per model family**：Whisper 用 faster-whisper，FunASR 系用独立 venv，Qwen3-ASR 用 transformers 原生环境，互不污染。
3. **测试集 manifest 驱动**：`testset/manifest.json` 统一描述每条音频的元信息（SNR、说话人、场景标签），批次按维度筛选。
4. **CER/WER 自动计算**：用 `jiwer` 或 `editdistance` 库，先做文本归一化（见 spec 01）再对齐。
5. **失败不进入统计**：与 TTS arena 一致，失败项保留记录但不参与中位数计算。
6. **流式与离线分离**：同一模型若支持两种模式，分别记录；不支持流式的模型在流式批次中自动不可选。
