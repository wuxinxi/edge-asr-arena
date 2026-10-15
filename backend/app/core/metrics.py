"""
edge-asr-arena 指标计算与文本归一化引擎
对齐 docs/specs/01-accuracy-metrics.md 规范
"""

import re
import unicodedata
from typing import List, Tuple, Dict, Any, Optional
from pydantic import BaseModel, Field


class NormalizationConfig(BaseModel):
    """文本归一化配置项"""
    fullwidth_to_halfwidth: bool = True       # 全角数字/字母转半角
    collapse_whitespace: bool = True          # 连续空白合并
    trim_whitespace: bool = True              # 首尾空白去除
    unify_punctuation: bool = True            # 标点符号统一
    lowercase_english: bool = False           # 英文转小写（默认关）
    normalize_numbers: bool = False           # 口语数字转阿拉伯数字（默认关）
    remove_fillers: bool = False              # 剥离语气词 (嗯/啊等)
    traditional_to_simplified: bool = False   # 繁体转简体（默认关）


# 常见语气词正则
FILLER_WORDS_PATTERN = re.compile(r"[啊呃嗯呀吧啦哦哈呐哇]+")

# 标点映射：英文标点 -> 中文标点
PUNCT_MAP = {
    ',': '，',
    '.': '。',
    '!': '！',
    '?': '？',
    ':': '：',
    ';': '；',
    '(': '（',
    ')': '）',
    '[': '【',
    ']': '】',
    '"': '"',
    "'": "'",
}


def normalize_text(text: str, config: Optional[NormalizationConfig] = None) -> str:
    """对输入文本应用归一化流水线"""
    if not text:
        return ""
    if config is None:
        config = NormalizationConfig()

    # 1. 全角字符转半角 (Unicode NFKC 形式)
    if config.fullwidth_to_halfwidth:
        # 使用 NFKC 分解并重组兼容字符
        text = unicodedata.normalize("NFKC", text)

    # 2. 标点符号统一
    if config.unify_punctuation:
        for en_p, zh_p in PUNCT_MAP.items():
            text = text.replace(en_p, zh_p)

    # 3. 英文大小写
    if config.lowercase_english:
        text = text.lower()

    # 4. 剥离语气词
    if config.remove_fillers:
        text = FILLER_WORDS_PATTERN.sub("", text)

    # 5. 空白处理
    if config.collapse_whitespace:
        text = re.sub(r"\s+", " ", text)
    if config.trim_whitespace:
        text = text.strip()

    return text


def tokenize(text: str, mode: str = "char") -> List[str]:
    """
    分词切分:
    - mode="char": 中文按字符切分（英文连续词作为单个 token，或者纯单字）
    - mode="word": 英文按空格/词切分
    """
    if not text:
        return []
    if mode == "word":
        return text.split()
    
    # 智能字符模式：中文按单字切分，连续英文字母/数字作为一个整体 token
    tokens: List[str] = []
    current_alnum: List[str] = []
    
    for ch in text:
        if ch.isalnum() and ch.isascii():
            current_alnum.append(ch)
        else:
            if current_alnum:
                tokens.append("".join(current_alnum))
                current_alnum = []
            if not ch.isspace():
                tokens.append(ch)
                
    if current_alnum:
        tokens.append("".join(current_alnum))
        
    return tokens


def levenshtein_align(
    ref_tokens: List[str], hyp_tokens: List[str]
) -> Tuple[int, int, int, List[Tuple[str, Optional[str], Optional[str]]]]:
    """
    Levenshtein 动态规划对齐，计算 S, D, I 及详细对齐序列。
    返回: (substitutions, deletions, insertions, alignments)
    alignments 列表项: (op, ref_token, hyp_token)
    op in ['equal', 'sub', 'del', 'ins']
    """
    n, m = len(ref_tokens), len(hyp_tokens)
    # dp[i][j] = distance
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref_tokens[i - 1] == hyp_tokens[j - 1]:
                cost = 0
            else:
                cost = 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,       # deletion
                dp[i][j - 1] + 1,       # insertion
                dp[i - 1][j - 1] + cost # substitution or match
            )

    # 回溯生成对齐序列
    alignments: List[Tuple[str, Optional[str], Optional[str]]] = []
    i, j = n, m
    sub_count = 0
    del_count = 0
    ins_count = 0

    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] and ref_tokens[i - 1] == hyp_tokens[j - 1]:
            alignments.append(("equal", ref_tokens[i - 1], hyp_tokens[j - 1]))
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            alignments.append(("sub", ref_tokens[i - 1], hyp_tokens[j - 1]))
            sub_count += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            alignments.append(("del", ref_tokens[i - 1], None))
            del_count += 1
            i -= 1
        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            alignments.append(("ins", None, hyp_tokens[j - 1]))
            ins_count += 1
            j -= 1
        else:
            # 边界容错
            if i > 0:
                alignments.append(("del", ref_tokens[i - 1], None))
                del_count += 1
                i -= 1
            elif j > 0:
                alignments.append(("ins", None, hyp_tokens[j - 1]))
                ins_count += 1
                j -= 1

    alignments.reverse()
    return sub_count, del_count, ins_count, alignments


class MetricsResult(BaseModel):
    """评测指标结果"""
    cer: float
    wer: float
    substitutions: int
    deletions: int
    insertions: int
    ref_length: int
    hyp_length: int
    normalized_ref: str
    normalized_hyp: str
    alignments: List[Tuple[str, Optional[str], Optional[str]]] = Field(default_factory=list)


def compute_metrics(
    reference: str,
    hypothesis: str,
    norm_config: Optional[NormalizationConfig] = None,
    language: str = "zh",
) -> MetricsResult:
    """
    计算 CER/WER 指标及错误分解
    - language="zh": 中文主导，按字符 token 计算 CER
    - language="en": 英文主导，按词计算 WER
    """
    cfg = norm_config or NormalizationConfig()
    norm_ref = normalize_text(reference, cfg)
    norm_hyp = normalize_text(hypothesis, cfg)

    # 中文按字符 token，英文按词 token
    token_mode = "char" if language.lower().startswith("zh") else "word"
    ref_tokens = tokenize(norm_ref, mode=token_mode)
    hyp_tokens = tokenize(norm_hyp, mode=token_mode)

    sub, dele, ins, aligns = levenshtein_align(ref_tokens, hyp_tokens)
    ref_len = len(ref_tokens)
    hyp_len = len(hyp_tokens)

    # 错误率计算：(S + D + I) / N_ref，避免除零
    if ref_len == 0:
        error_rate = 1.0 if hyp_len > 0 else 0.0
    else:
        error_rate = round((sub + dele + ins) / ref_len, 4)

    # 如果是中文，cer 为主要指标，wer 同步给出词级或设为 error_rate
    cer = error_rate if token_mode == "char" else 0.0
    wer = error_rate if token_mode == "word" else 0.0

    return MetricsResult(
        cer=cer,
        wer=wer,
        substitutions=sub,
        deletions=dele,
        insertions=ins,
        ref_length=ref_len,
        hyp_length=hyp_len,
        normalized_ref=norm_ref,
        normalized_hyp=norm_hyp,
        alignments=aligns,
    )
