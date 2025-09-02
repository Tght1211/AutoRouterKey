# OutlookRegister 🍎 macOS版

Outlook 自动注册机 - 已完全适配macOS系统  
不保证可用性，自行测试。 

## ✨ 主要功能

1. 🤖 模拟人类填表操作  
2. 🔐 自动过验证码  
3. ✅ 注册成功（长效账号）
4. 🍎 完全支持macOS系统
5. 🔍 自动检测浏览器路径

## 🚀 快速开始

### 安装依赖（推荐方式）

```bash
# 运行自动安装脚本
./install_macos.sh
```

### 手动安装

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装Playwright浏览器
playwright install chromium
```

## ⚙️ 配置设置

在 `config.json` 中进行配置：

1. **浏览器路径** - 可留空，程序会自动检测macOS上的Chrome/Edge
2. **代理设置** - 填写你的代理服务器地址
3. **OAuth2** - 如需要，设置 `"enable_oauth2": true` 并填写相关参数
4. **浏览器关闭控制** - 设置 `"close_browser_after_registration": false` 可在注册完成后保持浏览器开启状态
5. **并发注册控制** - 设置 `"concurrent_flows"` 控制并发注册数量，`"max_tasks"` 控制总注册数量

### macOS 浏览器自动检测路径：
- `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- `/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge`
- `/Applications/Chromium.app/Contents/MacOS/Chromium`

## 📁 输出文件

注册成功的账号会自动保存到 `Results/` 目录：
- `logged_email.txt` - 启用OAuth2时的账号
- `unlogged_email.txt` - 普通注册账号  
- `outlook_token.txt` - OAuth2令牌信息

## 🎯 使用方法

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行程序
python3 OutlookRegister.py
```

## ⚠️ 注意事项

- 选用高质量的**IP**与**浏览器**，否则可能过不去检测
- 同一IP短时间不宜多次注册
- 建议浏览器能通过 https://www.browserscan.net 检测
- 支持无头模式，但需注意反爬措施
- 高并发建议使用协议方式

## 🔧 系统要求

- **操作系统**: macOS 10.14+ 
- **Python**: 3.7+
- **浏览器**: Chrome 或 Edge（可自动检测）
- **网络**: 稳定的代理服务器

## 📋 更新日志

### v2.0 - macOS优化版
- ✅ 完全适配macOS系统
- ✅ 自动浏览器检测
- ✅ 跨平台路径处理
- ✅ 改进错误处理
- ✅ 安装脚本支持

---

💡 **提示**: 该项目已针对macOS全面优化，如遇问题请检查终端输出信息。