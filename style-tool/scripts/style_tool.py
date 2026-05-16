#!/usr/bin/env python3
"""
style_tool — C/C++ 代码格式化 + Doxygen 注释生成

用法:
    python style_tool.py [目录/文件] --mode format   # 仅格式化
    python style_tool.py [目录/文件] --mode comment  # 仅注释
    python style_tool.py [目录/文件] --mode all      # 格式化+注释
    python style_tool.py [目录/文件] --indent 2      # 使用2空格缩进
"""
import argparse
import os
import sys
import glob
import re
from datetime import date
import chardet

# 同目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser import CParser
from models import FileInfo, FunctionInfo, StructInfo, EnumInfo, MacroInfo, GlobalVarInfo


# ============================================================
# 代码格式化器
# ============================================================

class CodeFormatter:
    """C/C++ 代码格式化器"""

    def __init__(self, indent_size=4):
        self.indent_str = " " * indent_size

    def format_source(self, source: str) -> str:
        lines = source.split('\n')
        lines = self._fix_indentation(lines)
        lines = self._fix_brace_style(lines)
        lines = self._strip_trailing(lines)
        lines = self._fix_blank_lines(lines)
        return '\n'.join(lines)

    def _fix_indentation(self, lines: list[str]) -> list[str]:
        result = []
        depth = 0
        in_block_comment = False

        for line in lines:
            stripped = line.strip()

            if not stripped:
                result.append("")
                continue

            if stripped.startswith('#'):
                result.append(stripped)
                continue

            if in_block_comment:
                if stripped.startswith('*'):
                    result.append(self.indent_str * depth + ' ' + stripped)
                else:
                    result.append(self.indent_str * depth + stripped)
                if '*/' in stripped:
                    in_block_comment = False
                continue

            if stripped.startswith('/*'):
                result.append(self.indent_str * depth + stripped)
                if '*/' not in stripped:
                    in_block_comment = True
                continue

            if stripped.startswith('//'):
                result.append(self.indent_str * depth + stripped)
                continue

            if stripped.startswith('}'):
                depth = max(0, depth - 1)

            result.append(self.indent_str * depth + stripped)

            open_count = stripped.count('{') - stripped.count('}')
            if open_count > 0:
                depth += open_count
            elif open_count < 0 and not stripped.startswith('}'):
                depth = max(0, depth + open_count)

        return result

    def _fix_brace_style(self, lines: list[str]) -> list[str]:
        result = []
        for line in lines:
            if line.strip() == '{' and result:
                prev = result[-1].rstrip()
                if prev and not prev.endswith('{') and not prev.endswith('}'):
                    result[-1] = prev + ' {'
                else:
                    result.append(line)
            else:
                result.append(line)
        return result

    def _strip_trailing(self, lines: list[str]) -> list[str]:
        return [line.rstrip() for line in lines]

    def _fix_blank_lines(self, lines: list[str]) -> list[str]:
        result = []
        blank_count = 0
        for line in lines:
            if not line.strip():
                blank_count += 1
                if blank_count <= 2:
                    result.append(line)
            else:
                blank_count = 0
                result.append(line)
        while result and not result[-1].strip():
            result.pop()
        result.append("")
        return result


# ============================================================
# 辅助函数
# ============================================================

def find_c_files(path: str) -> list:
    if os.path.isfile(path):
        return [path]
    patterns = ["**/*.c", "**/*.h", "**/*.cpp", "**/*.hpp"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(path, p), recursive=True))
    return sorted(set(files))


def detect_encoding(file_path: str) -> str:
    with open(file_path, "rb") as f:
        raw = f.read()
    result = chardet.detect(raw)
    encoding = result.get("encoding", "utf-8") or "utf-8"
    if encoding.lower() in ("gb2312", "gbk", "gb18030"):
        return "gb18030"
    return encoding


# ============================================================
# 注释提取 — 保留用户填写的内容
# ============================================================

def find_comment_block(lines: list[str], element_line: int):
    """查找元素上方的注释块，返回 (start_idx, end_idx) 或 None"""
    idx = element_line - 2
    while idx >= 0 and not lines[idx].strip():
        idx -= 1
    if idx < 0:
        return None

    if lines[idx].strip().endswith('*/'):
        end_idx = idx
        start_idx = idx
        while start_idx >= 0 and not lines[start_idx].strip().startswith('/*'):
            start_idx -= 1
        if start_idx >= 0:
            return (start_idx, end_idx)

    if lines[idx].strip().startswith('//'):
        return (idx, idx)

    return None


