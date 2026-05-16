# Doxygen Doc Skill 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 Claude Code 技能，自动为 C/C++ 代码生成 Doxygen 风格注释，并导出 HTML/Markdown/JSON 格式的 API 文档。

**Architecture:** Python 脚本使用 tree-sitter 解析 C/C++ AST，提取代码结构后生成标准 Doxygen 注释模板（@brief 留给用户填写），再通过 Jinja2 模板导出文档。Claude Code Skill 作为用户入口调用脚本。

**Tech Stack:** Python 3.8+, tree-sitter, tree-sitter-c, Jinja2

---

## 文件结构

```
dgm_coding/
├── docs/superpowers/skills/doxygen-doc/
│   ├── SKILL.md
│   └── scripts/
│       ├── doxygen_generator.py  # 主入口，CLI 解析
│       ├── models.py             # 数据模型 (dataclass)
│       ├── parser.py             # tree-sitter 解析
│       ├── commentator.py        # 注释生成
│       ├── writer.py             # 写入源文件
│       └── exporter.py           # 文档导出 (JSON/MD/HTML)
├── templates/
│   └── html/
│       ├── base.html
│       ├── style.css
│       └── script.js
└── docs/api/                     # 导出输出目录
```

---

### Task 1: 项目骨架与依赖安装

**Files:**
- Create: `docs/superpowers/skills/doxygen-doc/scripts/models.py`
- Create: `docs/superpowers/skills/doxygen-doc/scripts/__init__.py`
- Create: `docs/superpowers/skills/doxygen-doc/requirements.txt`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p docs/superpowers/skills/doxygen-doc/scripts
mkdir -p templates/html
mkdir -p docs/api
```

- [ ] **Step 2: 创建 requirements.txt**

```txt
tree-sitter>=0.20.0
tree-sitter-c>=0.20.0
Jinja2>=3.1.0
```

- [ ] **Step 3: 安装依赖**

```bash
pip install tree-sitter tree-sitter-c Jinja2
```

- [ ] **Step 4: 创建数据模型 models.py**

```python
"""C/C++ 代码元素的数据模型"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Param:
    """函数参数"""
    name: str
    type: str
    brief: str = ""


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    return_type: str
    params: list[Param] = field(default_factory=list)
    brief: str = ""
    return_brief: str = ""
    line_number: int = 0
    has_existing_comment: bool = False
    existing_comment_text: str = ""


@dataclass
class FieldInfo:
    """结构体/联合体字段"""
    name: str
    type: str
    brief: str = ""


@dataclass
class StructInfo:
    """结构体/联合体信息"""
    name: str
    kind: str  # "struct" or "union"
    fields: list[FieldInfo] = field(default_factory=list)
    brief: str = ""
    line_number: int = 0
    has_existing_comment: bool = False
    existing_comment_text: str = ""


@dataclass
class EnumValue:
    """枚举值"""
    name: str
    value: Optional[str]
    brief: str = ""


@dataclass
class EnumInfo:
    """枚举信息"""
    name: str
    values: list[EnumValue] = field(default_factory=list)
    brief: str = ""
    line_number: int = 0
    has_existing_comment: bool = False
    existing_comment_text: str = ""


@dataclass
class MacroInfo:
    """宏定义信息"""
    name: str
    is_function_like: bool
    params: list[str] = field(default_factory=list)
    brief: str = ""
    line_number: int = 0
    has_existing_comment: bool = False
    existing_comment_text: str = ""


@dataclass
class GlobalVarInfo:
    """全局变量信息"""
    name: str
    type: str
    is_extern: bool = False
    brief: str = ""
    line_number: int = 0
    has_existing_comment: bool = False
    existing_comment_text: str = ""


@dataclass
class FileInfo:
    """单个文件的解析结果"""
    path: str
    file_brief: str = ""
    functions: list[FunctionInfo] = field(default_factory=list)
    structs: list[StructInfo] = field(default_factory=list)
    enums: list[EnumInfo] = field(default_factory=list)
    macros: list[MacroInfo] = field(default_factory=list)
    globals: list[GlobalVarInfo] = field(default_factory=list)


@dataclass
class ProjectInfo:
    """整个项目的解析结果"""
    project_name: str
    generated_at: str = ""
    files: list[FileInfo] = field(default_factory=list)

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()
```

- [ ] **Step 5: 创建 __init__.py**

```python
# doxygen-doc scripts package
```

- [ ] **Step 6: 提交**

```bash
git add docs/superpowers/skills/doxygen-doc/ templates/
git commit -m "feat: doxygen-doc 项目骨架与数据模型"
```

---

### Task 2: parser.py — tree-sitter 代码解析

**Files:**
- Create: `docs/superpowers/skills/doxygen-doc/scripts/parser.py`
- Create: `tests/test_parser.py`

- [ ] **Step 1: 创建测试文件 tests/test_parser.py**

```python
"""parser.py 单元测试"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'docs', 'superpowers', 'skills', 'doxygen-doc', 'scripts'))

from parser import CParser


def test_parse_simple_function():
    code = b'int add(int a, int b) {\n    return a + b;\n}\n'
    parser = CParser()
    result = parser.parse(code, "test.c")
    assert len(result.functions) == 1
    fn = result.functions[0]
    assert fn.name == "add"
    assert fn.return_type == "int"
    assert len(fn.params) == 2
    assert fn.params[0].name == "a"
    assert fn.params[0].type == "int"
    assert fn.params[1].name == "b"
    assert fn.params[1].type == "int"


def test_parse_struct():
    code = b'typedef struct {\n    uint8_t brightness;\n    uint8_t mode;\n} Config_t;\n'
    parser = CParser()
    result = parser.parse(code, "test.c")
    assert len(result.structs) == 1
    s = result.structs[0]
    assert s.name == "Config_t"
    assert len(s.fields) == 2
    assert s.fields[0].name == "brightness"
    assert s.fields[0].type == "uint8_t"


def test_parse_enum():
    code = b'typedef enum {\n    MODE_OFF = 0,\n    MODE_ON = 1\n} Mode_t;\n'
    parser = CParser()
    result = parser.parse(code, "test.c")
    assert len(result.enums) == 1
    e = result.enums[0]
    assert e.name == "Mode_t"
    assert len(e.values) == 2
    assert e.values[0].name == "MODE_OFF"
    assert e.values[0].value == "0"


def test_parse_macro():
    code = b'#define MAX(a, b) ((a) > (b) ? (a) : (b))\n#define BUFFER_SIZE 1024\n'
    parser = CParser()
    result = parser.parse(code, "test.c")
    assert len(result.macros) == 2
    m0 = result.macros[0]
    assert m0.name == "MAX"
    assert m0.is_function_like is True
    assert m0.params == ["a", "b"]
    m1 = result.macros[1]
    assert m1.name == "BUFFER_SIZE"
    assert m1.is_function_like is False


def test_parse_global_variable():
    code = b'extern uint32_t g_tick_count;\nstatic int g_config_value = 42;\n'
    parser = CParser()
    result = parser.parse(code, "test.c")
    assert len(result.globals) == 2
    assert result.globals[0].name == "g_tick_count"
    assert result.globals[0].is_extern is True
    assert result.globals[1].name == "g_config_value"


def test_parse_void_function():
    code = b'void led_init(void) {\n    // do nothing\n}\n'
    parser = CParser()
    result = parser.parse(code, "test.c")
    assert len(result.functions) == 1
    fn = result.functions[0]
    assert fn.name == "led_init"
    assert fn.return_type == "void"
    assert len(fn.params) == 0


def test_parse_function_with_pointer_param():
    code = b'int process(Config_t* cfg, uint8_t* buf) { return 0; }\n'
    parser = CParser()
    result = parser.parse(code, "test.c")
    fn = result.functions[0]
    assert fn.params[0].type == "Config_t*"
    assert fn.params[1].type == "uint8_t*"


def test_parse_named_struct():
    code = b'struct Point {\n    int x;\n    int y;\n};\n'
    parser = CParser()
    result = parser.parse(code, "test.c")
    assert len(result.structs) == 1
    assert result.structs[0].name == "Point"
    assert result.structs[0].kind == "struct"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_parser.py -v
```
预期: ModuleNotFoundError 或所有测试 FAIL

- [ ] **Step 3: 实现 parser.py**

```python
"""tree-sitter C/C++ 代码解析器"""
import tree_sitter_c
from tree_sitter import Language, Parser

from models import (
    FileInfo, FunctionInfo, Param, StructInfo, FieldInfo,
    EnumInfo, EnumValue, MacroInfo, GlobalVarInfo
)


def _get_text(node, source_code: bytes) -> str:
    """从 AST 节点提取源码文本"""
    return source_code[node.start_byte:node.end_byte].decode("utf-8", errors="replace").strip()


def _find_child(node, type_name: str):
    """查找指定类型的子节点"""
    for child in node.children:
        if child.type == type_name:
            return child
    return None


