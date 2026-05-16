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
