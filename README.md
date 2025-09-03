# OutlookRegister 🍎 macOS版 - 重构版

Outlook 自动注册机 - 已完全适配macOS系统，采用模块化架构设计  
不保证可用性，自行测试。 

## 📁 项目结构

```
outlookregister/
├── main.py                     # 主入口文件，统一命令行界面
├── requirements.txt            # 依赖包列表
├── README.md                   # 原始说明文档
├── README_NEW.md              # 新版说明文档（本文件）
├── 
├── src/                       # 源代码目录
│   ├── __init__.py
│   ├── core/                  # 核心功能模块
│   │   ├── __init__.py
│   │   ├── register.py        # 账号注册功能 (原 OutlookRegister.py)
│   │   └── oauth.py           # OAuth2认证 (原 get_token.py)
│   ├── monitor/               # 邮件监听模块
│   │   ├── __init__.py
│   │   ├── imap_monitor.py    # IMAP邮件监听 (原 email_monitor.py)
│   │   └── graph_monitor.py   # Graph API监听 (原 graph_email_monitor.py)
│   ├── web/                   # Web界面模块
│   │   ├── __init__.py
│   │   ├── server.py          # Flask服务器 (原 account_server.py)
│   │   └── templates/
│   │       └── manager.html   # 管理界面 (原 account_manager.html)
│   └── utils/                 # 工具模块
│       ├── __init__.py
│       └── system_check.py    # 系统检查 (原 check_system.py)
├── 
├── config/                    # 配置文件目录
│   ├── app.json              # 应用主配置 (原 config/app.json)
│   ├── imap_monitor.json     # IMAP监听配置 (原 email_monitor_config.json)
│   └── graph_monitor.json    # Graph监听配置 (原 graph_monitor_config.json)
├── 
├── scripts/                   # 脚本文件目录
│   ├── install.sh            # 安装脚本 (原 install_macos.sh)
│   ├── run.sh                # 运行脚本 (原 run_macos.sh)
│   └── start_manager.sh      # 管理器启动脚本
├── 
├── data/                      # 数据存储目录
│   └── results/              # 结果文件 (原 Results/)
│       ├── accounts_data.json
│       ├── logged_email.txt
│       ├── unlogged_email.txt
│       └── outlook_token.txt
├── 
├── docs/                      # 文档目录
│   ├── 账号管理器使用说明.md
│   └── 邮件监听使用说明.md
├── 
├── venv/                      # 虚拟环境 (创建后)
└── *.log                      # 日志文件
```

## ✨ 重构优势

### 🎯 模块化设计
- **清晰的功能分离**: 每个模块职责明确，便于维护
- **标准Python包结构**: 遵循Python项目最佳实践
- **可扩展架构**: 易于添加新功能和模块

### 📦 统一入口
- **单一命令行界面**: 通过 `main.py` 访问所有功能
- **参数化配置**: 支持命令行参数自定义运行方式
- **一致的使用体验**: 所有功能都有统一的调用方式

### 🔧 配置管理
- **集中配置存储**: 所有配置文件统一放在 `config/` 目录
- **分类配置文件**: 不同功能的配置独立管理
- **数据与代码分离**: 数据文件统一存储在 `data/` 目录

## 🚀 快速开始

### 安装依赖（推荐方式）

```bash
# 运行自动安装脚本
./scripts/install.sh
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

## 🎯 使用方法

### 统一命令行界面

```bash
# 查看帮助
python3 main.py --help

# 启动账号注册
python3 main.py register

# 启动账号注册（自定义参数）
python3 main.py register --concurrent 2 --max-tasks 5

# 启动Web管理界面
python3 main.py web

# 启动Web界面（自定义端口）
python3 main.py web --port 8080 --debug

# 启动IMAP邮件监听
python3 main.py monitor imap

# 启动Graph API邮件监听
python3 main.py monitor graph

# 系统检查
python3 main.py check
```

### 快速启动脚本

```bash
# 启动Web管理界面
./scripts/start_manager.sh

# 运行账号注册
./scripts/run.sh
```

## ⚙️ 配置设置

配置文件现在统一存放在 `config/` 目录下：

### 主应用配置 (`config/app.json`)
- 浏览器设置
- 代理配置  
- OAuth2设置
- 注册参数

### 邮件监听配置
- IMAP监听: `config/imap_monitor.json`
- Graph API监听: `config/graph_monitor.json`

## 📁 数据文件

所有数据文件统一存储在 `data/results/` 目录：
- `unlogged_email.txt` - 普通注册账号
- `logged_email.txt` - OAuth2账号  
- `outlook_token.txt` - OAuth2令牌
- `accounts_data.json` - 账号元数据

## 🔄 兼容性说明

### 向后兼容
- 所有原有功能保持不变
- 数据文件格式完全兼容
- 配置文件内容保持一致（仅路径调整）

### 迁移指南
如果您有现有的数据和配置：

1. **配置文件迁移**:
   - `config/app.json` → `config/app.json`
   - `email_monitor_config.json` → `config/imap_monitor.json`
   - `graph_monitor_config.json` → `config/graph_monitor.json`

2. **数据文件迁移**:
   - `Results/` → `data/results/`
   - `config.json` → `config/app.json`

3. **使用新的启动方式**:
   - 原: `python3 OutlookRegister.py` → 新: `python3 main.py register`
   - 原: `python3 account_server.py` → 新: `python3 main.py web`
   - 原: `./run_macos.sh` → 新: `./scripts/run.sh`

## 🛠️ 开发说明

### 添加新功能
1. 在相应的模块目录下创建新文件
2. 在 `__init__.py` 中导出新功能
3. 在 `main.py` 中添加命令行接口

### 代码结构
- `src/core/` - 核心业务逻辑
- `src/monitor/` - 监听相关功能
- `src/web/` - Web界面相关
- `src/utils/` - 通用工具函数

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

### v2.1 - 架构重构版
- ✅ 模块化项目结构
- ✅ 统一命令行界面
- ✅ 配置文件集中管理
- ✅ 数据文件规范化
- ✅ 向后兼容保证
- ✅ 开发体验优化

### v2.0 - macOS优化版
- ✅ 完全适配macOS系统
- ✅ 自动浏览器检测
- ✅ 跨平台路径处理
- ✅ 改进错误处理
- ✅ 安装脚本支持

---

💡 **提示**: 该项目已采用现代化的模块架构，便于维护和扩展。如遇问题请检查终端输出信息。