def _find_all_children(node, type_name: str):
    """查找所有指定类型的子节点"""
    return [c for c in node.children if c.type == type_name]


class CParser:
    """C 语言代码解析器"""

    def __init__(self):
        self.language = Language(tree_sitter_c.language())
        self.parser = Parser(self.language)

    def parse(self, source_code: bytes, file_path: str = "") -> FileInfo:
        """解析 C 源码，提取所有代码元素"""
        tree = self.parser.parse(source_code)
        root = tree.root_node

        file_info = FileInfo(path=file_path)

        for child in root.children:
            if child.type == "function_definition":
                fn = self._parse_function(child, source_code)
                if fn:
                    file_info.functions.append(fn)

            elif child.type in ("struct_specifier", "union_specifier"):
                s = self._parse_struct(child, source_code)
                if s:
                    file_info.structs.append(s)

            elif child.type == "type_definition":
                result = self._parse_typedef(child, source_code)
                if result:
                    if isinstance(result, StructInfo):
                        file_info.structs.append(result)
                    elif isinstance(result, EnumInfo):
                        file_info.enums.append(result)

            elif child.type == "enum_specifier":
                e = self._parse_enum(child, source_code)
                if e:
                    file_info.enums.append(e)

            elif child.type == "preproc_def":
                m = self._parse_preproc_def(child, source_code)
                if m:
                    file_info.macros.append(m)

            elif child.type == "declaration":
                g = self._parse_global_var(child, source_code)
                if g:
                    file_info.globals.append(g)

        return file_info

    def _parse_function(self, node, src: bytes) -> FunctionInfo | None:
        """解析函数定义"""
        # 提取返回类型和声明器
        type_node = _find_child(node, "type")
        declarator = _find_child(node, "declarator")
        if not declarator:
            return None

        # 处理指针声明器: int *foo(...)
        while declarator.type in ("pointer_declarator", "parenthesized_declarator"):
            inner = _find_child(declarator, "pointer_declarator") or \
                    _find_child(declarator, "parenthesized_declarator") or \
                    _find_child(declarator, "function_declarator") or \
                    _find_child(declarator, "identifier") or \
                    _find_child(declarator, "field_identifier")
            if inner and inner.type in ("pointer_declarator", "parenthesized_declarator"):
                declarator = inner
            else:
                break

        if declarator.type != "function_declarator":
            return None

        # 函数名
        name_node = _find_child(declarator, "identifier") or _find_child(declarator, "field_identifier")
        if not name_node:
            return None
        fn_name = _get_text(name_node, src)

        # 返回类型
        return_type = ""
        if type_node:
            return_type = _get_text(type_node, src)

        # 参数列表
        params_node = _find_child(declarator, "parameter_list")
        params = []
        if params_node:
            for param_decl in _find_all_children(params_node, "parameter_declaration"):
                p_type_node = _find_child(param_decl, "type")
                p_name_node = _find_child(param_decl, "declarator") or _find_child(param_decl, "abstract_declarator")

                p_type = _get_text(p_type_node, src) if p_type_node else ""
                p_name = ""

                if p_name_node:
                    # 处理指针参数: int *buf
                    if p_name_node.type == "pointer_declarator":
                        p_type += " *"
                        inner = _find_child(p_name_node, "identifier") or _find_child(p_name_node, "declarator")
                        if inner:
                            if inner.type == "identifier":
                                p_name = _get_text(inner, src)
                            elif inner.type == "declarator":
                                p_name = _get_text(inner, src)
                    elif p_name_node.type == "identifier":
                        p_name = _get_text(p_name_node, src)
                    else:
                        p_name = _get_text(p_name_node, src)

                # 过滤 void 参数
                if p_type == "void" and not p_name:
                    continue

                params.append(Param(name=p_name, type=p_type))

        return FunctionInfo(
            name=fn_name,
            return_type=return_type,
            params=params,
            line_number=node.start_point[0] + 1
        )

    def _parse_struct(self, node, src: bytes) -> StructInfo | None:
        """解析结构体/联合体"""
        kind = "struct" if node.type == "struct_specifier" else "union"

        # 查找类型名
        name = ""
        name_node = _find_child(node, "type_identifier")
        if name_node:
            name = _get_text(name_node, src)

        # 查找字段
        body = _find_child(node, "field_declaration_list")
        fields = []
        if body:
            for field_decl in _find_all_children(body, "field_declaration"):
                f_type_node = _find_child(field_decl, "type")
                f_name_node = _find_child(field_decl, "declarator") or _find_child(field_decl, "field_identifier")

                f_type = _get_text(f_type_node, src) if f_type_node else ""
                f_name = _get_text(f_name_node, src) if f_name_node else ""

                if f_name:
                    fields.append(FieldInfo(name=f_name, type=f_type))

        if not name and not fields:
            return None

        return StructInfo(
            name=name,
            kind=kind,
            fields=fields,
            line_number=node.start_point[0] + 1
        )

    def _parse_typedef(self, node, src: bytes) -> StructInfo | EnumInfo | None:
        """解析 typedef，可能包含结构体或枚举"""
        # 查找 struct/union/enum
        struct_node = _find_child(node, "struct_specifier") or _find_child(node, "union_specifier")
        enum_node = _find_child(node, "enum_specifier")

        # typedef 名
        type_def_name = ""
        declarator = _find_child(node, "declarator") or _find_child(node, "type_identifier")
        if declarator:
            type_def_name = _get_text(declarator, src)

        if struct_node:
            s = self._parse_struct(struct_node, src)
            if s and type_def_name:
                s.name = type_def_name
            return s

        if enum_node:
            e = self._parse_enum(enum_node, src)
            if e and type_def_name:
                e.name = type_def_name
            return e

        return None

    def _parse_enum(self, node, src: bytes) -> EnumInfo | None:
        """解析枚举"""
        name = ""
        name_node = _find_child(node, "type_identifier")
        if name_node:
            name = _get_text(name_node, src)

        body = _find_child(node, "enumerator_list")
        values = []
        if body:
            for enum_val in _find_all_children(body, "enumerator"):
                val_name_node = _find_child(enum_val, "name") or _find_child(enum_val, "identifier")
                val_value_node = _find_child(enum_val, "number_literal") or \
                                _find_child(enum_val, "unary_expression") or \
                                _find_child(enum_val, "identifier")

                val_name = _get_text(val_name_node, src) if val_name_node else ""
                val_value = _get_text(val_value_node, src) if val_value_node else None

                if val_name:
                    values.append(EnumValue(name=val_name, value=val_value))

        return EnumInfo(
            name=name,
            values=values,
            line_number=node.start_point[0] + 1
        )

    def _parse_preproc_def(self, node, src: bytes) -> MacroInfo | None:
        """解析 #define 宏"""
        # 查找宏名
        name_node = _find_child(node, "identifier")
        if not name_node:
            return None
        name = _get_text(name_node, src)

        # 检查是否是函数式宏
        is_function_like = False
        params = []
        for child in node.children:
            if child.type == "preproc_params":
                is_function_like = True
                for param in _find_all_children(child, "identifier"):
                    params.append(_get_text(param, src))
                break

        return MacroInfo(
            name=name,
            is_function_like=is_function_like,
            params=params,
            line_number=node.start_point[0] + 1
        )

    def _parse_global_var(self, node, src: bytes) -> GlobalVarInfo | None:
        """解析全局变量声明"""
        type_node = _find_child(node, "type")
        declarator = _find_child(node, "declarator")
        if not declarator or not type_node:
            return None

        # 跳过函数声明（不是变量）
        if declarator.type == "function_declarator":
            return None

        # 检查是否 extern
        is_extern = False
        for child in node.children:
            if child.type == "storage_class_specifier" and _get_text(child, src) == "extern":
                is_extern = True
                break

        var_name = ""
        var_type = _get_text(type_node, src)

        if declarator.type == "init_declarator":
            name_node = _find_child(declarator, "identifier") or _find_child(declarator, "declarator")
            if name_node:
                if name_node.type == "pointer_declarator":
                    var_type += " *"
                    inner = _find_child(name_node, "identifier")
                    if inner:
                        var_name = _get_text(inner, src)
                else:
                    var_name = _get_text(name_node, src)
        elif declarator.type == "identifier":
            var_name = _get_text(declarator, src)
        elif declarator.type == "pointer_declarator":
            var_type += " *"
            inner = _find_child(declarator, "identifier")
            if inner:
                var_name = _get_text(inner, src)

        if not var_name:
            return None

        return GlobalVarInfo(
            name=var_name,
            type=var_type,
            is_extern=is_extern,
            line_number=node.start_point[0] + 1
        )

    def parse_file(self, file_path: str) -> FileInfo:
        """解析文件"""
        with open(file_path, "rb") as f:
            source_code = f.read()
        return self.parse(source_code, file_path)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_parser.py -v
