"""排序核心判据：拼音序、稳定性、去重、逆序、空行处理。"""

from __future__ import annotations

import pytest

from paixu.core import LineRecord, SortOptions, sort_lines, sort_records
from paixu.pinyin import pinyin_available

names = ["3. 张三", "1、李四", "2）王五"]


@pytest.mark.skipif(not pinyin_available(), reason="未安装 pypinyin：拼音序判据不适用")
def test_sort_by_pinyin() -> None:
    """li < wang < zhang —— 输出是**原文**（编号仍在），只有排序键被清洗。"""
    assert sort_lines(names) == ["1、李四", "2）王五", "3. 张三"]


def test_reverse() -> None:
    got = sort_lines(names, SortOptions(use_pinyin=False, reverse=True))
    assert got == list(reversed(sort_lines(names, SortOptions(use_pinyin=False))))


def test_blank_lines_are_dropped() -> None:
    assert sort_lines(["b", "", "   ", "a"], SortOptions(use_pinyin=False)) == ["a", "b"]


def test_stable_for_equal_keys() -> None:
    """键相同保持输入顺序 —— 稳定排序是契约，不是实现细节。"""
    records = [LineRecord(text="1. 张三"), LineRecord(text="2. 张三"), LineRecord(text="张三")]
    ordered = sort_records(records, SortOptions(use_pinyin=False))
    assert [r.text for r in ordered] == ["1. 张三", "2. 张三", "张三"]


def test_dedupe_uses_sort_key() -> None:
    """`1. 张三` 与 `张三` 的键相同，去重后只留先出现的那条原文。"""
    got = sort_lines(["1. 张三", "张三", "李四"], SortOptions(use_pinyin=False, dedupe=True))
    assert got == ["1. 张三", "李四"]


def test_keys_are_exposed_on_records() -> None:
    ordered = sort_records([LineRecord(text="1. 张三")], SortOptions(use_pinyin=False))
    assert ordered[0].key == "张三"
    assert ordered[0].text == "1. 张三"


def test_case_sensitivity_switch() -> None:
    lower = sort_lines(["B", "a"], SortOptions(use_pinyin=False, case_sensitive=False))
    assert lower == ["a", "B"]          # casefold 后 a < b
    exact = sort_lines(["B", "a"], SortOptions(use_pinyin=False, case_sensitive=True))
    assert exact == ["B", "a"]          # 码位序 B(66) < a(97)
