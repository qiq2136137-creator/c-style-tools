#!/bin/bash
# style-tool 安装脚本
# 用法: bash install.sh [目标项目目录]

TARGET="${1:-.}"

echo "安装 style-tool..."

# 1. 复制到目标项目
if [ ! -d "$TARGET/style-tool" ]; then
    cp -r "$(dirname "$0")" "$TARGET/style-tool"
    echo "  ✓ 已复制到 $TARGET/style-tool/"
else
    echo "  ⚠ $TARGET/style-tool/ 已存在，跳过复制"
fi

# 2. 安装 Python 依赖
pip install tree-sitter tree-sitter-c chardet -q
echo "  ✓ Python 依赖已安装"

echo ""
echo "安装完成！用法:"
echo "  python style-tool/scripts/style_tool.py <文件/目录> --mode all"
echo ""
echo "在 Claude Code 中使用 /style-tool 调用"