```
预期: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add docs/superpowers/skills/doxygen-doc/scripts/parser.py tests/test_parser.py
git commit -m "feat: tree-sitter C 语言解析器"
```

---

### Task 3: commentator.py — 注释生成

**Files:**
- Create: `docs/superpowers/skills/doxygen-doc/scripts/commentator.py`
- Create: `tests/test_commentator.py`

- [ ] **Step 1: 创建测试 tests/test_commentator.py**

```python
"""commentator.py 单元测试"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'docs', 'superpowers', 'skills', 'doxygen-doc', 'scripts'))

from commentator import DoxygenCommentator
from models import (
    FunctionInfo, Param, StructInfo, FieldInfo,
    EnumInfo, EnumValue, MacroInfo, GlobalVarInfo
)


def test_function_no_existing_comment():
    fn = FunctionInfo(name="add", return_type="int", params=[
        Param(name="a", type="int"), Param(name="b", type="int")
    ])
    comment = DoxygenCommentator.generate_function_comment(fn)
    assert "@brief TODO:" in comment
    assert "@param a" in comment
    assert "@param b" in comment
    assert "@return int" in comment


def test_function_with_existing_comment():
    fn = FunctionInfo(
        name="add", return_type="int",
        params=[Param(name="a", type="int"), Param(name="b", type="int")],
        has_existing_comment=True,
        existing_comment_text="表示ab的和"
    )
    comment = DoxygenCommentator.generate_function_comment(fn)
    assert "@brief 表示ab的和" in comment
    assert "@param a" in comment
    assert "@return int" in comment


def test_void_function_no_return():
    fn = FunctionInfo(name="led_init", return_type="void", params=[])
    comment = DoxygenCommentator.generate_function_comment(fn)
    assert "@return" not in comment


def test_struct_comment():
    s = StructInfo(name="Config_t", kind="struct", fields=[
        FieldInfo(name="brightness", type="uint8_t"),
        FieldInfo(name="mode", type="uint8_t")
    ])
    comment = DoxygenCommentator.generate_struct_comment(s)
    assert "@brief TODO:" in comment
    assert 'brightness; /*!< TODO: 亮度 */' in comment


def test_struct_with_existing_comment():
    s = StructInfo(
        name="Config_t", kind="struct",
        fields=[FieldInfo(name="brightness", type="uint8_t")],
        has_existing_comment=True,
        existing_comment_text="显示配置"
    )
    comment = DoxygenCommentator.generate_struct_comment(s)
    assert "@brief 显示配置" in comment


def test_enum_comment():
    e = EnumInfo(name="Mode_t", values=[
        EnumValue(name="MODE_OFF", value="0"),
        EnumValue(name="MODE_ON", value="1")
    ])
    comment = DoxygenCommentator.generate_enum_comment(e)
    assert "@brief TODO:" in comment
    assert "MODE_OFF = 0" in comment
    assert "MODE_ON = 1" in comment


def test_macro_function_like():
    m = MacroInfo(name="MAX", is_function_like=True, params=["a", "b"])
    comment = DoxygenCommentator.generate_macro_comment(m)
    assert "@brief TODO:" in comment
    assert "@param a" in comment
    assert "@param b" in comment


def test_macro_object_like():
    m = MacroInfo(name="BUFFER_SIZE", is_function_like=False)
    comment = DoxygenCommentator.generate_macro_comment(m)
    assert "@brief TODO:" in comment
    assert "@param" not in comment


def test_global_var_comment():
    g = GlobalVarInfo(name="g_tick", type="uint32_t")
    comment = DoxygenCommentator.generate_global_comment(g)
    assert "@brief TODO:" in comment


def test_file_comment():
    comment = DoxygenCommentator.generate_file_comment("src/drv_led.c")
    assert "@file drv_led.c" in comment
    assert "@date" in comment
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_commentator.py -v
```
预期: ModuleNotFoundError 或全部 FAIL

- [ ] **Step 3: 实现 commentator.py**

```python
"""Doxygen 注释生成器"""
from datetime import date

from models import (
    FileInfo, FunctionInfo, StructInfo, EnumInfo,
    MacroInfo, GlobalVarInfo
)


class DoxygenCommentator:
    """根据解析结果生成 Doxygen 注释"""

    @staticmethod
    def generate_function_comment(fn: FunctionInfo) -> str:
        """生成函数注释"""
        lines = ["/**"]

        if fn.has_existing_comment and fn.existing_comment_text:
            lines.append(f" * @brief {fn.existing_comment_text}")
        else:
            lines.append(" * @brief TODO: 描述功能")

        for p in fn.params:
            lines.append(f" * @param {p.name}")

        if fn.return_type and fn.return_type != "void":
            lines.append(f" * @return {fn.return_type}")

        lines.append(" */")
        return "\n".join(lines)

    @staticmethod
    def generate_struct_comment(s: StructInfo) -> str:
        """生成结构体/联合体注释"""
        lines = ["/**"]

        if s.has_existing_comment and s.existing_comment_text:
            lines.append(f" * @brief {s.existing_comment_text}")
        else:
            kind_name = "结构体" if s.kind == "struct" else "联合体"
            lines.append(f" * @brief TODO: 描述{kind_name}")

        lines.append(" */")
        return "\n".join(lines)

    @staticmethod
    def generate_enum_comment(e: EnumInfo) -> str:
        """生成枚举注释"""
        lines = ["/**"]

        if e.has_existing_comment and e.existing_comment_text:
            lines.append(f" * @brief {e.existing_comment_text}")
        else:
            lines.append(" * @brief TODO: 描述枚举")

        lines.append(" */")
        return "\n".join(lines)

    @staticmethod
    def generate_macro_comment(m: MacroInfo) -> str:
        """生成宏定义注释"""
        lines = ["/**"]

        if m.has_existing_comment and m.existing_comment_text:
            lines.append(f" * @brief {m.existing_comment_text}")
        else:
            lines.append(" * @brief TODO: 描述宏")

        for p in m.params:
            lines.append(f" * @param {p}")

        lines.append(" */")
        return "\n".join(lines)

    @staticmethod
    def generate_global_comment(g: GlobalVarInfo) -> str:
        """生成全局变量注释"""
        lines = ["/**"]

        if g.has_existing_comment and g.existing_comment_text:
            lines.append(f" * @brief {g.existing_comment_text}")
        else:
            lines.append(" * @brief TODO: 描述全局变量")

        lines.append(" */")
        return "\n".join(lines)

    @staticmethod
    def generate_file_comment(file_path: str) -> str:
        """生成文件头注释"""
        import os
        filename = os.path.basename(file_path)
        today = date.today().isoformat()

        lines = [
            "/**",
            f" * @file {filename}",
            " * @brief TODO: 文件描述",
            " * @author",
            f" * @date {today}",
            " */"
        ]
        return "\n".join(lines)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_commentator.py -v
```
预期: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add docs/superpowers/skills/doxygen-doc/scripts/commentator.py tests/test_commentator.py
git commit -m "feat: Doxygen 注释生成器"
```

---

### Task 4: writer.py — 注释写入源文件

**Files:**
- Create: `docs/superpowers/skills/doxygen-doc/scripts/writer.py`
- Create: `tests/test_writer.py`

- [ ] **Step 1: 创建测试 tests/test_writer.py**

```python
"""writer.py 单元测试"""
import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'docs', 'superpowers', 'skills', 'doxygen-doc', 'scripts'))

from writer import CommentWriter
from parser import CParser
from commentator import DoxygenCommentator
from models import FunctionInfo, Param, FileInfo


def test_insert_function_comment():
    source = b'int add(int a, int b) {\n    return a + b;\n}\n'
    parser = CParser()
    file_info = parser.parse(source, "test.c")

    writer = CommentWriter()
    fn_comment = DoxygenCommentator.generate_function_comment(file_info.functions[0])
    result = writer.insert_comments(source.decode(), file_info, file_comments={"functions": {0: fn_comment}})

    assert "/**" in result
    assert "@brief TODO:" in result
    assert "@param a" in result
    assert "int add(int a, int b)" in result


def test_insert_file_header():
    source = b'#include <stdio.h>\n\nint main() { return 0; }\n'
    parser = CParser()
    file_info = parser.parse(source, "test.c")

    writer = CommentWriter()
    file_comment = DoxygenCommentator.generate_file_comment("test.c")
    result = writer.insert_file_header(source.decode(), file_comment)

    assert "@file test.c" in result
    assert result.index("@file") < result.index("#include")


def test_preserve_existing_doxygen():
    source = b'/**\n * @brief 已有注释\n * @param x\n */\nvoid foo(int x) {}\n'
    parser = CParser()
    file_info = parser.parse(source, "test.c")

    writer = CommentWriter()
    result = writer.insert_comments(source.decode(), file_info)

    assert "已有注释" in result
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_writer.py -v
```
预期: ModuleNotFoundError 或全部 FAIL

- [ ] **Step 3: 实现 writer.py**

```python
"""注释写入器 — 将生成的注释插入源文件"""
import re

