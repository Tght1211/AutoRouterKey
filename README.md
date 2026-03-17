# OutlookRegister

Outlook 邮箱自动注册工具，基于 Playwright 浏览器自动化，支持并发注册、OAuth2 认证、Web 管理界面。针对 macOS 优化，采用模块化架构设计。

> **免责声明**：本项目仅供学习和研究用途，请遵守微软服务条款。使用本工具产生的一切后果由使用者自行承担。

## 功能特性

- **自动注册** — 自动填写注册表单，支持验证码按压识别
- **并发执行** — 多浏览器实例并行注册，可配置并发数和任务数
- **OAuth2 认证** — 可选的 OAuth2 令牌获取，支持 Microsoft Graph API
- **反检测** — 隐藏 WebDriver 特征、伪装浏览器指纹、支持无痕模式
- **Web 管理** — 内置 Flask Web 界面，可视化管理账号状态
- **系统检查** — 一键检测运行环境（Python、浏览器、网络、依赖）

## 项目结构

```
OutlookRegister/
├── main.py                          # 统一 CLI 入口
├── requirements.txt                 # Python 依赖
├── config/
│   ├── app.example.json             # 配置文件示例（复制为 app.json 使用）
│   └── app.json                     # 实际配置（已 gitignore）
├── data/
│   ├── accounts.example.json        # 账号数据示例
│   └── accounts.json                # 注册账号数据（已 gitignore）
├── src/
│   ├── core/
│   │   ├── register.py              # 核心注册逻辑
│   │   └── oauth.py                 # OAuth2 认证
│   ├── web/
│   │   ├── server.py                # Flask Web 服务
│   │   └── templates/
│   │       └── manager.html         # 账号管理界面
│   └── utils/
│       └── system_check.py          # 系统环境检查
├── scripts/
│   ├── install.sh                   # 自动安装脚本
│   ├── run.sh                       # 运行注册脚本
│   └── start_manager.sh             # 启动管理界面脚本
└── docs/
    └── 账号管理器使用说明.md
```

## 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | macOS 10.14+（其他系统未经测试） |
| Python | 3.7+ |
| 浏览器 | Chrome 或 Edge（可自动检测，也可留空使用 Playwright 内置浏览器） |
| 网络 | 需要代理服务器（建议使用高质量住宅 IP） |

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/tght/OutlookRegister.git
cd OutlookRegister
```

### 2. 安装依赖

**方式一：使用安装脚本（推荐）**

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

**方式二：手动安装**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 3. 配置

```bash
cp config/app.example.json config/app.json
```

编辑 `config/app.json`，根据你的环境修改以下关键配置：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `browser_path` | 浏览器可执行文件路径，留空自动检测 | `""` |
| `proxy` | 代理地址，支持 http/socks5 | `"http://127.0.0.1:7890"` |
| `concurrent_flows` | 并发浏览器数量 | `2` |
| `max_tasks` | 最大注册任务数 | `4` |
| `use_incognito_mode` | 无痕模式（提高人机验证通过率） | `true` |
| `enable_oauth2` | 注册后自动获取 OAuth2 令牌 | `false` |
| `Bot_protection_wait` | 人机验证等待时间（秒） | `30` |
| `registration_delay` | 连续注册间隔时间（秒） | `60` |
| `close_browser_after_registration` | 注册后关闭浏览器 | `true` |

如需使用 OAuth2 功能，还需配置 `client_id`、`redirect_url` 和 `Scopes`。

### 4. 初始化数据文件

```bash
cp data/accounts.example.json data/accounts.json
```

## 使用方法

### CLI 命令

```bash
# 查看帮助
python3 main.py --help

# 启动账号注册（使用配置文件中的参数）
python3 main.py register

# 自定义并发数和任务数
python3 main.py register --concurrent 3 --max-tasks 10

# 启动 Web 管理界面
python3 main.py web

# 指定端口和调试模式
python3 main.py web --port 8080 --debug

# 系统环境检查
python3 main.py check
```

### 快捷脚本

```bash
# 运行注册
./scripts/run.sh

# 启动 Web 管理界面
./scripts/start_manager.sh
```

## Web 管理界面

启动 Web 服务后访问 `http://localhost:5010`，提供以下功能：

- **账号列表** — 查看所有注册账号的邮箱、密码、状态
- **一键复制** — 快速复制邮箱和密码到剪贴板
- **状态管理** — 标记账号为可用 / 已注册 OpenRouter / 已使用
- **实时搜索** — 按关键词过滤账号
- **数据导出** — 导出账号数据为文本文件
- **统计面板** — 实时显示账号总数和各状态统计

### API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/accounts` | 获取所有账号 |
| PUT | `/api/accounts/{id}/status` | 更新账号状态 |
| PUT | `/api/accounts/{id}/openrouter` | 更新 OpenRouter 状态 |
| PUT | `/api/accounts/{id}/notes` | 更新账号备注 |
| GET | `/api/accounts/stats` | 获取统计信息 |
| GET | `/api/accounts/export` | 导出账号数据 |
| POST | `/api/accounts/refresh` | 刷新账号数据 |

## 注意事项

- **IP 质量**至关重要，低质量 IP 会导致无法进入注册页面或触发频率限制
- **同一 IP** 短时间内不宜多次注册，建议设置合理的 `registration_delay`
- 推荐使用**指纹浏览器**，确保能通过 [BrowserScan](https://www.browserscan.net) 检测
- 开启**无痕模式**（`use_incognito_mode: true`）有助于通过人机验证
- 配置文件 `config/app.json` 和账号数据 `data/accounts.json` 已被 `.gitignore` 忽略，不会被提交到仓库

## 常见问题

**Q: 注册时提示 "IP质量不佳"**
A: 更换高质量代理 IP，避免使用数据中心 IP。

**Q: 验证码一直无法通过**
A: 尝试使用指纹浏览器、调大 `Bot_protection_wait` 值、检查浏览器是否通过 BrowserScan 检测。

**Q: Web 管理界面无法访问**
A: 确认端口 5010 未被占用，检查 Flask 和 flask-cors 是否已安装。

**Q: OAuth2 认证失败**
A: 确保 `client_id` 和 `redirect_url` 已正确配置，且 Azure AD 应用注册已完成。

## 技术栈

- [Playwright](https://playwright.dev/python/) — 浏览器自动化
- [Flask](https://flask.palletsprojects.com/) — Web 服务框架
- [Faker](https://faker.readthedocs.io/) — 随机数据生成

## License

MIT
