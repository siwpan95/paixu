#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拼音转换封装：优先使用 pypinyin；缺失时透明降级为按原字符排序。"""

from __future__ import annotations

from typing import Callable

try:
    from pypinyin import Style, lazy_pinyin  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - 取决于运行环境
    Style = None  # type: ignore[assignment]
    lazy_pinyin = None  # type: ignore[assignment]


def pinyin_available() -> bool:
    """返回是否可以使用 pypinyin 进行拼音转换。"""
    return lazy_pinyin is not None


def pinyin_error_hint() -> str:
    """返回安装 pypinyin 的提示文本。"""
    return "未检测到 pypinyin，中文将按 Unicode 码位排序。请执行: pip install pypinyin"


def make_translator(
    *, use_pinyin: bool = True, first_letter: bool = False
) -> Callable[[str], str]:
    """构造把文本转为排序用字符串的转换函数。

    默认使用 pypinyin 的 NORMAL 风格并原样保留非中文字符（与 lazy_pinyin
    默认 errors 策略一致）；first_letter=True 时改用拼音首字母。缺少
    pypinyin 或 use_pinyin=False 时按原字符返回，由调用方决定是否警告。
    """
    if use_pinyin and lazy_pinyin is not None:
        style = Style.FIRST_LETTER if first_letter else Style.NORMAL

        def translate(text: str) -> str:
            return "".join(lazy_pinyin(text, style=style))

        return translate

    def passthrough(text: str) -> str:
        return text

    return passthrough
