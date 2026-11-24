#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""paixu 的命令行接口。

机器友好约定（clig.dev）：
- 数据走 stdout，人类消息走 stderr；
- 结构化输出显式启用：--format json|ndjson|csv；
- 失败时 json/ndjson 仍向 stdout 输出 ok=false 信封；
- 退出码：0 成功，1 运行时错误，2 用法错误。
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from typing import Sequence

from . import __version__
from .core import LineRecord, SortOptions, sort_records
from .pinyin import pinyin_available, pinyin_error_hint
from .workspace import Workspace

FORMATS = ("text", "json", "ndjson", "csv")


def build_parser() -> argparse.ArgumentParser:
    """构造参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="paixu",
        description=(
            "按拼音排序文本行：自动剥离行首编号与标点，输出原文（不带编号）。\n"
            "无文件参数且为交互运行时，自动读取工作目录 input/ 下的文本文件："
            "text 格式逐个写入 output/ 下的同名文件；机器格式写标准输出。\n"
            "目录不存在会自动创建；工作目录默认为当前目录，可用 PAIXU_ROOT 指定。"
        ),
        epilog=(
            "示例:\n"
            "  paixu                       # 交互模式：input/*.txt -> output/同名文件\n"
            "  paixu names.txt             # 指定文件，结果写到标准输出\n"
            "  cat names.txt | paixu       # 管道输入\n"
            "  paixu a.txt b.txt -o out.txt --reverse\n"
            "  paixu --format ndjson       # 机器可读流式输出\n"
            "  python -m paixu --schema    # 机器可读接口描述\n"
            "\n"
            "Exit status:\n"
            "  0  成功（含空输入）\n"
            "  1  运行时错误：读取/写入失败，或部分文件处理失败\n"
            "  2  用法错误：参数不合法"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="输入文件（可多个）；省略时交互模式用 input/，管道模式用标准输入",
    )
    parser.add_argument(
        "-o", "--output", metavar="FILE", help="输出文件；省略时写到标准输出"
    )
    parser.add_argument(
        "--format",
        choices=FORMATS,
        default="text",
        help="输出格式（默认: text）；json/ndjson/csv 为机器可读格式",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="抑制非错误提示（警告、写入路径等）；错误仍输出到标准错误",
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="输出机器可读的接口描述（JSON）并退出",
    )
    parser.add_argument(
        "-e", "--encoding", default="utf-8", help="读写编码（默认: utf-8）"
    )
    parser.add_argument(
        "--errors",
        default="strict",
        choices=["strict", "ignore", "replace"],
        help="解码错误策略（默认: strict）",
    )

    ordering = parser.add_argument_group("排序选项")
    ordering.add_argument("-r", "--reverse", action="store_true", help="降序排列")
    ordering.add_argument(
        "--first-letter", action="store_true", help="按拼音首字母排序（需 pypinyin）"
    )
    ordering.add_argument(
        "--no-pinyin", action="store_true", help="禁用拼音转换，按原字符排序"
    )
    ordering.add_argument(
        "--require-pinyin",
        action="store_true",
        help="要求必须可用 pypinyin，否则报错退出",
    )
    ordering.add_argument(
        "--case-sensitive", action="store_true", help="区分大小写（默认不区分）"
    )
    ordering.add_argument(
        "--keep-numbers", action="store_true", help="保留行首编号参与排序"
    )
    ordering.add_argument(
        "--keep-punctuation", action="store_true", help="保留前导标点参与排序"
    )
    ordering.add_argument(
        "--dedupe", action="store_true", help="按排序键去重（如 1. 张三 与 张三 视为重复）"
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


def build_schema() -> dict:
    """返回机器可读的接口描述。"""
    return {
        "name": "paixu",
        "version": __version__,
        "description": "按拼音排序文本行，剥离行首编号与标点",
        "formats": list(FORMATS),
        "exit_codes": {
            "0": "成功（含空输入）",
            "1": "运行时错误：读取/写入失败，或部分文件处理失败",
            "2": "用法错误：参数不合法",
        },
        "io": {
            "data": "stdout",
            "messages": "stderr",
            "workspace": "input/ -> output/（交互 text 模式），PAIXU_ROOT 指定根目录",
            "newline": "\n",
            "bom": "输出始终无 BOM；UTF-8 系列输入自动剥离 BOM",
        },
        "json_contract": {
            "ok": "bool",
            "version": "str",
            "results[].source": "str|null（单文件为路径；多文件汇总为 null；管道为 -）",
            "results[].count": "int",
            "results[].deduped": "int（被 --dedupe 剔除的行数）",
            "results[].output": "str?（text 格式写入的文件路径）",
            "results[].items[].rank": "int（1-based）",
            "results[].items[].line": "str",
            "results[].items[].key": "str（排序键）",
            "results[].items[].source": "str",
            "results[].items[].source_line": "int",
            "errors[].message": "str（部分失败时出现）",
        },
        "flags": {
            "--format": "text|json|ndjson|csv（默认 text）",
            "-o/--output": "输出文件（text 格式）",
            "-e/--encoding": "读写编码（默认 utf-8）",
            "--errors": "strict|ignore|replace",
            "-r/--reverse": "降序排列",
            "--first-letter": "按拼音首字母排序（需 pypinyin）",
            "--no-pinyin": "禁用拼音转换，按原字符排序",
            "--require-pinyin": "无 pypinyin 时报错退出",
            "--case-sensitive": "区分大小写",
            "--keep-numbers": "保留行首编号参与排序",
            "--keep-punctuation": "保留前导标点参与排序",
            "--dedupe": "按排序键去重",
            "-q/--quiet": "抑制非错误提示",
            "--schema": "输出本描述",
        },
    }


_UTF8_ALIASES = {"utf-8", "utf8", "utf-8-sig", "utf8-sig"}


def _read_encoding(encoding: str) -> str:
    """读取编码：UTF-8 系列按 utf-8-sig 解码，自动剥离 BOM。"""
    return "utf-8-sig" if encoding.lower().replace("_", "-") in _UTF8_ALIASES else encoding


def _write_encoding(encoding: str) -> str:
    """写入编码：UTF-8 系列统一写出无 BOM 的 utf-8。"""
    return "utf-8" if encoding.lower().replace("_", "-") in _UTF8_ALIASES else encoding


def _info(quiet: bool, message: str) -> None:
    """向标准错误输出信息性提示，quiet 时抑制。"""
    if not quiet:
        print(message, file=sys.stderr)


def _error(message: str) -> None:
    """向标准错误输出错误信息（不受 quiet 影响）。"""
    print(message, file=sys.stderr)


def _read_records(
    entries: Sequence[tuple[str, str]], encoding: str, errors: str
) -> list[LineRecord]:
    """按 (读取路径, 来源显示名) 读取行；空白行被忽略，空列表读标准输入。"""
    codec = _read_encoding(encoding)
    records: list[LineRecord] = []

    def collect(text: str, source: str) -> None:
        for n, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped:
                records.append(LineRecord(text=stripped, source=source, source_line=n))

    if not entries:
        buffer = getattr(sys.stdin, "buffer", None)
        data = (
            buffer.read().decode(codec, errors=errors)
            if buffer is not None
            else sys.stdin.read()
        )
        collect(data, "-")
        return records

    for path, label in entries:
        with open(path, encoding=codec, errors=errors) as handle:
            collect(handle.read(), label)
    return records


def _process_unit(
    entries: Sequence[tuple[str, str]],
    source_label: str | None,
    args: argparse.Namespace,
    options: SortOptions,
) -> tuple[dict | None, dict | None]:
    """处理一个输入单元，返回 (结果, 错误)，二者恰好其一非空。"""
    try:
        records = _read_records(entries, args.encoding, args.errors)
    except OSError as exc:
        return None, {"source": source_label, "message": f"无法读取输入: {exc}"}
    except UnicodeError as exc:
        return (
            None,
            {"source": source_label, "message": f"解码失败（可用 --errors 调整）: {exc}"},
        )

    ordered = sort_records(records, options)
    items = [
        {
            "rank": rank,
            "line": record.text,
            "key": record.key,
            "source": record.source,
            "source_line": record.source_line,
        }
        for rank, record in enumerate(ordered, 1)
    ]
    result = {
        "source": source_label,
        "count": len(items),
        "deduped": len(records) - len(items),
        "items": items,
    }
    return result, None


def _text_body(result: dict) -> str:
    """渲染 text 格式正文。"""
    output = "\n".join(item["line"] for item in result["items"])
    return f"{output}\n" if output else ""


def _write_output(target: str, content: str, encoding: str) -> dict | None:
    """把内容写入目标文件，失败返回错误对象。"""
    try:
        with open(target, "w", encoding=_write_encoding(encoding), newline="\n") as handle:
            handle.write(content)
        return None
    except OSError as exc:
        return {"source": target, "message": f"无法写入输出: {exc}"}


def _emit(args: argparse.Namespace, results: list[dict], errors: list[dict]) -> None:
    """把机器格式结果写到标准输出；失败同样输出信封。"""
    ok = not errors
    if args.format == "json":
        payload: dict = {"ok": ok, "version": __version__, "results": results}
        if errors:
            payload["errors"] = errors
            payload["error"] = {"message": errors[0]["message"]}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.format == "ndjson":
        for result in results:
            for rank, item in enumerate(result["items"], 1):
                line_obj = {
                    "file": item["source"],
                    "rank": rank,
                    "line": item["line"],
                    "key": item["key"],
                    "source_line": item["source_line"],
                }
                print(json.dumps(line_obj, ensure_ascii=False))
        summary = {
            "summary": True,
            "ok": ok,
            "count": sum(r["count"] for r in results),
            "deduped": sum(r["deduped"] for r in results),
        }
        if errors:
            summary["error"] = errors[0]["message"]
        print(json.dumps(summary, ensure_ascii=False))
    elif args.format == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(["file", "rank", "line", "key", "source_line"])
        for result in results:
            for rank, item in enumerate(result["items"], 1):
                writer.writerow(
                    [item["source"], rank, item["line"], item["key"], item["source_line"]]
                )
        sys.stdout.write(buffer.getvalue())


def _force_utf8_stdio() -> None:
    """把标准输出/错误固定为 UTF-8 与 LF 换行，保证管道输出编码确定。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", newline="\n")
        except (OSError, ValueError):  # pragma: no cover - 特殊流可能不支持
            pass


