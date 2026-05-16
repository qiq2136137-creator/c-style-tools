#!/bin/bash
# Doxygen Doc 技能安装脚本

echo "安装 Doxygen Doc 依赖..."
pip install tree-sitter tree-sitter-c Jinja2

echo "依赖安装完成！"
echo ""
echo "使用方法："
echo "  python docs/superpowers/skills/doxygen-doc/scripts/doxygen_generator.py [目录]"
echo "  python docs/superpowers/skills/doxygen-doc/scripts/doxygen_generator.py --export html"
