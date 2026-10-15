import pytest
from backend.app.core.metrics import (
    normalize_text,
    NormalizationConfig,
    tokenize,
    levenshtein_align,
    compute_metrics,
)


def test_normalize_text():
    # 1. 全角转半角
    text = "ＡＢＣ１２３，你好！"
    norm = normalize_text(text)
    assert "ABC123" in norm

    # 2. 空白合并与裁剪
    text2 = "  你好   世界   "
    assert normalize_text(text2) == "你好 世界"

    # 3. 标点符号统一
    text3 = "Hello. World, Yes!"
    norm3 = normalize_text(text3)
    assert "Hello。 World， Yes！" == norm3

    # 4. 英文小写开关
    cfg_lower = NormalizationConfig(lowercase_english=True)
    assert normalize_text("Hello World", cfg_lower) == "hello world"

    # 5. 语气词剥离
    cfg_filler = NormalizationConfig(remove_fillers=True)
    assert normalize_text("嗯，你好啊，请问在吗？", cfg_filler) == "，你好，请问在吗？"


def test_tokenize():
    # 中文单字切分，英文连续词保留
    text = "请在 tomorrow 早上 9 点前提交"
    tokens = tokenize(text, mode="char")
    assert "请" in tokens
    assert "tomorrow" in tokens
    assert "9" in tokens


def test_levenshtein_align_and_metrics():
    # Case 1: 完全一致
    res1 = compute_metrics("今天天气真好", "今天天气真好")
    assert res1.cer == 0.0
    assert res1.substitutions == 0
    assert res1.deletions == 0
    assert res1.insertions == 0

    # Case 2: 替换错误 (S)
    # 参考="今天天气真好", 输出="今天天气真差" (好 -> 差)
    res2 = compute_metrics("今天天气真好", "今天天气真差")
    assert res2.substitutions == 1
    assert res2.deletions == 0
    assert res2.insertions == 0
    assert res2.cer == pytest.approx(1 / 6, 0.01)

    # Case 3: 漏字 (D - Deletion)
    # 参考="今天天气真好", 输出="今天真好" (漏"天气")
    res3 = compute_metrics("今天天气真好", "今天真好")
    assert res3.deletions == 2
    assert res3.substitutions == 0

    # Case 4: 幻觉多字 (I - Insertion)
    # 参考="今天天气真好", 输出="今天天气真真好" (多"真")
    res4 = compute_metrics("今天天气真好", "今天天气真真好")
    assert res4.insertions == 1
    assert res4.substitutions == 0


def test_english_wer():
    ref = "the quick brown fox"
    hyp = "the fast brown fox"
    res = compute_metrics(ref, hyp, language="en")
    assert res.wer == 0.25
    assert res.substitutions == 1