from models import FileInfo


class CommentWriter:
    """将 Doxygen 注释写入源文件"""

    # 匹配已有的 Doxygen 注释 (/** ... */)
    DOXYGEN_COMMENT_RE = re.compile(
        r'/\*\*.*?\*/\s*', re.DOTALL
    )

    # 匹配已有的普通注释 (// 或 /* ... */)
    SINGLE_COMMENT_RE = re.compile(r'//\s*(.*)$')
    BLOCK_COMMENT_RE = re.compile(r'/\*\s*(.*?)\s*\*/', re.DOTALL)

    def insert_comments(
        self,
        source: str,
        file_info: FileInfo,
        file_comments: dict | None = None
    ) -> str:
        """将注释插入到对应代码元素上方

        Args:
            source: 源文件内容
            file_info: 解析结果
            file_comments: dict, key 为元素类型，value 为 {index: comment_text}
        """
        if file_comments is None:
            return source

        lines = source.split('\n')
        insertions = []  # (line_index, comment_text)

        # 处理函数
        for i, fn in enumerate(file_info.functions):
            if "functions" in file_comments and i in file_comments["functions"]:
                comment = file_comments["functions"][i]
                line_idx = fn.line_number - 1
                if line_idx < len(lines):
                    insertions.append((line_idx, comment))

        # 处理结构体
        for i, s in enumerate(file_info.structs):
            if "structs" in file_comments and i in file_comments["structs"]:
                comment = file_comments["structs"][i]
                line_idx = s.line_number - 1
                if line_idx < len(lines):
                    insertions.append((line_idx, comment))

        # 处理枚举
        for i, e in enumerate(file_info.enums):
            if "enums" in file_comments and i in file_comments["enums"]:
                comment = file_comments["enums"][i]
                line_idx = e.line_number - 1
                if line_idx < len(lines):
                    insertions.append((line_idx, comment))

        # 处理宏
        for i, m in enumerate(file_info.macros):
            if "macros" in file_comments and i in file_comments["macros"]:
                comment = file_comments["macros"][i]
                line_idx = m.line_number - 1
                if line_idx < len(lines):
                    insertions.append((line_idx, comment))

        # 处理全局变量
        for i, g in enumerate(file_info.globals):
            if "globals" in file_comments and i in file_comments["globals"]:
                comment = file_comments["globals"][i]
                line_idx = g.line_number - 1
                if line_idx < len(lines):
                    insertions.append((line_idx, comment))

        # 从后往前插入，避免行号偏移
        insertions.sort(key=lambda x: x[0], reverse=True)

        for line_idx, comment in insertions:
            # 获取缩进
            indent = ""
            if line_idx < len(lines):
                match = re.match(r'^(\s*)', lines[line_idx])
                if match:
                    indent = match.group(1)

            # 检查该行上方是否已有 Doxygen 注释
            has_existing = self._has_comment_above(lines, line_idx)

            if not has_existing:
                comment_lines = comment.split('\n')
                indented_comment = "\n".join(
                    indent + cl if cl.strip() else cl
                    for cl in comment_lines
                )
                lines.insert(line_idx, indented_comment)

        return '\n'.join(lines)

    def insert_file_header(self, source: str, file_comment: str) -> str:
        """在文件顶部插入文件头注释"""
        # 如果文件已有文件头注释，跳过
        if source.lstrip().startswith('/**') and '@file' in source[:200]:
            return source

        return file_comment + "\n" + source

    def _has_comment_above(self, lines: list[str], line_idx: int) -> bool:
        """检查指定行上方是否已有 Doxygen 注释"""
        if line_idx == 0:
            return False

        # 向上查找非空行
        check_idx = line_idx - 1
        while check_idx >= 0 and not lines[check_idx].strip():
            check_idx -= 1

        if check_idx < 0:
            return False

        # 检查是否是 Doxygen 注释结束符 "*/"
        if lines[check_idx].strip().endswith("*/"):
            return True

        return False
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_writer.py -v
```
预期: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add docs/superpowers/skills/doxygen-doc/scripts/writer.py tests/test_writer.py
git commit -m "feat: 注释写入器"
```

---

### Task 5: exporter.py — JSON 导出

**Files:**
- Create: `docs/superpowers/skills/doxygen-doc/scripts/exporter.py` (仅 JSON 部分)
- Create: `tests/test_exporter.py`

- [ ] **Step 1: 创建测试 tests/test_exporter_json.py**

```python
"""exporter.py JSON 导出测试"""
import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'docs', 'superpowers', 'skills', 'doxygen-doc', 'scripts'))

from exporter import DocExporter
from models import (
    ProjectInfo, FileInfo, FunctionInfo, Param,
    StructInfo, FieldInfo, EnumInfo, EnumValue
)


def _make_sample_project():
    return ProjectInfo(
        project_name="test_project",
        files=[
            FileInfo(
                path="src/test.c",
                file_brief="测试文件",
                functions=[
                    FunctionInfo(
                        name="add", return_type="int",
                        params=[Param(name="a", type="int"), Param(name="b", type="int")],
                        brief="两数之和"
                    )
                ],
                structs=[
                    StructInfo(
                        name="Config_t", kind="struct",
                        fields=[FieldInfo(name="val", type="int")],
                        brief="配置"
                    )
                ],
                enums=[
                    EnumInfo(
                        name="Mode_t",
                        values=[EnumValue(name="OFF", value="0")],
                        brief="模式"
                    )
                ]
            )
        ]
    )


def test_export_json(tmp_path):
    project = _make_sample_project()
    exporter = DocExporter()
    output = tmp_path / "api.json"
    exporter.export_json(project, str(output))

    with open(output) as f:
        data = json.load(f)

    assert data["project"] == "test_project"
    assert len(data["files"]) == 1
    assert data["files"][0]["functions"][0]["name"] == "add"
    assert data["files"][0]["functions"][0]["brief"] == "两数之和"
    assert data["files"][0]["structs"][0]["name"] == "Config_t"
    assert data["files"][0]["enums"][0]["name"] == "Mode_t"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_exporter_json.py -v
```
预期: ModuleNotFoundError 或 FAIL

- [ ] **Step 3: 实现 exporter.py JSON 部分**

