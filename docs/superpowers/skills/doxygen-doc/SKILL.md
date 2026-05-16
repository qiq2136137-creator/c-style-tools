---
name: doxygen-doc
description: 为 C/C++ 代码自动生成 Doxygen 风格注释，并导出 API 文档 (HTML/Markdown/JSON)
---

# Doxygen Doc

自动为 C/C++ 代码生成标准 Doxygen 注释并导出 API 文档。

## 用法

用户可以通过以下方式调用：

- `/doxygen-doc` — 处理当前目录所有 C/C++ 文件
- `/doxygen-doc src/` — 处理指定目录
- `/doxygen-doc file.c` — 处理单个文件
- `/doxygen-doc --export html` — 仅导出 HTML 文档
- `/doxygen-doc --export md` — 仅导出 Markdown 文档
- `/doxygen-doc --export json` — 仅导出 JSON 数据
- `/doxygen-doc --export all` — 导出全部格式

## 执行流程

当用户调用此技能时：

1. 解析用户参数（路径、导出格式）
2. 运行 Python 脚本：`python docs/superpowers/skills/doxygen-doc/scripts/doxygen_generator.py <args>`
3. 展示执行结果统计
4. 如有导出，告知用户文档位置

## 前置条件

- Python 3.8+
- 依赖包：`pip install tree-sitter tree-sitter-c Jinja2`

## 注释规则

- 函数：`@brief`、`@param`、`@return`
- 结构体/联合体：`@brief`
- 枚举：`@brief`
- 宏：`@brief`、函数式宏添加 `@param`
- 全局变量：`@brief`
- 文件头：`@file`、`@brief`、`@date`

## 已有注释处理

- 已有 Doxygen 注释 → 保留格式，补充缺失的 @param/@return
- 已有普通注释 → 搬入 @brief，生成标准格式
- 无注释 → @brief 标记 TODO: 描述功能

## 输出

注释直接写入源文件。文档导出到 `docs/api/` 目录：
- `api.json` — 结构化 JSON
- `index.md` — Markdown 文档
- `index.html` — Docusaurus 风格 HTML 文档
