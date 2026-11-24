#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文本规范化：剥离行首编号与前导标点，供排序键计算使用。"""

from __future__ import annotations

import re

# 行首编号：1. / 2、 / (3) / 4： / [5] / 一、 / （二） / A) / b.
# 分隔符后不能紧跟数字，避免把 "1.5 倍" 误判为编号。
_NUM_PREFIX = re.compile(
    r"^\s*[（(\[]?\s*(?:\d+|[一二三四五六七八九十百]+|[A-Za-z])\s*"
    r"[）)\].、,，:：](?!\d)\s*"
)

# 计算排序键时忽略的行首符号
_PUNCT_CHARS = (
    " \t\u3000\"'“”‘’()（）[]【】{}<>《》,，.。、;；:：!！?？—–-…·~`@#$%^&*_+=|\\/"
)
_PUNCT_STR = "".join(sorted(set(_PUNCT_CHARS)))


def strip_number_prefix(line: str) -> str:
    """去掉行首编号，支持阿拉伯数字、中文数字与字母编号。"""
    return _NUM_PREFIX.sub("", line)


def strip_leading_punctuation(text: str) -> str:
    """去掉前导标点；若整行都是标点则保留原文。"""
    stripped = text.lstrip(_PUNCT_STR)
    return stripped or text


def normalize_line(
    line: str, *, strip_numbers: bool = True, strip_punctuation: bool = True
) -> str:
    """按配置规范化一行文本，返回用于计算排序键的文本。"""
    result = line
    if strip_numbers:
        result = strip_number_prefix(result)
    if strip_punctuation:
        result = strip_leading_punctuation(result)
    return result