def extract_existing_content(lines: list[str], block) -> dict:
    """从已有注释中提取用户填写的内容"""
    content = {"brief": "", "note": "", "see": "", "params": {}, "return_text": ""}

    if block is None:
        return content

    start, end = block
    comment_text = "\n".join(lines[start:end + 1])

    m = re.search(r'@brief\s+(.+)', comment_text)
    if m:
        brief = m.group(1).strip()
        if brief and not brief.startswith("TODO"):
            content["brief"] = brief

    m = re.search(r'@note\s+(.+)', comment_text)
    if m:
        note = m.group(1).strip()
        if note and not note.startswith("TODO"):
            content["note"] = note

    m = re.search(r'@see\s+(.+)', comment_text)
    if m:
        see = m.group(1).strip()
        if see and not see.startswith("TODO"):
            content["see"] = see

    for pm in re.finditer(r'@param(?:\[(?:in|out|inout)\])?\s+(\w+)\s+(.+)', comment_text):
        desc = pm.group(2).strip()
        if desc and not desc.startswith("TODO"):
            content["params"][pm.group(1)] = desc

    m = re.search(r'@return\s+(.+)', comment_text)
    if m:
        ret = m.group(1).strip()
        if ret and not ret.startswith("TODO"):
            content["return_text"] = ret

    # 处理普通 // 注释
    if start == end and lines[start].strip().startswith('//'):
        text = lines[start].strip()[2:].strip()
        if text and not text.startswith("TODO"):
            content["brief"] = text

    # 提取 @brief 之后的描述行（非标签的内容行）
    if content["brief"]:
        brief_lines = []
        in_brief = False
        for cline in comment_text.split('\n'):
            cline_stripped = cline.strip().lstrip('*').strip()
            # 跳过注释结束标记
            if cline_stripped == '/' or cline_stripped == '':
                continue
            if cline_stripped.startswith('@brief'):
                in_brief = True
                continue
            if in_brief:
                if cline_stripped.startswith('@'):
                    break
                if cline_stripped and not cline_stripped.startswith("TODO"):
                    brief_lines.append(cline_stripped)
        if brief_lines:
            content["brief_extra"] = "\n".join(brief_lines)

    return content


# ============================================================
# 华为标准注释生成
# ============================================================

def generate_file_header(file_path: str, existing: dict = None) -> str:
    """生成文件头注释 — 华为标准: @file @brief @author @version @date @copyright"""
    filename = os.path.basename(file_path)
    today = date.today().isoformat()
    brief = (existing or {}).get("brief", "")

    lines = [
        "/**",
        f" * @file {filename}",
        f" * @brief {brief if brief else 'TODO: 文件描述'}",
        " * @author",
        " * @version 1.0",
        f" * @date {today}",
        " * @copyright Copyright (c) 2026",
        " */",
    ]
    return "\n".join(lines)


def generate_function_comment(fn, existing: dict = None) -> str:
    """生成函数注释 — 华为标准: @brief @param[in] @return @note @see"""
    ex = existing or {}
    brief = ex.get("brief", "")
    brief_extra = ex.get("brief_extra", "")
    note = ex.get("note", "")
    see = ex.get("see", "")
    ret_text = ex.get("return_text", "")
    param_descs = ex.get("params", {})

    lines = ["/**"]
    lines.append(f" * @brief {brief if brief else 'TODO: 描述功能'}")
    lines.append(" *")
    if brief_extra:
        for bel in brief_extra.split('\n'):
            lines.append(f" * {bel}")
    else:
        lines.append(" * TODO: 详细描述函数的业务逻辑")
    lines.append(" *")

    for p in fn.params:
        desc = param_descs.get(p.name, "")
        lines.append(f" * @param[in] {p.name}  {desc if desc else f'TODO: {p.name} 的含义'}")

    if fn.return_type and fn.return_type != "void":
        lines.append(f" * @return {ret_text if ret_text else f'TODO: 返回值含义'}")

    lines.append(" *")
    lines.append(f" * @note {note if note else 'TODO: 注意事项（可选）'}")
    lines.append(f" * @see  {see if see else 'TODO: 相关函数（可选）'}")
    lines.append(" */")
    return "\n".join(lines)


def generate_struct_comment(s, existing: dict = None) -> str:
    """生成结构体注释"""
    ex = existing or {}
    brief = ex.get("brief", "")
    if not brief:
        kind_name = "结构体" if s.kind == "struct" else "联合体"
        brief = f"TODO: 描述{kind_name}"

    lines = [
        "/**",
        f" * @brief {brief}",
        " *",
        " * TODO: 详细描述结构体的用途",
        " */",
    ]
    return "\n".join(lines)


def generate_enum_comment(e, existing: dict = None) -> str:
    """生成枚举注释"""
    ex = existing or {}
    brief = ex.get("brief", "")

    lines = [
        "/**",
        f" * @brief {brief if brief else 'TODO: 描述枚举'}",
        " *",
        " * TODO: 详细描述枚举的用途",
        " */",
    ]
    return "\n".join(lines)


def generate_macro_comment(m, existing: dict = None) -> str:
    """生成宏注释"""
    ex = existing or {}
    brief = ex.get("brief", "")

    lines = [
        "/**",
        f" * @brief {brief if brief else 'TODO: 描述宏'}",
    ]

    if m.is_function_like and m.params:
        lines.append(" *")
        for p in m.params:
            desc = ex.get("params", {}).get(p, "")
            lines.append(f" * @param {p}  {desc if desc else f'TODO: {p} 的含义'}")

    lines.append(" */")
    return "\n".join(lines)