```python
"""API 文档导出器"""
import json
import os
from datetime import datetime

from models import ProjectInfo, FileInfo


class DocExporter:
    """将解析结果导出为多种格式"""

    def export_json(self, project: ProjectInfo, output_path: str):
        """导出为 JSON 格式"""
        data = {
            "project": project.project_name,
            "generated_at": project.generated_at,
            "files": []
        }

        for fi in project.files:
            file_data = {
                "path": fi.path,
                "brief": fi.file_brief,
                "functions": [
                    {
                        "name": fn.name,
                        "brief": fn.brief,
                        "return_type": fn.return_type,
                        "return_brief": fn.return_brief,
                        "params": [
                            {"name": p.name, "type": p.type, "brief": p.brief}
                            for p in fn.params
                        ]
                    }
                    for fn in fi.functions
                ],
                "structs": [
                    {
                        "name": s.name,
                        "kind": s.kind,
                        "brief": s.brief,
                        "fields": [
                            {"name": f.name, "type": f.type, "brief": f.brief}
                            for f in s.fields
                        ]
                    }
                    for s in fi.structs
                ],
                "enums": [
                    {
                        "name": e.name,
                        "brief": e.brief,
                        "values": [
                            {"name": v.name, "value": v.value, "brief": v.brief}
                            for v in e.values
                        ]
                    }
                    for e in fi.enums
                ],
                "macros": [
                    {
                        "name": m.name,
                        "brief": m.brief,
                        "is_function_like": m.is_function_like,
                        "params": m.params
                    }
                    for m in fi.macros
                ],
                "globals": [
                    {
                        "name": g.name,
                        "type": g.type,
                        "brief": g.brief,
                        "is_extern": g.is_extern
                    }
                    for g in fi.globals
                ]
            }
            data["files"].append(file_data)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_exporter_json.py -v
```
预期: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add docs/superpowers/skills/doxygen-doc/scripts/exporter.py tests/test_exporter_json.py
git commit -m "feat: JSON 文档导出"
```

---

### Task 6: exporter.py — Markdown 导出

**Files:**
- Modify: `docs/superpowers/skills/doxygen-doc/scripts/exporter.py`
- Create: `tests/test_exporter_md.py`

- [ ] **Step 1: 创建测试 tests/test_exporter_md.py**

```python
"""exporter.py Markdown 导出测试"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'docs', 'superpowers', 'skills', 'doxygen-doc', 'scripts'))

from exporter import DocExporter
from models import (
    ProjectInfo, FileInfo, FunctionInfo, Param,
    StructInfo, FieldInfo, EnumInfo, EnumValue,
    MacroInfo, GlobalVarInfo
)


def _make_sample_project():
    return ProjectInfo(
        project_name="test_project",
        files=[
            FileInfo(
                path="src/test.c",
                file_brief="测试模块",
                functions=[
                    FunctionInfo(
                        name="add", return_type="int",
                        params=[Param(name="a", type="int", brief="加数"), Param(name="b", type="int", brief="被加数")],
                        brief="计算两数之和"
                    )
                ],
                structs=[
                    StructInfo(
                        name="Config_t", kind="struct",
                        fields=[FieldInfo(name="val", type="int", brief="数值")],
                        brief="配置结构体"
                    )
                ],
                enums=[
                    EnumInfo(
                        name="Mode_t",
                        values=[EnumValue(name="OFF", value="0", brief="关闭"), EnumValue(name="ON", value="1", brief="开启")],
                        brief="工作模式"
                    )
                ],
                macros=[
                    MacroInfo(name="BUFFER_SIZE", is_function_like=False, brief="缓冲区大小")
                ],
                globals=[
                    GlobalVarInfo(name="g_tick", type="uint32_t", brief="系统滴答计数")
                ]
            )
        ]
    )


def test_export_markdown(tmp_path):
    project = _make_sample_project()
    exporter = DocExporter()
    output_dir = str(tmp_path / "api")
    exporter.export_markdown(project, output_dir)

    index_path = os.path.join(output_dir, "index.md")
    assert os.path.exists(index_path)

    with open(index_path, encoding="utf-8") as f:
        content = f.read()

    assert "# API 文档" in content
    assert "test.c" in content


def test_markdown_has_function_details(tmp_path):
    project = _make_sample_project()
    exporter = DocExporter()
    output_dir = str(tmp_path / "api")
    exporter.export_markdown(project, output_dir)

    index_path = os.path.join(output_dir, "index.md")
    with open(index_path, encoding="utf-8") as f:
        content = f.read()

    assert "### add" in content
    assert "计算两数之和" in content
    assert "| a | int | 加数 |" in content
    assert "| b | int | 被加数 |" in content


def test_markdown_has_struct_details(tmp_path):
    project = _make_sample_project()
    exporter = DocExporter()
    output_dir = str(tmp_path / "api")
    exporter.export_markdown(project, output_dir)

    index_path = os.path.join(output_dir, "index.md")
    with open(index_path, encoding="utf-8") as f:
        content = f.read()

    assert "### Config_t" in content
    assert "配置结构体" in content
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_exporter_md.py -v
```
预期: FAIL

- [ ] **Step 3: 在 exporter.py 中添加 Markdown 导出方法**

```python
# 添加到 DocExporter 类中

def export_markdown(self, project: ProjectInfo, output_dir: str):
    """导出为 Markdown 格式"""
    os.makedirs(output_dir, exist_ok=True)

    # 生成索引页
    lines = ["# API 文档\n"]
    lines.append(f"项目: **{project.project_name}**\n")
    lines.append(f"生成时间: {project.generated_at}\n")

    # 按文件组织
    for fi in project.files:
        lines.append(f"\n---\n\n## 📄 {os.path.basename(fi.path)}\n")
        if fi.file_brief:
            lines.append(f"> {fi.file_brief}\n")

        # 函数
        if fi.functions:
            lines.append("\n### 函数\n")
            for fn in fi.functions:
                lines.append(f"\n#### {fn.name}\n")
                if fn.brief:
                    lines.append(f"\n> {fn.brief}\n")

                if fn.params:
                    lines.append("\n| 参数 | 类型 | 说明 |")
                    lines.append("|------|------|------|")
                    for p in fn.params:
                        brief = p.brief if p.brief else ""
                        lines.append(f"| {p.name} | `{p.type}` | {brief} |")

                if fn.return_type and fn.return_type != "void":
                    ret_brief = f" — {fn.return_brief}" if fn.return_brief else ""
                    lines.append(f"\n**返回值:** `{fn.return_type}`{ret_brief}\n")

        # 结构体
        if fi.structs:
            lines.append("\n### 结构体\n")
            for s in fi.structs:
                kind_label = "结构体" if s.kind == "struct" else "联合体"
                lines.append(f"\n#### {s.name}\n")
                if s.brief:
                    lines.append(f"\n> {s.brief}\n")

                if s.fields:
                    lines.append(f"\n| 字段 | 类型 | 说明 |")
                    lines.append("|------|------|------|")
                    for f in s.fields:
                        brief = f.brief if f.brief else ""
                        lines.append(f"| {f.name} | `{f.type}` | {brief} |")

        # 枚举
        if fi.enums:
            lines.append("\n### 枚举\n")
            for e in fi.enums:
                lines.append(f"\n#### {e.name}\n")
                if e.brief:
                    lines.append(f"\n> {e.brief}\n")

                if e.values:
                    lines.append("\n| 值 | 数值 | 说明 |")
                    lines.append("|------|------|------|")
                    for v in e.values:
                        val = v.value if v.value else ""
                        brief = v.brief if v.brief else ""
                        lines.append(f"| {v.name} | {val} | {brief} |")

        # 宏
        if fi.macros:
            lines.append("\n### 宏定义\n")
            for m in fi.macros:
                lines.append(f"\n#### {m.name}\n")
                if m.brief:
                    lines.append(f"\n> {m.brief}\n")
                if m.is_function_like:
                    lines.append(f"\n函数式宏，参数: {', '.join(m.params)}\n")

        # 全局变量
        if fi.globals:
            lines.append("\n### 全局变量\n")
            lines.append("\n| 变量名 | 类型 | 说明 |")
            lines.append("|--------|------|------|")
            for g in fi.globals:
                brief = g.brief if g.brief else ""
                lines.append(f"| {g.name} | `{g.type}` | {brief} |")

    content = "\n".join(lines)
    with open(os.path.join(output_dir, "index.md"), "w", encoding="utf-8") as f:
        f.write(content)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_exporter_md.py -v
```
预期: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add docs/superpowers/skills/doxygen-doc/scripts/exporter.py tests/test_exporter_md.py
git commit -m "feat: Markdown 文档导出"
```

---

### Task 7: HTML 导出 — Docusaurus 风格模板

**Files:**
- Create: `templates/html/base.html`
- Create: `templates/html/style.css`
- Create: `templates/html/script.js`
- Modify: `docs/superpowers/skills/doxygen-doc/scripts/exporter.py`
- Create: `tests/test_exporter_html.py`

- [ ] **Step 1: 创建 Docusaurus 风格 CSS templates/html/style.css**

```css
:root {
    --bg: #ffffff;
    --bg-secondary: #f6f6f6;
    --text: #1c1e21;
    --text-secondary: #606770;
    --primary: #2e8555;
    --primary-dark: #1a5c3a;
    --border: #e1e4e8;
    --sidebar-bg: #f9fafb;
    --code-bg: #f4f5f7;
    --card-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

[data-theme="dark"] {
    --bg: #1b1b1d;
    --bg-secondary: #242526;
    --text: #e3e3e3;
    --text-secondary: #b0b0b0;
    --primary: #2e8555;
    --primary-dark: #4aba7a;
    --border: #444950;
    --sidebar-bg: #242526;
    --code-bg: #2d2d2d;
    --card-shadow: 0 1px 3px rgba(0,0,0,0.3);
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
}

.layout {
    display: flex;
    min-height: 100vh;
}

.sidebar {
    width: 280px;
    background: var(--sidebar-bg);
    border-right: 1px solid var(--border);
    padding: 20px 0;
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    overflow-y: auto;
}

.sidebar h2 {
    padding: 0 20px 15px;
    font-size: 1.1em;
    color: var(--primary);
    border-bottom: 1px solid var(--border);
}

.sidebar .nav-group {
    padding: 10px 0;
}

.sidebar .nav-group-title {
    padding: 8px 20px;
    font-size: 0.75em;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-secondary);
    font-weight: 600;
}

.sidebar .nav-item {
    display: block;
    padding: 6px 20px 6px 30px;
    color: var(--text);
    text-decoration: none;
    font-size: 0.9em;
    border-left: 3px solid transparent;
    transition: all 0.15s;
}

.sidebar .nav-item:hover {
    background: var(--bg-secondary);
    border-left-color: var(--primary);
    color: var(--primary);
}

.sidebar .nav-item.active {
    border-left-color: var(--primary);
    color: var(--primary);
    font-weight: 500;
}

.main {
    margin-left: 280px;
    flex: 1;
    padding: 30px 50px;
    max-width: 900px;
}

.topbar {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    padding: 10px 20px;
    gap: 12px;
    position: fixed;
    top: 0;
    right: 0;
    left: 280px;
    background: var(--bg);
    border-bottom: 1px solid var(--border);
    z-index: 10;
}

.search-box {
    padding: 8px 14px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg-secondary);
    color: var(--text);
    font-size: 0.9em;
    width: 250px;
    outline: none;
    transition: border-color 0.2s;
}

.search-box:focus {
    border-color: var(--primary);
}

.theme-toggle {
    background: none;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 12px;
    cursor: pointer;
    font-size: 1.1em;
}

.content {
    margin-top: 50px;
}

h1 { font-size: 2em; margin-bottom: 10px; }
h2 { font-size: 1.5em; margin: 30px 0 15px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
h3 { font-size: 1.2em; margin: 25px 0 10px; color: var(--primary-dark); }
h4 { font-size: 1em; margin: 15px 0 8px; }

.card {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    margin: 15px 0;
    box-shadow: var(--card-shadow);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.card-title {
    font-size: 1.1em;
    font-weight: 600;
    font-family: "SFMono-Regular", Consolas, monospace;
}

.card-badge {
    background: var(--primary);
    color: white;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75em;
}

.brief {
    color: var(--text-secondary);
    margin-bottom: 12px;
    font-style: italic;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 0.9em;
}

th, td {
    text-align: left;
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
}

th {
    background: var(--code-bg);
    font-weight: 600;
    font-size: 0.85em;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

code {
    background: var(--code-bg);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: "SFMono-Regular", Consolas, monospace;
    font-size: 0.9em;
}

.todo {
    color: #d32f2f;
    font-size: 0.85em;
}

.search-results {
    display: none;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin: 10px 0;
    max-height: 300px;
    overflow-y: auto;
}

.search-result-item {
    padding: 10px 15px;
    border-bottom: 1px solid var(--border);
    cursor: pointer;
    transition: background 0.1s;
}

.search-result-item:hover {
    background: var(--bg-secondary);
}

.search-result-item:last-child {
    border-bottom: none;
}

@media (max-width: 768px) {
    .sidebar { display: none; }
    .main { margin-left: 0; padding: 20px; }
    .topbar { left: 0; }
}
```

- [ ] **Step 2: 创建 JavaScript 搜索与主题切换 templates/html/script.js**

```javascript
// 主题切换
function initTheme() {
    const saved = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = saved || (prefersDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
}

// 搜索功能
function initSearch() {
    const searchBox = document.getElementById('search');
    const searchResults = document.getElementById('search-results');
    if (!searchBox || !searchResults) return;

    // 收集所有可搜索的条目
    const items = [];
    document.querySelectorAll('[data-searchable]').forEach(el => {
        items.push({
            text: el.getAttribute('data-searchable'),
            type: el.getAttribute('data-type') || '',
            element: el
        });
    });

    searchBox.addEventListener('input', function() {
        const query = this.value.toLowerCase().trim();
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }

        const matches = items.filter(item =>
            item.text.toLowerCase().includes(query) ||
            item.type.toLowerCase().includes(query)
        );

        if (matches.length === 0) {
            searchResults.style.display = 'none';
            return;
        }

        searchResults.innerHTML = matches.slice(0, 20).map(item =>
            `<div class="search-result-item" data-target="${item.element.id}">
                <strong>${item.text}</strong>
                <span style="color:var(--text-secondary);font-size:0.85em;margin-left:8px">${item.type}</span>
            </div>`
        ).join('');
        searchResults.style.display = 'block';

        searchResults.querySelectorAll('.search-result-item').forEach(el => {
            el.addEventListener('click', function() {
                const targetId = this.getAttribute('data-target');
                const target = document.getElementById(targetId);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    searchResults.style.display = 'none';
                    searchBox.value = '';
                }
            });
        });
    });

    // 点击外部关闭搜索结果
    document.addEventListener('click', function(e) {
        if (!searchBox.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.style.display = 'none';
        }
    });
}

// 侧边栏高亮当前章节
function initSidebarHighlight() {
    const sections = document.querySelectorAll('h2[id], h3[id], h4[id]');
    const navItems = document.querySelectorAll('.nav-item');

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                navItems.forEach(item => item.classList.remove('active'));
                const activeItem = document.querySelector(`.nav-item[href="#${entry.target.id}"]`);
                if (activeItem) activeItem.classList.add('active');
            }
        });
    }, { rootMargin: '-80px 0px -80% 0px' });

    sections.forEach(section => observer.observe(section));
}

document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    initSearch();
    initSidebarHighlight();
});
```

- [ ] **Step 3: 创建 HTML 模板 templates/html/base.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ project.project_name }} - API 文档</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="topbar">
        <input type="text" id="search" class="search-box" placeholder="搜索 API...">
        <button class="theme-toggle" onclick="toggleTheme()" title="切换主题">&#9790;</button>
    </div>

    <div class="layout">
        <nav class="sidebar">
            <h2>{{ project.project_name }}</h2>
            {% for file in project.files %}
            <div class="nav-group">
                <div class="nav-group-title">{{ file.path | basename }}</div>
                {% for fn in file.functions %}
                <a class="nav-item" href="#fn-{{ fn.name }}">{{ fn.name }}()</a>
                {% endfor %}
                {% for s in file.structs %}
                <a class="nav-item" href="#struct-{{ s.name }}">{{ s.name }}</a>
                {% endfor %}
                {% for e in file.enums %}
                <a class="nav-item" href="#enum-{{ e.name }}">{{ e.name }}</a>
                {% endfor %}
                {% for m in file.macros %}
                <a class="nav-item" href="#macro-{{ m.name }}">#{{ m.name }}</a>
                {% endfor %}
            </div>
            {% endfor %}
        </nav>

        <div class="main">
            <div class="content">
                <h1>{{ project.project_name }} API 文档</h1>
                <p style="color:var(--text-secondary)">生成时间: {{ project.generated_at }}</p>

                {% for file in project.files %}
                <h2 id="file-{{ loop.index }}">{{ file.path | basename }}</h2>
                {% if file.brief %}<p class="brief">{{ file.brief }}</p>{% endif %}

                {% if file.functions %}
                <h3>函数</h3>
                {% for fn in file.functions %}
                <div class="card" id="fn-{{ fn.name }}" data-searchable="{{ fn.name }}" data-type="函数">
                    <div class="card-header">
                        <span class="card-title">{{ fn.name }}()</span>
                        <span class="card-badge">函数</span>
                    </div>
                    {% if fn.brief and not fn.brief.startswith('TODO:') %}
                        <p class="brief">{{ fn.brief }}</p>
                    {% else %}
                        <p class="brief todo">{{ fn.brief or 'TODO: 描述功能' }}</p>
                    {% endif %}

                    {% if fn.params %}
                    <table>
                        <thead><tr><th>参数</th><th>类型</th><th>说明</th></tr></thead>
                        <tbody>
                        {% for p in fn.params %}
                        <tr>
                            <td><code>{{ p.name }}</code></td>
                            <td><code>{{ p.type }}</code></td>
                            <td>{{ p.brief or '—' }}</td>
                        </tr>
                        {% endfor %}
                        </tbody>
                    </table>
                    {% endif %}

                    {% if fn.return_type and fn.return_type != 'void' %}
                    <p><strong>返回值:</strong> <code>{{ fn.return_type }}</code>{% if fn.return_brief %} — {{ fn.return_brief }}{% endif %}</p>
                    {% endif %}
                </div>
                {% endfor %}
                {% endif %}

                {% if file.structs %}
                <h3>结构体</h3>
                {% for s in file.structs %}
                <div class="card" id="struct-{{ s.name }}" data-searchable="{{ s.name }}" data-type="结构体">
                    <div class="card-header">
                        <span class="card-title">{{ s.name }}</span>
                        <span class="card-badge">{{ s.kind }}</span>
                    </div>
                    {% if s.brief and not s.brief.startswith('TODO:') %}
                        <p class="brief">{{ s.brief }}</p>
                    {% else %}
                        <p class="brief todo">{{ s.brief or 'TODO: 描述结构体' }}</p>
                    {% endif %}

                    {% if s.fields %}
                    <table>
                        <thead><tr><th>字段</th><th>类型</th><th>说明</th></tr></thead>
                        <tbody>
                        {% for f in s.fields %}
                        <tr>
                            <td><code>{{ f.name }}</code></td>
                            <td><code>{{ f.type }}</code></td>
                            <td>{{ f.brief or '—' }}</td>
                        </tr>
                        {% endfor %}
                        </tbody>
                    </table>
                    {% endif %}
                </div>
                {% endfor %}
                {% endif %}

                {% if file.enums %}
                <h3>枚举</h3>
                {% for e in file.enums %}
                <div class="card" id="enum-{{ e.name }}" data-searchable="{{ e.name }}" data-type="枚举">
                    <div class="card-header">
                        <span class="card-title">{{ e.name }}</span>
                        <span class="card-badge">enum</span>
                    </div>
                    {% if e.brief and not e.brief.startswith('TODO:') %}
                        <p class="brief">{{ e.brief }}</p>
                    {% else %}
                        <p class="brief todo">{{ e.brief or 'TODO: 描述枚举' }}</p>
                    {% endif %}

                    {% if e.values %}
                    <table>
                        <thead><tr><th>值</th><th>数值</th><th>说明</th></tr></thead>
                        <tbody>
                        {% for v in e.values %}
                        <tr>
                            <td><code>{{ v.name }}</code></td>
                            <td>{{ v.value or '—' }}</td>
                            <td>{{ v.brief or '—' }}</td>
                        </tr>
                        {% endfor %}
                        </tbody>
                    </table>
                    {% endif %}
                </div>
                {% endfor %}
                {% endif %}

                {% if file.macros %}
                <h3>宏定义</h3>
                {% for m in file.macros %}
                <div class="card" id="macro-{{ m.name }}" data-searchable="{{ m.name }}" data-type="宏">
                    <div class="card-header">
                        <span class="card-title">#{{ m.name }}</span>
                        <span class="card-badge">{% if m.is_function_like %}函数式宏{% else %}宏{% endif %}</span>
                    </div>
                    {% if m.brief and not m.brief.startswith('TODO:') %}
                        <p class="brief">{{ m.brief }}</p>
                    {% else %}
                        <p class="brief todo">{{ m.brief or 'TODO: 描述宏' }}</p>
                    {% endif %}
                    {% if m.is_function_like and m.params %}
                    <p>参数: {% for p in m.params %}<code>{{ p }}</code>{% if not loop.last %}, {% endif %}{% endfor %}</p>
                    {% endif %}
                </div>
                {% endfor %}
                {% endif %}

                {% if file.globals %}
                <h3>全局变量</h3>
                <table>
                    <thead><tr><th>变量名</th><th>类型</th><th>说明</th></tr></thead>
                    <tbody>
                    {% for g in file.globals %}
                    <tr>
                        <td><code>{{ g.name }}</code></td>
                        <td><code>{{ g.type }}</code></td>
                        <td>{{ g.brief or '—' }}</td>
                    </tr>
                    {% endfor %}
                    </tbody>
                </table>
                {% endif %}

                {% endfor %}
            </div>
        </div>
    </div>

    <div id="search-results" class="search-results"></div>
    <script src="script.js"></script>
</body>
</html>
```

- [ ] **Step 4: 创建测试 tests/test_exporter_html.py**

```python
"""exporter.py HTML 导出测试"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'docs', 'superpowers', 'skills', 'doxygen-doc', 'scripts'))

