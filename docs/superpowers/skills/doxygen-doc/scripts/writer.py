"""注释写入器 — 将生成的注释插入源文件"""
import re

from models import FileInfo


class CommentWriter:
    """将 Doxygen 注释写入源文件"""

    def insert_comments(
        self,
        source: str,
        file_info: FileInfo,
        file_comments: dict | None = None
    ) -> str:
        """将注释插入到对应代码元素上方"""
        if file_comments is None:
            return source

        lines = source.split('\n')
        insertions = []

        for i, fn in enumerate(file_info.functions):
            if "functions" in file_comments and i in file_comments["functions"]:
                comment = file_comments["functions"][i]
                line_idx = fn.line_number - 1
                if line_idx < len(lines):
                    insertions.append((line_idx, comment))

        for i, s in enumerate(file_info.structs):
            if "structs" in file_comments and i in file_comments["structs"]:
                comment = file_comments["structs"][i]
                line_idx = s.line_number - 1
                if line_idx < len(lines):
                    insertions.append((line_idx, comment))

        for i, e in enumerate(file_info.enums):
            if "enums" in file_comments and i in file_comments["enums"]:
                comment = file_comments["enums"][i]
                line_idx = e.line_number - 1
                if line_idx < len(lines):
                    insertions.append((line_idx, comment))

        for i, m in enumerate(file_info.macros):
            if "macros" in file_comments and i in file_comments["macros"]:
                comment = file_comments["macros"][i]
                line_idx = m.line_number - 1
                if line_idx < len(lines):
                    insertions.append((line_idx, comment))

        for i, g in enumerate(file_info.globals):
            if "globals" in file_comments and i in file_comments["globals"]:
                comment = file_comments["globals"][i]
                line_idx = g.line_number - 1
                if line_idx < len(lines):
                    insertions.append((line_idx, comment))

        # 从后往前插入，避免行号偏移
        insertions.sort(key=lambda x: x[0], reverse=True)

        for line_idx, comment in insertions:
            indent = ""
            if line_idx < len(lines):
                match = re.match(r'^(\s*)', lines[line_idx])
                if match:
                    indent = match.group(1)

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
        if source.lstrip().startswith('/**') and '@file' in source[:200]:
            return source

        return file_comment + "\n" + source

    def _has_comment_above(self, lines: list[str], line_idx: int) -> bool:
        """检查指定行上方是否已有 Doxygen 注释"""
        if line_idx == 0:
            return False

        check_idx = line_idx - 1
        while check_idx >= 0 and not lines[check_idx].strip():
            check_idx -= 1

        if check_idx < 0:
            return False

        if lines[check_idx].strip().endswith("*/"):
            return True

        return False
