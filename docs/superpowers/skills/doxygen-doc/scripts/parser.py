"""tree-sitter C/C++ 代码解析器"""
import tree_sitter_c
from tree_sitter import Language, Parser

from models import (
    FileInfo, FunctionInfo, Param, StructInfo, FieldInfo,
    EnumInfo, EnumValue, MacroInfo, GlobalVarInfo
)


def _get_text(node, source_code: bytes) -> str:
    """从 AST 节点提取源码文本"""
    return source_code[node.start_byte:node.end_byte].decode("utf-8", errors="replace").strip()


def _find_child(node, type_name: str):
    """查找指定类型的子节点"""
    for child in node.children:
        if child.type == type_name:
            return child
    return None


def _find_type_node(node):
    """查找类型节点 (primitive_type, type_identifier, sized_type_specifier 等)"""
    type_names = ("primitive_type", "type_identifier", "sized_type_specifier",
                  "struct_specifier", "union_specifier", "enum_specifier")
    for child in node.children:
        if child.type in type_names:
            return child
    return None


def _find_all_children(node, type_name: str):
    """查找所有指定类型的子节点"""
    return [c for c in node.children if c.type == type_name]


class CParser:
    """C 语言代码解析器"""

    def __init__(self):
        self.language = Language(tree_sitter_c.language())
        self.parser = Parser(self.language)

    def parse(self, source_code: bytes, file_path: str = "") -> FileInfo:
        """解析 C 源码，提取所有代码元素"""
        tree = self.parser.parse(source_code)
        root = tree.root_node

        file_info = FileInfo(path=file_path)

        for child in root.children:
            if child.type == "function_definition":
                fn = self._parse_function(child, source_code)
                if fn:
                    file_info.functions.append(fn)

            elif child.type in ("struct_specifier", "union_specifier"):
                s = self._parse_struct(child, source_code)
                if s:
                    file_info.structs.append(s)

            elif child.type == "type_definition":
                result = self._parse_typedef(child, source_code)
                if result:
                    if isinstance(result, StructInfo):
                        file_info.structs.append(result)
                    elif isinstance(result, EnumInfo):
                        file_info.enums.append(result)

            elif child.type == "enum_specifier":
                e = self._parse_enum(child, source_code)
                if e:
                    file_info.enums.append(e)

            elif child.type == "preproc_def":
                m = self._parse_preproc_def(child, source_code, is_function_like=False)
                if m:
                    file_info.macros.append(m)

            elif child.type == "preproc_function_def":
                m = self._parse_preproc_def(child, source_code, is_function_like=True)
                if m:
                    file_info.macros.append(m)

            elif child.type == "declaration":
                g = self._parse_global_var(child, source_code)
                if g:
                    file_info.globals.append(g)

        return file_info

    def _parse_function(self, node, src: bytes) -> FunctionInfo | None:
        """解析函数定义"""
        type_node = _find_type_node(node)
        declarator = _find_child(node, "declarator") or _find_child(node, "function_declarator")
        if not declarator:
            return None

        # 处理指针声明器: int *foo(...)
        while declarator.type in ("pointer_declarator", "parenthesized_declarator"):
            inner = _find_child(declarator, "pointer_declarator") or \
                    _find_child(declarator, "parenthesized_declarator") or \
                    _find_child(declarator, "function_declarator") or \
                    _find_child(declarator, "identifier") or \
                    _find_child(declarator, "field_identifier")
            if inner and inner.type in ("pointer_declarator", "parenthesized_declarator"):
                declarator = inner
            else:
                break

        if declarator.type != "function_declarator":
            return None

        name_node = _find_child(declarator, "identifier") or _find_child(declarator, "field_identifier")
        if not name_node:
            return None
        fn_name = _get_text(name_node, src)

        return_type = ""
        if type_node:
            return_type = _get_text(type_node, src)

        params_node = _find_child(declarator, "parameter_list")
        params = []
        if params_node:
            for param_decl in _find_all_children(params_node, "parameter_declaration"):
                p_type_node = _find_type_node(param_decl)
                p_name_node = _find_child(param_decl, "pointer_declarator") or \
                              _find_child(param_decl, "declarator") or \
                              _find_child(param_decl, "abstract_declarator") or \
                              _find_child(param_decl, "identifier")

                p_type = _get_text(p_type_node, src) if p_type_node else ""
                p_name = ""

                if p_name_node:
                    if p_name_node.type == "pointer_declarator":
                        p_type += " *"
                        inner = _find_child(p_name_node, "identifier") or _find_child(p_name_node, "declarator")
                        if inner:
                            p_name = _get_text(inner, src)
                    elif p_name_node.type in ("identifier", "field_identifier"):
                        p_name = _get_text(p_name_node, src)
                    else:
                        p_name = _get_text(p_name_node, src)

                if p_type == "void" and not p_name:
                    continue

                params.append(Param(name=p_name, type=p_type))

        return FunctionInfo(
            name=fn_name,
            return_type=return_type,
            params=params,
            line_number=node.start_point[0] + 1
        )

    def _parse_struct(self, node, src: bytes) -> StructInfo | None:
        """解析结构体/联合体"""
        kind = "struct" if node.type == "struct_specifier" else "union"

        name = ""
        name_node = _find_child(node, "type_identifier")
        if name_node:
            name = _get_text(name_node, src)

        body = _find_child(node, "field_declaration_list")
        fields = []
        if body:
            for field_decl in _find_all_children(body, "field_declaration"):
                f_type_node = _find_type_node(field_decl)
                f_name_node = _find_child(field_decl, "field_identifier") or _find_child(field_decl, "declarator")

                f_type = _get_text(f_type_node, src) if f_type_node else ""
                f_name = _get_text(f_name_node, src) if f_name_node else ""

                if f_name:
                    fields.append(FieldInfo(name=f_name, type=f_type))

        if not name and not fields:
            return None

        return StructInfo(
            name=name,
            kind=kind,
            fields=fields,
            line_number=node.start_point[0] + 1
        )

    def _parse_typedef(self, node, src: bytes) -> StructInfo | EnumInfo | None:
        """解析 typedef，可能包含结构体或枚举"""
        struct_node = _find_child(node, "struct_specifier") or _find_child(node, "union_specifier")
        enum_node = _find_child(node, "enum_specifier")

        type_def_name = ""
        declarator = _find_child(node, "declarator") or _find_child(node, "type_identifier")
        if declarator:
            type_def_name = _get_text(declarator, src)

        if struct_node:
            s = self._parse_struct(struct_node, src)
            if s and type_def_name:
                s.name = type_def_name
            return s

        if enum_node:
            e = self._parse_enum(enum_node, src)
            if e and type_def_name:
                e.name = type_def_name
            return e

        return None

    def _parse_enum(self, node, src: bytes) -> EnumInfo | None:
        """解析枚举"""
        name = ""
        name_node = _find_child(node, "type_identifier")
        if name_node:
            name = _get_text(name_node, src)

        body = _find_child(node, "enumerator_list")
        values = []
        if body:
            for enum_val in _find_all_children(body, "enumerator"):
                val_name_node = _find_child(enum_val, "name") or _find_child(enum_val, "identifier")
                val_value_node = _find_child(enum_val, "number_literal") or \
                                _find_child(enum_val, "unary_expression") or \
                                _find_child(enum_val, "identifier")

                val_name = _get_text(val_name_node, src) if val_name_node else ""
                val_value = _get_text(val_value_node, src) if val_value_node else None

                if val_name:
                    values.append(EnumValue(name=val_name, value=val_value))

        return EnumInfo(
            name=name,
            values=values,
            line_number=node.start_point[0] + 1
        )

    def _parse_preproc_def(self, node, src: bytes, is_function_like: bool = False) -> MacroInfo | None:
        """解析 #define 宏"""
        name_node = _find_child(node, "identifier")
        if not name_node:
            return None
        name = _get_text(name_node, src)

        params = []
        if is_function_like:
            for child in node.children:
                if child.type == "preproc_params":
                    for param in _find_all_children(child, "identifier"):
                        params.append(_get_text(param, src))
                    break

        return MacroInfo(
            name=name,
            is_function_like=is_function_like,
            params=params,
            line_number=node.start_point[0] + 1
        )

    def _parse_global_var(self, node, src: bytes) -> GlobalVarInfo | None:
        """解析全局变量声明"""
        type_node = _find_type_node(node)
        if not type_node:
            return None

        # 查找声明器：可能在 init_declarator, identifier, pointer_declarator 中
        declarator = _find_child(node, "init_declarator") or \
                     _find_child(node, "declarator")

        # 如果没有 declarator 子节点，直接找 identifier
        if not declarator:
            id_node = _find_child(node, "identifier")
            if id_node and type_node:
                is_extern = False
                for child in node.children:
                    if child.type == "storage_class_specifier" and _get_text(child, src) == "extern":
                        is_extern = True
                        break
                return GlobalVarInfo(
                    name=_get_text(id_node, src),
                    type=_get_text(type_node, src),
                    is_extern=is_extern,
                    line_number=node.start_point[0] + 1
                )
            return None

        if declarator.type == "function_declarator":
            return None

        is_extern = False
        for child in node.children:
            if child.type == "storage_class_specifier" and _get_text(child, src) == "extern":
                is_extern = True
                break

        var_name = ""
        var_type = _get_text(type_node, src)

        if declarator.type == "init_declarator":
            name_node = _find_child(declarator, "identifier") or _find_child(declarator, "declarator")
            if name_node:
                if name_node.type == "pointer_declarator":
                    var_type += " *"
                    inner = _find_child(name_node, "identifier")
                    if inner:
                        var_name = _get_text(inner, src)
                else:
                    var_name = _get_text(name_node, src)
        elif declarator.type == "identifier":
            var_name = _get_text(declarator, src)
        elif declarator.type == "pointer_declarator":
            var_type += " *"
            inner = _find_child(declarator, "identifier")
            if inner:
                var_name = _get_text(inner, src)

        if not var_name:
            return None

        return GlobalVarInfo(
            name=var_name,
            type=var_type,
            is_extern=is_extern,
            line_number=node.start_point[0] + 1
        )

    def parse_file(self, file_path: str) -> FileInfo:
        """解析文件"""
        with open(file_path, "rb") as f:
            source_code = f.read()
        return self.parse(source_code, file_path)