from exporter import DocExporter
from models import ProjectInfo, FileInfo, FunctionInfo, Param


def _make_sample_project():
    return ProjectInfo(
        project_name="test_project",
        files=[
            FileInfo(
                path="src/test.c",
                functions=[
                    FunctionInfo(
                        name="add", return_type="int",
                        params=[Param(name="a", type="int"), Param(name="b", type="int")],
                        brief="两数之和"
                    )
                ]
            )
        ]
    )


def test_export_html(tmp_path):
    project = _make_sample_project()
    exporter = DocExporter()
    templates_dir = os.path.join(
        os.path.dirname(__file__), '..', 'templates', 'html'
    )
    output_dir = str(tmp_path / "api")
    exporter.export_html(project, output_dir, templates_dir=templates_dir)

    index_path = os.path.join(output_dir, "index.html")
    assert os.path.exists(index_path)
    assert os.path.exists(os.path.join(output_dir, "style.css"))
    assert os.path.exists(os.path.join(output_dir, "script.js"))

    with open(index_path, encoding="utf-8") as f:
        content = f.read()

    assert "test_project" in content
    assert "add()" in content
    assert "两数之和" in content
```

- [ ] **Step 5: 在 exporter.py 中添加 HTML 导出方法**

```python
# 在 exporter.py 的 DocExporter 类中添加

