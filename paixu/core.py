#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""排序核心：将文本行按规范化排序键稳定排序。"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Iterable

from .normalize import normalize_line
from .pinyin import make_translator


@dataclass(frozen=True)
class LineRecord:
    """带来源信息的单行记录，key 由 sort_records 计算填充。"""

    text: str
    source: str = "-"
    source_line: int = 0
    key: str = ""


@dataclass(frozen=True)
class SortOptions:
    """排序行为配置。"""

    reverse: bool = False
    case_sensitive: bool = False
    use_pinyin: bool = True
    first_letter: bool = False
    strip_numbers: bool = True
    strip_punctuation: bool = True
    dedupe: bool = False

    def build_key(self) -> Callable[[str], str]:
        """根据当前配置构造排序键函数。"""
        translate = make_translator(
            use_pinyin=self.use_pinyin, first_letter=self.first_letter
        )

        def key(line: str) -> str:
            text = normalize_line(
                line,
                strip_numbers=self.strip_numbers,
                strip_punctuation=self.strip_punctuation,
            )
            result = translate(text)
            return result if self.case_sensitive else result.casefold()

        return key


def sort_records(
    records: Iterable[LineRecord], options: SortOptions | None = None
) -> list[LineRecord]:
    """按排序键稳定排序记录；忽略空白行，可选按排序键去重。"""
    opts = options if options is not None else SortOptions()
    key_fn = opts.build_key()
    valid = [r for r in records if r.text]
    enriched = [replace(r, key=key_fn(r.text)) for r in valid]
    ordered = sorted(enriched, key=lambda r: r.key, reverse=opts.reverse)
    if not opts.dedupe:
        return ordered

    # 按排序键去重（如 "1. 张三" 与 "张三" 视为重复），保留先出现的原文。
    seen: set[str] = set()
    unique: list[LineRecord] = []
    for item in ordered:
        if item.key not in seen:
            seen.add(item.key)
            unique.append(item)
    return unique


def sort_lines(lines: Iterable[str], options: SortOptions | None = None) -> list[str]:
    """按排序键稳定排序；忽略空白行，输出去除首尾空白的原文。"""
    opts = options if options is not None else SortOptions()
    records = [
        LineRecord(text=stripped, source="-", source_line=n)
        for n, line in enumerate(lines, 1)
        if (stripped := line.strip())
    ]
    return [r.text for r in sort_records(records, opts)]
