#!/bin/bash

# macOS Outlook注册机运行脚本
# 作者: Claude
# 适用于: macOS 系统

echo "🍎 启动 macOS Outlook 注册机..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 错误: 虚拟环境不存在。请先运行 ./install_macos.sh 进行安装。"
    exit 1
fi

# 激活虚拟环境
echo "📦 激活虚拟环境..."
source venv/bin/activate

# 检查配置文件
if [ ! -f "config.json" ]; then
    echo "❌ 错误: config.json 配置文件不存在。"
    exit 1
fi

# 检查Results目录
if [ ! -d "Results" ]; then
    echo "📁 创建Results目录..."
    mkdir -p Results
fi

# 显示系统信息
echo "🔍 系统信息:"
echo "   操作系统: $(uname -s) $(uname -r)"
echo "   Python版本: $(python --version 2>/dev/null || python3 --version)"

# 检查浏览器
echo "🌐 检查浏览器:"
chrome_path="/Applications/Google Chrome.app"
edge_path="/Applications/Microsoft Edge.app"

if [ -d "$chrome_path" ]; then
    echo "   ✅ Google Chrome 已安装"
elif [ -d "$edge_path" ]; then
    echo "   ✅ Microsoft Edge 已安装"
else
    echo "   ⚠️  未检测到Chrome或Edge，将使用Playwright自带浏览器"
fi

# 检查网络连接
echo "📡 检查网络连接..."
if ping -c 1 google.com &> /dev/null; then
    echo "   ✅ 网络连接正常"
else
    echo "   ⚠️  网络连接可能有问题，请检查代理设置"
fi

echo ""
echo "🚀 开始运行注册程序..."
echo "   提示: 按 Ctrl+C 可以停止程序"
echo ""

# 运行主程序
python OutlookRegister.py

# 显示结果
echo ""
echo "📊 运行完成！"
if [ -f "Results/logged_email.txt" ] || [ -f "Results/unlogged_email.txt" ]; then
    echo "📁 结果文件保存在 Results/ 目录中:"
    ls -la Results/
else
    echo "⚠️  未发现输出文件，请检查程序运行日志"
fi

echo ""
echo "💡 如需再次运行，请执行: ./run_macos.sh"
