# paixu

按**拼音**给文本行排序的小工具：自动剥离行首编号与前导标点，输出原文（不带编号）。

> 一句话场景：把「3. 张三」「1、李四」「（2）王五」这种乱序名单，按 zhang / li / wang 排好，
> 且**不破坏原文** —— 排序只看清洗后的键，输出仍是原样那一行。

## 安装

```bash
pip install pypinyin          # 必需（拼音转换）
pip install -e .              # 开发安装；或 pip install . 正常安装
```

需要 Python ≥ 3.9。装好后有 `paixu` 命令；不装也能用 `python -m paixu`。

## 用法

```bash
# 1) 排一个文件，结果打到标准输出
paixu examples/names.txt

# 2) 写到文件 / 机器可读格式
paixu names.txt -o sorted.txt
paixu names.txt --format json
paixu names.txt --format csv | head

# 3) 管道
cat names.txt | paixu

# 4) 交互式工作区（无参数且是终端）：读 ./input/*.txt，逐个写 ./output/同名文件
cd 某个目录 && paixu
```

常用开关：`-r` 逆序 ｜ `--first-letter` 按拼音首字母 ｜ `--no-pinyin` 按原字符 ｜
`--keep-numbers` / `--keep-punctuation` 保留编号与标点 ｜ `--dedupe` 按排序键去重 ｜
`-e/--encoding` 指定编码 ｜ `-q` 只输出结果。

## 输出格式

| `--format` | 说明 |
|---|---|
| `text`（默认） | 每行一条排序后的原文 |
| `json` | `{"ok":true,"items":[{"text","source","source_line","key"}...]}` |
| `ndjson` | 每行一个 JSON 对象，适合流式处理 |
| `csv` | 含表头的 CSV（`text,source,source_line,key`） |

## 退出码

| 码 | 含义 |
|---|---|
| `0` | 成功 |
| `1` | 运行时错误（文件读不了、编码不匹配等；JSON 格式下仍会输出 `ok:false` 信封） |
| `2` | 用法错误（参数非法、`--require-pinyin` 但没装 pypinyin） |

## 已知边界

- **没装 pypinyin 时不报错，而是按 Unicode 码位排序**（中文会变成乱序）。要强制失败用
  `--require-pinyin`。这条是刻意设计：让「只是排英文」的用户不必装中文依赖。
- 排序是**稳定**的：键相同时保持输入顺序。
- 行首编号识别覆盖 `1.` `2、` `(3)` `4：` `[5]` `一、` `（二）` `A)` `b.`；
  分隔符后紧跟数字（如 `1.5 倍`）不算编号。
- **保留编号时前导标点剥不动**：`--keep-numbers` 下 `1. 《张三》` 的排序键仍是
  `1. 《张三》`（`lstrip` 只吃行首，标点在被保留的编号后面）。要两者都剥就别加这个开关。
- `input/`、`output/` 是运行期工作区，已在 `.gitignore` 里 —— 那是用户文本，不是仓库资产。

## 开发

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -e . pytest   # Windows
.venv/bin/python -m pip install -e . pytest                                # POSIX
python -m pytest -q
```

## 许可

MIT-0（MIT No Attribution），全文见 [LICENSE](LICENSE)。可自由使用、修改、再分发，无需署名。
