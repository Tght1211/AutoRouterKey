#!/bin/bash
# AutoRouterKey Web 管理平台启动脚本

echo "🚀 启动 AutoRouterKey Web 管理平台..."

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"
else
    echo "⚠️  未检测到虚拟环境，尝试激活..."
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "✅ 虚拟环境已激活"
    else
        echo "❌ 未找到虚拟环境，请先运行 ./install.sh"
        exit 1
    fi
fi

# 检查依赖
echo "🔍 检查依赖..."
python3 -c "import flask, flask_cors" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Flask 依赖已安装"
else
    echo "📦 安装缺失的依赖..."
    pip install flask flask-cors
fi

# 检查账号文件
echo "📄 检查账号文件..."
if [ ! -d "data/results" ]; then
    echo "📁 创建 data/results 目录..."
    mkdir -p data/results
fi

if [ ! -f "data/accounts.json" ]; then
    echo "⚠️  未找到 data/accounts.json 文件"
    echo "💡 请先运行注册程序生成账号数据"
else
    account_count=$(python3 -c "import json; data=json.load(open('data/accounts.json')); print(len(data.get('accounts', [])))" 2>/dev/null || echo "未知")
    echo "✅ 发现账号数据文件，共 $account_count 个账号"
fi

# 启动服务器
echo "🌐 启动 Web 服务器..."
echo "📍 管理界面: http://localhost:5010"
echo "📍 按 Ctrl+C 停止服务器"
echo ""

python3 main.py web
