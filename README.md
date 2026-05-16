# style-tool

C/C++ 代码格式化 + Doxygen 风格注释自动生成工具

[English](#english) | 中文

---

## 功能

- **代码格式化** — 自动修正缩进、K&R 花括号风格、清除行尾空白
- **注释生成** — 为函数/结构体/枚举/宏/全局变量生成华为标准 Doxygen 注释
- **智能保留** — 已填写的 `@brief`、`@param`、`@return` 内容不会被覆盖
- **幂等执行** — 多次运行结果一致，不会重复添加注释

## 快速开始

```bash
# 安装依赖
pip install tree-sitter tree-sitter-c chardet

# 格式化 + 注释（全部处理）
python style-tool/scripts/style_tool.py your_code.c --mode all

# 仅格式化
python style-tool/scripts/style_tool.py src/ --mode format

# 仅注释
python style-tool/scripts/style_tool.py src/ --mode comment

# 使用 2 空格缩进
python style-tool/scripts/style_tool.py src/ --indent 2
```

## 注释规范（华为标准）

生成的注释符合华为 C 语言编程规范：

```c
/**
 * @file drv_key.c
 * @brief 按键驱动模块
 * @author
 * @version 1.0
 * @date 2026-05-17
 * @copyright Copyright (c) 2026
 */

/**
 * @brief 初始化按键 GPIO
 *
 * @param[in] mode  初始化模式
 * @return int  0 表示成功
 *
 * @note 注意事项
 * @see  相关函数
 */
```

## 已有注释处理

| 情况 | 处理方式 |
|------|---------|
| 已有标准格式 | 跳过，不重复处理 |
| 已填写 @brief | 保留内容，补充缺失标签 |
| 普通 `//` 注释 | 搬入 `@brief`，生成标准格式 |
| 无注释 | 生成完整模板（`@brief` 标记 TODO） |

## 在 Claude Code 中使用

将 `style-tool/` 复制到项目中，通过 `/style-tool` 调用。

```bash
bash style-tool/install.sh
```

## 项目结构

```
style-tool/
├── SKILL.md              # Claude Code 技能定义
├── install.sh            # 安装脚本
├── requirements.txt      # Python 依赖
└── scripts/
    ├── style_tool.py     # 主入口（格式化 + 注释）
    ├── parser.py         # tree-sitter C 解析器
    └── models.py         # 数据模型
```

## 依赖

- Python 3.8+
- tree-sitter
- tree-sitter-c
- chardet

---

<a id="english"></a>

# style-tool

C/C++ code formatter + Doxygen comment generator

## Features

- **Code Formatting** — Auto-fix indentation, K&R brace style, trailing whitespace
- **Comment Generation** — Generate Huawei-standard Doxygen comments for functions/structs/enums/macros/globals
- **Smart Preservation** — Existing `@brief`, `@param`, `@return` content is never overwritten
- **Idempotent** — Running multiple times produces the same result

## Quick Start

```bash
pip install tree-sitter tree-sitter-c chardet

# Format + comments
python style-tool/scripts/style_tool.py your_code.c --mode all

# Format only
python style-tool/scripts/style_tool.py src/ --mode format

# Comments only
python style-tool/scripts/style_tool.py src/ --mode comment

# 2-space indentation
python style-tool/scripts/style_tool.py src/ --indent 2
```

## CLI Options

| Option | Description |
|--------|-------------|
| `--mode format` | Format only (indentation, braces, whitespace) |
| `--mode comment` | Comments only (generate/fix Doxygen comments) |
| `--mode all` | Both (default) |
| `--indent N` | Indentation size (default: 4) |
| `--encoding ENC` | Force file encoding |

## License

MIT
