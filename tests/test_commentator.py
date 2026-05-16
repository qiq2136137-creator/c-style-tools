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