def export_html(self, project: ProjectInfo, output_dir: str, templates_dir: str):
    """导出为 Docusaurus 风格 HTML"""
    import shutil
    from jinja2 import Environment, FileSystemLoader

    os.makedirs(output_dir, exist_ok=True)

    # 复制静态资源
    for asset in ("style.css", "script.js"):
        src = os.path.join(templates_dir, asset)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(output_dir, asset))

    # Jinja2 模板渲染
    env = Environment(loader=FileSystemLoader(templates_dir))

    # 添加 basename 过滤器
    env.filters['basename'] = os.path.basename

    template = env.get_template("base.html")
    html = template.render(project=project)

    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
```

- [ ] **Step 6: 运行测试确认通过**

```bash
pytest tests/test_exporter_html.py -v
```
预期: 全部 PASS

- [ ] **Step 7: 提交**

```bash
git add templates/html/ docs/superpowers/skills/doxygen-doc/scripts/exporter.py tests/test_exporter_html.py
git commit -m "feat: HTML 文档导出 (Docusaurus 风格)"
```

---

### Task 8: doxygen_generator.py — 主入口与 CLI

**Files:**
- Create: `docs/superpowers/skills/doxygen-doc/scripts/doxygen_generator.py`
- Create: `tests/test_integration.py`

- [ ] **Step 1: 实现主入口 doxygen_generator.py**

```python
#!/usr/bin/env python3
"""
Doxygen 注释生成器 — 主入口

用法:
    python doxygen_generator.py [目录/文件] [--export html|md|json|all]
"""
import argparse
import os
import sys
import glob
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from parser import CParser
from commentator import DoxygenCommentator
from writer import CommentWriter
from exporter import DocExporter
from models import ProjectInfo, FileInfo


def find_c_files(path: str) -> list[str]:
    """扫描 C/C++ 源文件"""
    if os.path.isfile(path):
        return [path]

    patterns = ["**/*.c", "**/*.h", "**/*.cpp", "**/*.hpp"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(path, pattern), recursive=True))
    return sorted(set(files))


def generate_comments_for_file(
    file_path: str,
    parser: CParser,
    commentator: DoxygenCommentator,
    writer: CommentWriter
) -> tuple[FileInfo, int]:
    """为单个文件生成注释

    Returns:
        (FileInfo, 生成的注释数量)
    """
    # 读取源文件
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        original_source = f.read()

    # 解析
    file_info = parser.parse_file(file_path)

    # 收集已有注释文本（从源码中提取）
    _extract_existing_comments(original_source, file_info)

    # 生成注释
    comment_count = 0
    file_comments = {"functions": {}, "structs": {}, "enums": {}, "macros": {}, "globals": {}}

    # 文件头注释
    file_comment = DoxygenCommentator.generate_file_comment(file_path)

    for i, fn in enumerate(file_info.functions):
        file_comments["functions"][i] = DoxygenCommentator.generate_function_comment(fn)
        comment_count += 1

    for i, s in enumerate(file_info.structs):
        file_comments["structs"][i] = DoxygenCommentator.generate_struct_comment(s)
        comment_count += 1

    for i, e in enumerate(file_info.enums):
        file_comments["enums"][i] = DoxygenCommentator.generate_enum_comment(e)
        comment_count += 1

    for i, m in enumerate(file_info.macros):
        file_comments["macros"][i] = DoxygenCommentator.generate_macro_comment(m)
        comment_count += 1

    for i, g in enumerate(file_info.globals):
        file_comments["globals"][i] = DoxygenCommentator.generate_global_comment(g)
        comment_count += 1

    # 写入
    result = writer.insert_comments(original_source, file_info, file_comments)
    result = writer.insert_file_header(result, file_comment)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(result)

    return file_info, comment_count


def _extract_existing_comments(source: str, file_info: FileInfo):
    """从源码中提取已有注释文本"""
    import re

    lines = source.split('\n')

    # 提取每个代码元素上方的注释
    all_elements = (
        [(fn.line_number, fn) for fn in file_info.functions] +
        [(s.line_number, s) for s in file_info.structs] +
        [(e.line_number, e) for e in file_info.enums] +
        [(m.line_number, m) for m in file_info.macros] +
        [(g.line_number, g) for g in file_info.globals]
    )

    for line_num, element in all_elements:
        if line_num <= 1:
            continue

        # 向上查找注释
        comment_text = ""
        check_idx = line_num - 2  # 上一行（0-indexed）

        # 跳过空行
        while check_idx >= 0 and not lines[check_idx].strip():
            check_idx -= 1

        if check_idx < 0:
            continue

        line = lines[check_idx].strip()

        # 检查 Doxygen 注释结尾 */
        if line.endswith("*/"):
            element.has_existing_comment = True
            # 提取 @brief 内容
            doxygen_match = re.search(r'@brief\s+(.+)', source)
            if doxygen_match:
                element.existing_comment_text = doxygen_match.group(1).strip()
            # 提取普通注释内容
            else:
                comment_match = re.search(r'/\*\*?\s*(.*?)\s*\*/', line, re.DOTALL)
                if comment_match:
                    element.existing_comment_text = comment_match.group(1).strip()

        # 检查 // 单行注释
        elif line.startswith("//"):
            element.has_existing_comment = True
            element.existing_comment_text = line[2:].strip()


