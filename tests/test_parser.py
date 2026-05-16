"""parser.py 单元测试"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'docs', 'superpowers', 'skills', 'doxygen-doc', 'scripts'))

from parser import CParser


def test_parse_simple_function():
    code = b'int add(int a, int b) {\n    return a + b;\n}\n'
    parser = CParser()
    result = parser.parse(code, "test.c")
    assert len(result.functions) == 1
    fn = result.functions[0]
    assert fn.name == "add"
    assert fn.return_type == "int"
    assert len(fn.params) == 2
    assert fn.params[0].name == "a"
    assert fn.params[0].type == "int"
    assert fn.params[1].name == "b"
    assert fn.params[1].type == "int"


def test_parse_struct():
    code = b'typedef struct {\n    uint8_t brightness;\n    uint8_t mode;\n} Config_t;\n'
    parser = CParser()
    result = parser.parse(code, "test.c")
    assert len(result.structs) == 1
    s = result.structs[0]
    assert s.name == "Config_t"
    assert len(s.fields) == 2
    assert s.fields[0].name == "brightness"
    assert s.fields[0].type == "uint8_t"


def test_parse_enum():
    code = b'typedef enum {\n    MODE_OFF = 0,\n    MODE_ON = 1\n} Mode_t;\n'
    parser = CParser()
    result = parser.parse(code, "test.c")
    assert len(result.enums) == 1
    e = result.enums[0]
    assert e.name == "Mode_t"
    assert len(e.values) == 2
    assert e.values[0].name == "MODE_OFF"
    assert e.values[0].value == "0"


def test_parse_macro():
    code = b'#define MAX(a, b) ((a) > (b) ? (a) : (b))\n#define BUFFER_SIZE 1024\n'
    parser = CParser()
    result = parser.parse(code, "test.c")
    assert len(result.macros) == 2
    m0 = result.macros[0]
    assert m0.name == "MAX"
    assert m0.is_function_like is True
    assert m0.params == ["a", "b"]
    m1 = result.macros[1]
    assert m1.name == "BUFFER_SIZE"
    assert m1.is_function_like is False


def test_parse_global_variable():
    code = b'extern uint32_t g_tick_count;\nstatic int g_config_value = 42;\n'
    parser = CParser()
    result = parser.parse(code, "test.c")
    assert len(result.globals) == 2
    assert result.globals[0].name == "g_tick_count"
    assert result.globals[0].is_extern is True
    assert result.globals[1].name == "g_config_value"


def test_parse_void_function():
    code = b'void led_init(void) {\n    // do nothing\n}\n'
    parser = CParser()
    result = parser.parse(code, "test.c")
    assert len(result.functions) == 1
    fn = result.functions[0]
    assert fn.name == "led_init"
    assert fn.return_type == "void"
    assert len(fn.params) == 0


def test_parse_function_with_pointer_param():
    code = b'int process(Config_t* cfg, uint8_t* buf) { return 0; }\n'
    parser = CParser()
    result = parser.parse(code, "test.c")
    fn = result.functions[0]
    assert fn.params[0].type == "Config_t *"
    assert fn.params[1].type == "uint8_t *"


def test_parse_named_struct():
    code = b'struct Point {\n    int x;\n    int y;\n};\n'
    parser = CParser()
    result = parser.parse(code, "test.c")
    assert len(result.structs) == 1
    assert result.structs[0].name == "Point"
    assert result.structs[0].kind == "struct"
