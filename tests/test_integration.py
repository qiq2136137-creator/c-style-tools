"""集成测试 — 端到端流程"""
import sys
import os
import tempfile
import re
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
        src_file = os.path.join(tmpdir, "test.c")
        with open(src_file, "w") as f:
            f.write(SAMPLE_C_FILE)

        parser = CParser()
        file_info = parser.parse_file(src_file)
        assert len(file_info.functions) == 1
        assert len(file_info.structs) == 1
        assert len(file_info.enums) == 1
        assert len(file_info.macros) == 2
        assert len(file_info.globals) == 1

        with open(src_file, encoding="utf-8") as f:
            source = f.read()

        for fn in file_info.functions:
            match = re.search(r'//\s*(.*)', source)
            if match:
                fn.has_existing_comment = True
                fn.existing_comment_text = match.group(1).strip()

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

        result = writer.insert_comments(source, file_info, file_comments)
        result = writer.insert_file_header(result, commentator.generate_file_comment(src_file))

        with open(src_file, "w") as f:
            f.write(result)

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


def test_cli_main():
    """测试 CLI 主入口"""
    import subprocess

    script = os.path.join(
        os.path.dirname(__file__), '..', 'docs', 'superpowers', 'skills',
        'doxygen-doc', 'scripts', 'doxygen_generator.py'
    )
    script = os.path.abspath(script)

    with tempfile.TemporaryDirectory() as tmpdir:
        src_file = os.path.join(tmpdir, "test.c")
        with open(src_file, "w") as f:
            f.write(SAMPLE_C_FILE)

        out_dir = os.path.join(tmpdir, "api")
        result = subprocess.run(
            [sys.executable, script, src_file, "--output", out_dir],
            capture_output=True, text=True, encoding="utf-8"
        )

        assert result.returncode == 0
        assert "生成" in result.stdout
        assert os.path.exists(os.path.join(out_dir, "api.json"))
        assert os.path.exists(os.path.join(out_dir, "index.md"))
        assert os.path.exists(os.path.join(out_dir, "index.html"))