def main(argv: Sequence[str] | None = None) -> int:
    """CLI 主入口，返回进程退出码。"""
    _force_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.schema:
        print(json.dumps(build_schema(), ensure_ascii=False, indent=2))
        return 0

    if args.first_letter and args.no_pinyin:
        parser.error("--first-letter 与 --no-pinyin 不能同时使用")
    available = pinyin_available()
    if args.require_pinyin and not available:
        parser.error(pinyin_error_hint())
    if args.first_letter and not available:
        parser.error("--first-letter 需要 pypinyin。请执行: pip install pypinyin")

    options = SortOptions(
        reverse=args.reverse,
        case_sensitive=args.case_sensitive,
        use_pinyin=not args.no_pinyin,
        first_letter=args.first_letter,
        strip_numbers=not args.keep_numbers,
        strip_punctuation=not args.keep_punctuation,
        dedupe=args.dedupe,
    )
    if options.use_pinyin and not available:
        _info(args.quiet, f"paixu: 警告: {pinyin_error_hint()}")

    machine = args.format != "text"
    workspace_mode = not args.files and sys.stdin.isatty()
    ws = Workspace()

    results: list[dict] = []
    errors: list[dict] = []

    if workspace_mode:
        try:
            ws.ensure_dirs()
        except OSError as exc:
            errors.append({"source": None, "message": f"无法创建工作区目录: {exc}"})
            _emit(args, results, errors)
            for error in errors:
                _error(f"paixu: {error['message']}")
            return 1

        inputs = ws.discover_inputs()
        if not inputs:
            message = f"{ws.input_dir} 中没有可排序的文本文件"
            if machine:
                _emit(args, results, [{"source": None, "message": message}])
                return 0
            _info(args.quiet, f"paixu: {message}")
            return 0

        # text 格式：每个输入文件写入 output/ 下的同名文件；
        # 机器格式：合并为单一结果流写标准输出。
        for path in inputs:
            label = path.relative_to(ws.input_dir).as_posix()
            result, error = _process_unit([(str(path), label)], label, args, options)
            if error:
                errors.append(error)
                continue
            if not machine:
                target = str(ws.output_dir / path.name)
                write_error = _write_output(target, _text_body(result), args.encoding)
                if write_error:
                    errors.append(write_error)
                    continue
                result["output"] = target
                _info(args.quiet, f"paixu: 已写入 {target}")
            results.append(result)
    else:
        label = (
            "-"
            if not args.files
            else (args.files[0] if len(args.files) == 1 else None)
        )
        entries = [(path, path) for path in args.files]
        result, error = _process_unit(entries, label, args, options)
        if error:
            errors.append(error)
        elif not machine:
            content = _text_body(result)
            if args.output:
                write_error = _write_output(args.output, content, args.encoding)
                if write_error:
                    errors.append(write_error)
                else:
                    _info(args.quiet, f"paixu: 已写入 {args.output}")
            else:
                sys.stdout.write(content)
        if result is not None:
            results.append(result)

    for error in errors:
        _error(f"paixu: {error['message']}")
    if machine:
        _emit(args, results, errors)
    return 0 if not errors else 1