def main():
    parser = argparse.ArgumentParser(description="C/C++ Doxygen 注释生成器")
    parser.add_argument("path", nargs="?", default=".", help="要处理的目录或文件路径")
    parser.add_argument("--export", choices=["html", "md", "json", "all"],
                       help="仅导出文档格式（跳过注释生成）")
    parser.add_argument("--project-name", default="API", help="项目名称（用于文档导出）")
    parser.add_argument("--output", default="docs/api", help="文档输出目录")

    args = parser.parse_args()

    # 验证路径
    if not os.path.exists(args.path):
        print(f"错误: 路径不存在: {args.path}")
        sys.exit(1)

    # 初始化组件
    c_parser = CParser()
    commentator = DoxygenCommentator()
    writer = CommentWriter()
    exporter = DocExporter()

    # 扫描文件
    c_files = find_c_files(args.path)
    if not c_files:
        print("未找到 C/C++ 文件")
        sys.exit(0)

    print(f"扫描到 {len(c_files)} 个文件\n")

    if args.export:
        # 仅导出模式：解析所有文件，然后导出
        project = ProjectInfo(project_name=args.project_name)
        for fp in c_files:
            file_info = c_parser.parse_file(fp)
            _extract_existing_comments(open(fp, encoding="utf-8", errors="replace").read(), file_info)
            project.files.append(file_info)

        templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "templates", "html")

        if args.export in ("json", "all"):
            os.makedirs(args.output, exist_ok=True)
            exporter.export_json(project, os.path.join(args.output, "api.json"))
            print(f"  JSON: {args.output}/api.json")

        if args.export in ("md", "all"):
            exporter.export_markdown(project, args.output)
            print(f"  Markdown: {args.output}/index.md")

        if args.export in ("html", "all"):
            exporter.export_html(project, args.output, templates_dir=templates_dir)
            print(f"  HTML: {args.output}/index.html")

        return

    # 注释生成模式
    project = ProjectInfo(project_name=args.project_name)
    total_comments = 0

    for fp in c_files:
        print(f"  处理: {fp}")
        file_info, count = generate_comments_for_file(fp, c_parser, commentator, writer)
        project.files.append(file_info)
        total_comments += count
        print(f"    → 生成 {count} 个注释")

    print(f"\n完成: 处理 {len(c_files)} 个文件，生成 {total_comments} 个注释")

    # 自动生成 JSON 导出
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "templates", "html")
    os.makedirs(args.output, exist_ok=True)
    exporter.export_json(project, os.path.join(args.output, "api.json"))
    exporter.export_markdown(project, args.output)
    exporter.export_html(project, args.output, templates_dir=templates_dir)
    print(f"文档已导出到 {args.output}/")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 创建集成测试 tests/test_integration.py**

```python
"""集成测试 — 端到端流程"""
import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'docs', 'superpowers', 'skills', 'doxygen-doc', 'scripts'))

from parser import CParser
from commentator import DoxygenCommentator
from writer import CommentWriter
from exporter import DocExporter
from models import ProjectInfo


SAMPLE_C_FILE = """\
#include <stdint.h>

// 表示两个数的和
int add(int a, int b) {
    return a + b;
}

typedef struct {
    uint8_t brightness;
    uint8_t mode;
} Config_t;

typedef enum {
    MODE_OFF = 0,
    MODE_ON = 1
} Mode_t;

#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define BUFFER_SIZE 1024

extern uint32_t g_tick_count;
"""


def test_full_pipeline():
    """测试完整流程：解析 → 生成注释 → 写入 → 导出"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 写入测试文件
        src_file = os.path.join(tmpdir, "test.c")
        with open(src_file, "w") as f:
            f.write(SAMPLE_C_FILE)

        # 解析
        parser = CParser()
        file_info = parser.parse_file(src_file)
        assert len(file_info.functions) == 1
        assert len(file_info.structs) == 1
        assert len(file_info.enums) == 1
        assert len(file_info.macros) == 2
        assert len(file_info.globals) == 1

        # 搬入已有注释
        with open(src_file, encoding="utf-8") as f:
            source = f.read()

        import re
        for fn in file_info.functions:
            match = re.search(r'//\s*(.*)', source)
            if match:
                fn.has_existing_comment = True
                fn.existing_comment_text = match.group(1).strip()

        # 生成注释
        commentator = DoxygenCommentator()
        writer = CommentWriter()
        file_comments = {
            "functions": {0: commentator.generate_function_comment(file_info.functions[0])},
            "structs": {0: commentator.generate_struct_comment(file_info.structs[0])},
            "enums": {0: commentator.generate_enum_comment(file_info.enums[0])},
            "macros": {
                0: commentator.generate_macro_comment(file_info.macros[0]),
                1: commentator.generate_macro_comment(file_info.macros[1])
            },
            "globals": {0: commentator.generate_global_comment(file_info.globals[0])}
        }

        # 写入
        result = writer.insert_comments(source, file_info, file_comments)
        result = writer.insert_file_header(result, commentator.generate_file_comment(src_file))

        with open(src_file, "w") as f:
            f.write(result)

        # 验证写入结果
        with open(src_file) as f:
            final = f.read()

        assert "@file test.c" in final
        assert "@brief 表示两个数的和" in final
        assert "@param a" in final
        assert "@return int" in final
        assert "@brief TODO: 描述结构体" in final
        assert "@brief TODO: 描述枚举" in final
        assert "@brief TODO: 描述宏" in final
        assert "@brief TODO: 描述全局变量" in final

        # 导出
        out_dir = os.path.join(tmpdir, "api")
        project = ProjectInfo(project_name="test", files=[file_info])
        exporter = DocExporter()

        templates_dir = os.path.join(
            os.path.dirname(__file__), '..', 'templates', 'html'
        )

        exporter.export_json(project, os.path.join(out_dir, "api.json"))
        exporter.export_markdown(project, out_dir)
        exporter.export_html(project, out_dir, templates_dir=templates_dir)

        assert os.path.exists(os.path.join(out_dir, "api.json"))
        assert os.path.exists(os.path.join(out_dir, "index.md"))
        assert os.path.exists(os.path.join(out_dir, "index.html"))
```

- [ ] **Step 3: 运行所有测试**

```bash
pytest tests/ -v
```
预期: 全部 PASS

- [ ] **Step 4: 提交**

```bash
git add docs/superpowers/skills/doxygen-doc/scripts/doxygen_generator.py tests/test_integration.py
git commit -m "feat: 主入口 CLI 与集成测试"
```

---

### Task 9: SKILL.md — Claude Code 技能定义

**Files:**
- Create: `docs/superpowers/skills/doxygen-doc/SKILL.md`

- [ ] **Step 1: 创建 SKILL.md**

```markdown
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
- 结构体/联合体：`@brief`、字段用 `/**< */` 行内注释
- 枚举：`@brief`、枚举值用 `/**< */` 行内注释
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
```

- [ ] **Step 2: 提交**

```bash
git add docs/superpowers/skills/doxygen-doc/SKILL.md
git commit -m "feat: Doxygen Doc 技能定义文件"
```

---

### Task 10: 安装脚本与 README

**Files:**
- Create: `docs/superpowers/skills/doxygen-doc/install.sh`
- Create: `docs/superpowers/skills/doxygen-doc/README.md`

- [ ] **Step 1: 创建安装脚本 install.sh**

```bash
#!/bin/bash
# Doxygen Doc 技能安装脚本

echo "安装 Doxygen Doc 依赖..."
pip install tree-sitter tree-sitter-c Jinja2

echo "依赖安装完成！"
echo ""
echo "使用方法："
echo "  python docs/superpowers/skills/doxygen-doc/scripts/doxygen_generator.py [目录]"
echo "  python docs/superpowers/skills/doxygen-doc/scripts/doxygen_generator.py --export html"
```

- [ ] **Step 2: 设置执行权限**

```bash
chmod +x docs/superpowers/skills/doxygen-doc/install.sh
```

- [ ] **Step 3: 提交**

```bash
git add docs/superpowers/skills/doxygen-doc/install.sh docs/superpowers/skills/doxygen-doc/README.md
git commit -m "feat: 安装脚本与使用说明"
```

---

## 验收标准

1. `pytest tests/ -v` 全部通过
2. 对一个示例 C 文件运行 `python doxygen_generator.py test.c`，输出包含标准 Doxygen 注释
3. 运行 `python doxygen_generator.py --export all` 生成 JSON/Markdown/HTML 三种文档
4. HTML 文档可在浏览器中正常浏览，支持搜索和暗色模式
5. 已有注释被正确搬入 @brief 字段
