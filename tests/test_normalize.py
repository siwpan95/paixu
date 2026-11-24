"""规范化判据：编号剥离与前导标点剥离的边界。

这些用例的价值在**边界**，不在happy path：正则写宽了会把 `1.5 倍` 当编号剥掉，
写窄了会漏 `（二）` 这种全角编号 —— 两种都会让排序结果悄悄错位，而输出看起来正常。
"""

from __future__ import annotations

import pytest

from paixu.normalize import normalize_line, strip_leading_punctuation, strip_number_prefix


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1. 张三", "张三"),
        ("2、李四", "李四"),
        ("(3) 王五", "王五"),
        ("（4）赵六", "赵六"),
        ("5：钱七", "钱七"),
        ("[6] 孙八", "孙八"),
        ("一、周九", "周九"),
        ("（二）吴十", "吴十"),
        ("A) Alice", "Alice"),
        ("b. bob", "bob"),
        ("  7. 郑十一", "郑十一"),
    ],
)
def test_strip_number_prefix_variants(raw: str, expected: str) -> None:
    assert strip_number_prefix(raw) == expected


def test_number_prefix_does_not_eat_decimals() -> None:
    """`1.5 倍` 不是编号 —— 分隔符后紧跟数字时必须保留原样。"""
    assert strip_number_prefix("1.5 倍") == "1.5 倍"


def test_number_prefix_leaves_plain_text_alone() -> None:
    assert strip_number_prefix("张三") == "张三"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('"张三', "张三"),
        ("《李四》", "李四》"),
        ("- 王五", "王五"),
        ("...赵六", "赵六"),
    ],
)
def test_strip_leading_punctuation(raw: str, expected: str) -> None:
    assert strip_leading_punctuation(raw) == expected


def test_all_punctuation_line_is_kept() -> None:
    """整行都是标点时保留原文 —— 否则会变成空行，被下游当空白行丢掉。"""
    assert strip_leading_punctuation("...") == "..."


def test_normalize_line_respects_switches() -> None:
    raw = "1. 《张三》"
    assert normalize_line(raw) == "张三》"          # 默认：编号 + 前导标点都剥
    # 保留编号时前导标点剥不动：lstrip 只吃行首，而这一行以 "1" 开头，
    # 标点在被保留的编号后面。这是 kept-numbers 的应有语义（保留原样前缀），
    # 不是缺陷 —— 已写进 README「已知边界」。
    assert normalize_line(raw, strip_numbers=False) == "1. 《张三》"
    assert normalize_line(raw, strip_punctuation=False) == "《张三》"   # 编号照剥、标点留着
