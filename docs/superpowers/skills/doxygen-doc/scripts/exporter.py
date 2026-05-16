"""API 文档导出器"""
import json
import os

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

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def export_markdown(self, project: ProjectInfo, output_dir: str):
        """导出为 Markdown 格式"""
        os.makedirs(output_dir, exist_ok=True)

        lines = ["# API 文档\n"]
        lines.append(f"项目: **{project.project_name}**\n")
        lines.append(f"生成时间: {project.generated_at}\n")

        for fi in project.files:
            lines.append(f"\n---\n\n## {os.path.basename(fi.path)}\n")
            if fi.file_brief:
                lines.append(f"> {fi.file_brief}\n")

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

            if fi.structs:
                lines.append("\n### 结构体\n")
                for s in fi.structs:
                    lines.append(f"\n#### {s.name}\n")
                    if s.brief:
                        lines.append(f"\n> {s.brief}\n")

                    if s.fields:
                        lines.append("\n| 字段 | 类型 | 说明 |")
                        lines.append("|------|------|------|")
                        for f in s.fields:
                            brief = f.brief if f.brief else ""
                            lines.append(f"| {f.name} | `{f.type}` | {brief} |")

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

            if fi.macros:
                lines.append("\n### 宏定义\n")
                for m in fi.macros:
                    lines.append(f"\n#### {m.name}\n")
                    if m.brief:
                        lines.append(f"\n> {m.brief}\n")
                    if m.is_function_like:
                        lines.append(f"\n函数式宏，参数: {', '.join(m.params)}\n")

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

    def export_html(self, project: ProjectInfo, output_dir: str, templates_dir: str):
        """导出为 Docusaurus 风格 HTML"""
        import shutil
        from jinja2 import Environment, FileSystemLoader

        os.makedirs(output_dir, exist_ok=True)

        for asset in ("style.css", "script.js"):
            src = os.path.join(templates_dir, asset)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(output_dir, asset))

        env = Environment(loader=FileSystemLoader(templates_dir))
        env.filters['basename'] = os.path.basename

        template = env.get_template("base.html")
        html = template.render(project=project)

        with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
