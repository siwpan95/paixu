# 变更记录

> 面向使用 `paixu` 的人：这里只记「你会感知到什么变了」。

## 0.1.0 —— 2026-11-24

首个仓库化版本（此前是 `assets/` 下的草稿态，无 git、无 README、无测试）。

- 命令行：`paixu [FILE...]`，支持文本 / JSON / NDJSON / CSV 四种输出，
  退出码 0 成功 / 1 运行时错误 / 2 用法错误。
- 排序键：剥离行首编号（`1.` `2、` `(3)` `一、` `A)` …）与前导标点，
  按拼音排序；输出**保留原文**。
- 无 `pypinyin` 时透明降级为按 Unicode 码位排序（`--require-pinyin` 可强制失败）。
- 补 33 个 pytest 用例：规范化边界、排序稳定性与去重、CLI 退出码与 stdout/stderr 分流、
  JSON 失败信封。
- 工程外壳：README / LICENSE(MIT-0) / .gitignore / .gitattributes(LF) / CI（3.9 与 3.12）。
