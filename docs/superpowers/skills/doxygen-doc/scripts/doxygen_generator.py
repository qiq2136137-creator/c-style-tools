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
import re
import chardet

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from parser import CParser
from commentator import DoxygenCommentator
from writer import CommentWriter
from exporter import DocExporter
from models import ProjectInfo, FileInfo


def detect_encoding(file_path: str) -> str:
    """检测文件编码"""
    with open(file_path, "rb") as f:
        raw = f.read()
    result = chardet.detect(raw)
    encoding = result.get("encoding", "utf-8") or "utf-8"
    # 常见中文编码修正
    if encoding.lower() in ("gb2312", "gbk", "gb18030"):
        return "gb18030"
    return encoding


def find_c_files(path: str) -> list:
    """扫描 C/C++ 源文件"""
    if os.path.isfile(path):
        return [path]

    patterns = ["**/*.c", "**/*.h", "**/*.cpp", "**/*.hpp"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(path, pattern), recursive=True))
    return sorted(set(files))


def _extract_existing_comments(source: str, file_info: FileInfo):
    """从源码中提取已有注释文本"""
    lines = source.split('\n')

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

        check_idx = line_num - 2

        while check_idx >= 0 and not lines[check_idx].strip():
            check_idx -= 1

        if check_idx < 0:
            continue

        line = lines[check_idx].strip()

        if line.endswith("*/"):
            element.has_existing_comment = True
            doxygen_match = re.search(r'@brief\s+(.+)', source)
            if doxygen_match:
                element.existing_comment_text = doxygen_match.group(1).strip()
            else:
                comment_match = re.search(r'/\*\*?\s*(.*?)\s*\*/', line, re.DOTALL)
                if comment_match:
                    element.existing_comment_text = comment_match.group(1).strip()

        elif line.startswith("//"):
            element.has_existing_comment = True
            element.existing_comment_text = line[2:].strip()


def generate_comments_for_file(
    file_path: str,
    parser: CParser,
    commentator: DoxygenCommentator,
    writer: CommentWriter
) -> tuple:
    """为单个文件生成注释"""
    encoding = detect_encoding(file_path)
    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        original_source = f.read()

    file_info = parser.parse_file(file_path)
    _extract_existing_comments(original_source, file_info)

    comment_count = 0
    file_comments = {"functions": {}, "structs": {}, "enums": {}, "macros": {}, "globals": {}}

    file_comment = commentator.generate_file_comment(file_path)

    for i, fn in enumerate(file_info.functions):
        file_comments["functions"][i] = commentator.generate_function_comment(fn)
        comment_count += 1

    for i, s in enumerate(file_info.structs):
        file_comments["structs"][i] = commentator.generate_struct_comment(s)
        comment_count += 1

    for i, e in enumerate(file_info.enums):
        file_comments["enums"][i] = commentator.generate_enum_comment(e)
        comment_count += 1

    for i, m in enumerate(file_info.macros):
        file_comments["macros"][i] = commentator.generate_macro_comment(m)
        comment_count += 1

    for i, g in enumerate(file_info.globals):
        file_comments["globals"][i] = commentator.generate_global_comment(g)
        comment_count += 1

    result = writer.insert_comments(original_source, file_info, file_comments)
    result = writer.insert_file_header(result, file_comment)

    with open(file_path, "w", encoding=encoding) as f:
        f.write(result)

    return file_info, comment_count


def main():
    arg_parser = argparse.ArgumentParser(description="C/C++ Doxygen 注释生成器")
    arg_parser.add_argument("path", nargs="?", default=".", help="要处理的目录或文件路径")
    arg_parser.add_argument("--export", choices=["html", "md", "json", "all"],
                           help="仅导出文档格式（跳过注释生成）")
    arg_parser.add_argument("--project-name", default="API", help="项目名称")
    arg_parser.add_argument("--output", default="docs/api", help="文档输出目录")

    args = arg_parser.parse_args()

    if not os.path.exists(args.path):
        print(f"错误: 路径不存在: {args.path}")
        sys.exit(1)

    c_parser = CParser()
    commentator = DoxygenCommentator()
    writer = CommentWriter()
    exporter = DocExporter()

    c_files = find_c_files(args.path)
    if not c_files:
        print("未找到 C/C++ 文件")
        sys.exit(0)

    print(f"扫描到 {len(c_files)} 个文件\n")

    if args.export:
        project = ProjectInfo(project_name=args.project_name)
        for fp in c_files:
            file_info = c_parser.parse_file(fp)
            enc = detect_encoding(fp)
            _extract_existing_comments(
                open(fp, encoding=enc, errors="replace").read(), file_info
            )
            project.files.append(file_info)

        templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "templates", "html")

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

    project = ProjectInfo(project_name=args.project_name)
    total_comments = 0

    for fp in c_files:
        print(f"  处理: {fp}")
        file_info, count = generate_comments_for_file(fp, c_parser, commentator, writer)
        project.files.append(file_info)
        total_comments += count
        print(f"    → 生成 {count} 个注释")

    print(f"\n完成: 处理 {len(c_files)} 个文件，生成 {total_comments} 个注释")

    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "templates", "html")
    os.makedirs(args.output, exist_ok=True)
    exporter.export_json(project, os.path.join(args.output, "api.json"))
    exporter.export_markdown(project, args.output)
    exporter.export_html(project, args.output, templates_dir=templates_dir)
    print(f"文档已导出到 {args.output}/")


if __name__ == "__main__":
    main()
