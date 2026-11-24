#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工作区约定：基于当前工作目录（或 PAIXU_ROOT）的 input/ 与 output/。"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_OUTPUT_NAME = "sorted.txt"

# 参与排序的输入文件后缀（空字符串表示无扩展名文件）
SUPPORTED_SUFFIXES = {".txt", ".text", ".md", ".csv", ".log", ""}


class Workspace:
    """解析并持有一处工作区的根目录与输入输出目录。"""

    def __init__(self, root: Path | None = None) -> None:
        if root is None:
            env = os.environ.get("PAIXU_ROOT")
            root = Path(env).expanduser() if env else Path.cwd()
        self.root = root.resolve()
        self.input_dir = self.root / "input"
        self.output_dir = self.root / "output"

    def ensure_dirs(self) -> tuple[Path, Path]:
        """确保 input 与 output 目录存在，返回两者路径。"""
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.input_dir, self.output_dir

    def discover_inputs(self) -> list[Path]:
        """返回输入目录中的文本文件，按文件名排序。"""
        return sorted(
            path
            for path in self.input_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
        )

    def default_output_path(self) -> Path:
        """返回默认输出文件路径 output/sorted.txt。"""
        return self.output_dir / DEFAULT_OUTPUT_NAME
