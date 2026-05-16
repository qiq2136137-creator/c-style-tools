"""exporter.py 单元测试"""
import sys
import os
import json
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
    assert data["files"][0]["functions"][0]["brief"] == "计算两数之和"
    assert data["files"][0]["structs"][0]["name"] == "Config_t"
    assert data["files"][0]["enums"][0]["name"] == "Mode_t"


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
    assert "### add" in content
    assert "计算两数之和" in content
    assert "| a | `int` | 加数 |" in content
    assert "### Config_t" in content
    assert "配置结构体" in content


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
    assert "计算两数之和" in content