def generate_global_comment(g, existing: dict = None) -> str:
    """生成全局变量注释"""
    ex = existing or {}
    brief = ex.get("brief", "")

    lines = [
        "/**",
        f" * @brief {brief if brief else 'TODO: 描述全局变量'}",
        " */",
    ]
    return "\n".join(lines)


# ============================================================
# 注释处理主逻辑 — 每次都执行，保留用户内容
# ============================================================

def enhance_comments_for_file(file_path: str) -> int:
    """处理单个文件的注释，返回处理的注释数。
    所有操作基于原始行号，从后往前统一应用。"""
    encoding = detect_encoding(file_path)
    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        source = f.read()

    lines = source.split('\n')
    c_parser = CParser()
    file_info = c_parser.parse_file(file_path)

    # (start_idx, end_idx, new_comment_text)
    # end_idx < start_idx 表示仅插入不删除
    replacements = []

    # 处理所有代码元素的注释
    elements = (
        [(fn.line_number, fn, "function") for fn in file_info.functions] +
        [(s.line_number, s, "struct") for s in file_info.structs] +
        [(e.line_number, e, "enum") for e in file_info.enums] +
        [(m.line_number, m, "macro") for m in file_info.macros] +
        [(g.line_number, g, "global") for g in file_info.globals]
    )

    for line_num, element, kind in elements:
        block = find_comment_block(lines, line_num)
        existing = extract_existing_content(lines, block)

        if kind == "function":
            new_comment = generate_function_comment(element, existing)
        elif kind == "struct":
            new_comment = generate_struct_comment(element, existing)
        elif kind == "enum":
            new_comment = generate_enum_comment(element, existing)
        elif kind == "macro":
            new_comment = generate_macro_comment(element, existing)
        else:
            new_comment = generate_global_comment(element, existing)

        if block:
            replacements.append((block[0], block[1], new_comment))
        else:
            insert_idx = line_num - 1
            replacements.append((insert_idx, insert_idx - 1, new_comment))

    # 处理文件头 — 只匹配包含 @file 的注释块
    header_info = {}
    header_found = False
    for i, line in enumerate(lines[:20]):
        if line.strip().startswith('/**'):
            # 找到注释块的结尾
            block_end = None
            for j in range(i, min(i + 15, len(lines))):
                if lines[j].strip().endswith('*/'):
                    block_end = j
                    break
            if block_end is None:
                continue
            block_text = "\n".join(lines[i:block_end + 1])
            if '@file' in block_text:
                # 这是文件头注释
                m = re.search(r'@brief\s+(.+)', block_text)
                if m:
                    brief = m.group(1).strip()
                    if brief and not brief.startswith("TODO"):
                        header_info["brief"] = brief
                new_header = generate_file_header(file_path, header_info)
                replacements.append((i, block_end, new_header))
                header_found = True
            break  # 只检查第一个注释块

    if not header_found:
        new_header = generate_file_header(file_path, {})
        replacements.append((0, -1, new_header))

    # 从后往前统一应用，避免行号偏移
    replacements.sort(key=lambda r: r[0], reverse=True)

    for start_idx, end_idx, new_comment in replacements:
        if end_idx >= start_idx:
            del lines[start_idx:end_idx + 1]
        new_comment_lines = new_comment.split('\n')
        for j, nl in enumerate(new_comment_lines):
            lines.insert(start_idx + j, nl)

    result = '\n'.join(lines)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(result)

    return len(replacements)


# ============================================================
# CLI
# ============================================================

def main():
    arg_parser = argparse.ArgumentParser(
        description="C/C++ 代码格式化 + Doxygen 注释生成"
    )
    arg_parser.add_argument("path", nargs="?", default=".", help="目录或文件路径")
    arg_parser.add_argument(
        "--mode", choices=["format", "comment", "all"], default="all",
        help="format=格式化, comment=注释, all=两者都执行"
    )
    arg_parser.add_argument(
        "--indent", type=int, default=4, help="缩进空格数 (默认4)"
    )
    arg_parser.add_argument("--encoding", help="强制指定文件编码")

    args = arg_parser.parse_args()

    if not os.path.exists(args.path):
        print(f"错误: 路径不存在: {args.path}")
        sys.exit(1)

    c_files = find_c_files(args.path)
    if not c_files:
        print("未找到 C/C++ 文件")
        sys.exit(0)

    print(f"扫描到 {len(c_files)} 个文件\n")

    # 格式化
    if args.mode in ("format", "all"):
        formatter = CodeFormatter(indent_size=args.indent)
        for fp in c_files:
            print(f"  格式化: {fp}")
            enc = args.encoding or detect_encoding(fp)
            with open(fp, "r", encoding=enc, errors="replace") as f:
                source = f.read()
            formatted = formatter.format_source(source)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(formatted)
        print()

    # 注释 — 每次都执行，保留用户填写的 @brief
    if args.mode in ("comment", "all"):
        total = 0
        for fp in c_files:
            print(f"  注释: {fp}")
            count = enhance_comments_for_file(fp)
            total += count
            print(f"    → 处理 {count} 个注释")
        print(f"\n完成: {len(c_files)} 个文件, {total} 个注释")


if __name__ == "__main__":
    main()
