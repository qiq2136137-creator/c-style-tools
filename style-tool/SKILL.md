---
name: style-tool
description: C/C++ 代码格式化 + Doxygen 风格注释生成 (缩进/花括号/空行 + @brief/@param/@return)
---

# Style Tool

自动格式化 C/C++ 代码排版，并生成标准 Doxygen 风格注释。

## 用法

- `/style-tool` — 格式化 + 注释（当前目录所有 C/C++ 文件）
- `/style-tool src/` — 处理指定目录
- `/style-tool file.c` — 处理单个文件
- `/style-tool --mode format` — 仅格式化（缩进、花括号、空行）
- `/style-tool --mode comment` — 仅生成/补全注释
- `/style-tool --indent 2` — 使用 2 空格缩进（默认 4）

## 执行流程

当用户调用此技能时：

1. 解析用户参数（路径、模式、缩进）
2. 运行 Python 脚本：`python style-tool/scripts/style_tool.py <args>`
3. 展示执行结果统计

## 前置条件

- Python 3.8+
- 依赖包：`pip install tree-sitter tree-sitter-c chardet`

## 格式化

- 按大括号层级自动修正缩进
- 花括号统一为 K&R 风格
- 清除行尾空白、规范化空行

## 注释（华为标准）

- 文件头：`@file` `@brief` `@author` `@version` `@date` `@copyright`
- 函数：`@brief` `@param[in]` `@return` `@note` `@see`
- 结构体/枚举/宏/全局变量：`@brief`

## 已有注释处理

- 保留用户填写的 `@brief`、`@param`、`@return` 内容
- 已有标准格式注释 → 不重复处理
- 普通 `//` 注释 → 搬入 `@brief`，生成标准格式
- 无注释 → 生成完整模板（`@brief` 标记 TODO）

## 注意事项

- 会直接修改源文件，建议先提交 git
- `--mode all`（默认）先格式化再注释
- 每次调用都重新检查所有文件
