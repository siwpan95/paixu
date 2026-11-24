"""CLI 边界判据：退出码、stdout 与 stderr 分流、机器格式信封。

**测什么、为什么**：`paixu` 的机器友好约定（数据走 stdout、人类消息走 stderr、
失败时 JSON 仍有 `ok:false` 信封）是它对下游的承诺。这些约定一旦破了，
`paixu x.txt --format json | jq` 会在报错时静默拿到半个文档 —— 比崩掉更难查。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from paixu.cli import main


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_text_output_goes_to_stdout(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = _write(tmp_path, "in.txt", "2. 李四\n1. 张三\n")
    assert main([str(src)]) == 0
    out = capsys.readouterr().out
    # 拼音序：li（李四）在 zhang（张三）之前 —— 排序键清洗了编号，输出仍是原文
    assert out.splitlines() == ["2. 李四", "1. 张三"]


def test_json_envelope_on_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = _write(tmp_path, "in.txt", "2. 李四\n1. 张三\n")
    assert main([str(src), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    items = payload["results"][0]["items"]
    assert [item["line"] for item in items] == ["2. 李四", "1. 张三"]
    assert items[0]["source_line"] == 1                 # 保留来源行号（文件第 1 行）


def test_missing_file_is_runtime_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """读不到文件：退出码 1（不是 2），且错误只在 stderr —— stdout 不许被污染。"""
    assert main([str(tmp_path / "nope.txt")]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "nope.txt" in captured.err


def test_missing_file_json_still_emits_envelope(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """失败时机器格式仍输出 `ok:false` 信封 —— 下游不能靠「有没有输出」判断成败。"""
    assert main([str(tmp_path / "nope.txt"), "--format", "json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["errors"]


def test_schema_is_machine_readable(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--schema"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert "exit_codes" in payload


def test_conflicting_flags_are_usage_errors() -> None:
    """`--first-letter` + `--no-pinyin` 是用法错：argparse 抛 SystemExit(2)。"""
    with pytest.raises(SystemExit) as excinfo:
        main(["--first-letter", "--no-pinyin"])
    assert excinfo.value.code == 2


def test_output_file_written(tmp_path: Path) -> None:
    src = _write(tmp_path, "in.txt", "b\na\n")
    target = tmp_path / "out.txt"
    assert main([str(src), "-o", str(target)]) == 0
    assert target.read_text(encoding="utf-8").splitlines() == ["a", "b"]
