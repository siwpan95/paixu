#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""paixu：按拼音排序文本行，剥离行首编号与标点。

公共 API::

    from paixu import SortOptions, sort_lines
    result = sort_lines(["3. 张三", "1. 李四"])

命令行::

    python -m paixu names.txt
    paixu names.txt            # 安装后
"""

from .core import LineRecord, SortOptions, sort_lines, sort_records
from .normalize import (
    normalize_line,
    strip_leading_punctuation,
    strip_number_prefix,
)
from .pinyin import pinyin_available
from .workspace import Workspace

__version__ = "0.1.0"

__all__ = [
    "LineRecord",
    "SortOptions",
    "sort_lines",
    "sort_records",
    "normalize_line",
    "strip_number_prefix",
    "strip_leading_punctuation",
    "pinyin_available",
    "Workspace",
    "__version__",
]
