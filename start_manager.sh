#!/bin/bash
# Outlook 账号管理器启动脚本

echo "🚀 启动 Outlook 账号管理器..."

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"
else
    echo "⚠️  未检测到虚拟环境，尝试激活..."
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "✅ 虚拟环境已激活"
    else
        echo "❌ 未找到虚拟环境，请先运行 ./install_macos.sh"
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
if [ ! -d "Results" ]; then
    echo "📁 创建 Results 目录..."
    mkdir -p Results
fi

if [ ! -f "Results/unlogged_email.txt" ]; then
    echo "📝 创建示例账号文件..."
    cat > Results/unlogged_email.txt << EOF
nqtfooyhzjxip@outlook.com: HvWKO@HCOns7K
jwzowunvnustc@outlook.com: Zq0ZA16zK!P0
htfcctvg37qmix@outlook.com: pIUd^ee%qV9
cxzuvhnj2irevx@outlook.com: 2dRmB5WoWua*y
pdtbnecorclzb@outlook.com: yXGNdXd8de*M
bhdamuovtd03i@outlook.com: tVDwvQx6w%Og4
mwosoojtxnfz@outlook.com: K6WM^ixzyQGVc
xqpthgatdrckmm@outlook.com: 6Dbg#*fM0Ajdl
EOF
fi

# 启动服务器
echo "🌐 启动 Web 服务器..."
echo "📍 管理界面: http://localhost:5000"
echo "📍 按 Ctrl+C 停止服务器"
echo ""

python3 account_server.py
