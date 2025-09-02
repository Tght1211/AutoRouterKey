#!/bin/bash

# macOS Outlook注册机安装脚本
# 作者: Claude
# 适用于: macOS 系统

echo "🍎 开始在macOS上安装Outlook注册机..."

# 检查Python版本
python_version=$(python3 --version 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ 发现Python: $python_version"
else
    echo "❌ 错误: 需要安装Python 3.7+。请访问 https://python.org 下载安装。"
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ 错误: pip3 未找到。请确保Python安装正确。"
    exit 1
fi

# 创建虚拟环境（推荐）
echo "📦 创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 升级pip
echo "⬆️  升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📚 安装Python依赖包..."
pip install -r requirements.txt

# 安装Playwright浏览器
echo "🌐 安装Playwright浏览器..."
playwright install chromium

# 检查是否有Chrome或Edge浏览器
echo "🔍 检查系统浏览器..."
chrome_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
edge_path="/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"

if [ -f "$chrome_path" ]; then
    echo "✅ 发现 Google Chrome: $chrome_path"
elif [ -f "$edge_path" ]; then
    echo "✅ 发现 Microsoft Edge: $edge_path"
else
    echo "⚠️  警告: 未找到Chrome或Edge浏览器。建议安装以获得更好的兼容性。"
    echo "   Chrome下载: https://www.google.com/chrome/"
    echo "   Edge下载: https://www.microsoft.com/edge"
fi

# 检查代理设置
echo "🔧 检查网络设置..."
if command -v networksetup &> /dev/null; then
    proxy_info=$(networksetup -getwebproxy "Wi-Fi" 2>/dev/null)
    if echo "$proxy_info" | grep -q "Enabled: Yes"; then
        echo "📡 检测到系统代理设置，可能需要在config.json中配置相应代理。"
    fi
fi

echo ""
echo "🎉 安装完成！"
echo ""
echo "📋 使用说明:"
echo "1. 配置 config.json 文件（代理、浏览器路径等）"
echo "2. 激活虚拟环境: source venv/bin/activate"
echo "3. 运行程序: python3 OutlookRegister.py"
echo ""
echo "💡 提示:"
echo "- 浏览器路径可留空，程序会自动检测"
echo "- 确保代理服务器正常运行"
echo "- 建议使用高质量IP和指纹浏览器"
echo ""
echo "❓ 如有问题，请检查终端输出的错误信息。"
