# Doxygen Doc Skill 设计文档

## 概述

为 C/C++ 代码自动添加 Doxygen 风格注释，并导出 API 文档的 Claude Code 技能。

核心理念：**自动化结构化部分，语义部分留给用户**。工具负责解析代码结构、生成标准格式注释；`@brief` 等语义描述由用户填写，避免 AI 生成不准确的内容。

## 架构

```
dgm_coding/
├── docs/superpowers/skills/
│   └── doxygen-doc/
│       ├── SKILL.md                  # 技能定义
│       └── scripts/
│           ├── doxygen_generator.py  # 主入口
│           ├── parser.py             # tree-sitter 解析
│           ├── commentator.py        # 注释生成
│           ├── writer.py             # 写入源文件
│           └── exporter.py           # 文档导出
├── templates/
│   ├── html/                         # Docusaurus 风格 HTML 模板
│   │   ├── base.html
│   │   ├── style.css
│   │   └── script.js
│   └── markdown/                     # Markdown 模板
│       └── api_template.md
└── docs/api/                         # 导出的文档输出目录
```

## 命令接口

| 命令 | 说明 |
|------|------|
| `/doxygen-doc` | 处理当前目录所有 `.c`/`.h` 文件 |
| `/doxygen-doc src/` | 处理指定目录 |
| `/doxygen-doc file.c` | 处理单个文件 |
| `/doxygen-doc --export html` | 仅导出 HTML 文档 |
| `/doxygen-doc --export md` | 仅导出 Markdown 文档 |
| `/doxygen-doc --export json` | 仅导出 JSON 数据 |
| `/doxygen-doc --export all` | 导出全部格式 |

## 核心模块

### 1. parser.py — 代码解析

使用 tree-sitter 解析 C/C++，提取以下元素：

| 元素 | 提取内容 |
|------|----------|
| 函数定义 | 函数名、返回类型、参数名、参数类型 |
| 结构体/联合体 | 名称、每个字段的名称和类型 |
| 枚举 | 名称、每个枚举值及其值 |
| 宏定义 | 名称、是否函数式宏、参数 |
| 全局变量 | 名称、类型 |
| 文件头 | 文件路径 |

依赖：
- `tree-sitter` (Python 包)
- `tree-sitter-c` (C 语言 grammar)
- `tree-sitter-cpp` (C++ 语言 grammar，可选)

### 2. commentator.py — 注释生成

根据解析结果生成 Doxygen 注释。处理三种情况：

```
已有 Doxygen 注释：
  → 保留格式，补充缺失的 @param / @return

已有普通注释 (// 或 /* */)：
  → 搬入 @brief，生成标准 Doxygen 格式
  → 示例：// 表示ab的和 → @brief 表示ab的和

无注释：
  → @brief 留空占位
  → 生成：@brief TODO: 描述功能
```

生成的注释模板：

**函数：**
```c
/**
 * @brief TODO: 描述功能
 * @param a
 * @param b
 * @return int
 */
int add(int a, int b);
```

**结构体：**
```c
/**
 * @brief TODO: 描述结构体
 */
typedef struct {
    uint8_t brightness; /*!< TODO: 亮度 */
    uint8_t mode;       /*!< TODO: 模式 */
} DGM_Config_t;
```

**枚举：**
```c
/**
 * @brief TODO: 描述枚举
 */
typedef enum {
    MODE_OFF = 0, /*!< TODO: 关闭 */
    MODE_ON  = 1, /*!< TODO: 开启 */
} DGM_Mode_t;
```

**宏：**
```c
/**
 * @brief TODO: 描述宏
 * @param x
 */
#define MAX(a, b) ((a) > (b) ? (a) : (b))
```

**全局变量：**
```c
/**
 * @brief TODO: 描述全局变量
 */
extern uint32_t g_tick_count;
```

**文件头：**
```c
/**
 * @file drv_led.c
 * @brief TODO: 文件描述
 * @author
 * @date 2026-05-16
 */
```

### 3. writer.py — 写入源文件

将生成的注释插入到对应代码元素的上方。处理策略：

- 在函数/结构体/枚举/宏/变量定义的上方插入注释
- 文件头注释插入到文件最顶部（#include 之前）
- 保留原有缩进风格
- 跳过已经在注释保护标记内的代码（如 `/* USER CODE BEGIN */` 区域）

### 4. exporter.py — 文档导出

从代码中的 Doxygen 注释提取信息，生成三种格式的文档。

**JSON 结构：**
```json
{
  "project": "项目名",
  "generated_at": "2026-05-16T12:00:00",
  "files": [
    {
      "path": "src/drv_led.c",
      "brief": "LED 驱动模块",
      "functions": [
        {
          "name": "led_init",
          "brief": "初始化 LED",
          "params": [{"name": "config", "type": "DGM_Config_t*", "brief": "配置参数"}],
          "return_type": "int",
          "return_brief": "0=成功, -1=失败"
        }
      ],
      "structs": [...],
      "enums": [...],
      "macros": [...],
      "globals": [...]
    }
  ]
}
```

**HTML 输出：**
- Docusaurus 风格：左侧导航目录树 + 右侧内容区
- 支持搜索（客户端 JS 搜索）
- 按文件/按类型两种导航模式
- 响应式布局，支持暗色模式
- 纯静态 HTML+CSS+JS，无 Node.js 依赖

**Markdown 输出：**
- 与 HTML 相同的内容结构
- GitHub Flavored Markdown 格式
- 按模块分文件组织
- 适合直接提交到 Git 仓库浏览

## 依赖

- Python 3.8+
- tree-sitter
- tree-sitter-c (tree-sitter-cpp 可选)
- Jinja2 (HTML 模板渲染)

## 使用示例

```bash
# 在 Claude Code 中调用
/doxygen-doc                    # 处理当前项目
/doxygen-doc Core/Bsp/          # 只处理 BSP 目录
/doxygen-doc --export html      # 只导出 HTML 文档

# 也可以直接运行脚本
python scripts/doxygen_generator.py src/ --export all
```

## 工作流

```
1. 用户在 Claude Code 中输入 /doxygen-doc [路径]
2. Skill 解析参数
3. 调用 Python 脚本扫描指定路径的 .c/.h 文件
4. tree-sitter 解析每个文件的 AST
5. 提取函数、结构体、枚举、宏、全局变量
6. 检测已有注释：
   - 有 Doxygen 注释 → 保留，补充缺失字段
   - 有普通注释 → 搬入 @brief，重新格式化
   - 无注释 → 生成模板，@brief 标记 TODO
7. 将注释写入源文件
8. 从所有注释中提取信息
9. 生成文档到 docs/api/
10. 输出统计：处理文件数、生成注释数、导出格式
```
