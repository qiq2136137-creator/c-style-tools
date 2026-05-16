"""writer.py 单元测试"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'docs', 'superpowers', 'skills', 'doxygen-doc', 'scripts'))

from writer import CommentWriter
from parser import CParser
from commentator import DoxygenCommentator


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
    source = '/**\n * @brief existing comment\n * @param x\n */\nvoid foo(int x) {}\n'
    parser = CParser()
    file_info = parser.parse(source.encode(), "test.c")

    writer = CommentWriter()
    result = writer.insert_comments(source, file_info)

    assert "existing comment" in result
