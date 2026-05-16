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
