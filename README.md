# AutoRouterKey

> Automated OpenRouter API Key harvester — 从 Outlook 邮箱注册到 API Key 批量创建的全链路自动化。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Playwright](https://img.shields.io/badge/Playwright-Automation-green.svg)](https://playwright.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

基于 Playwright 浏览器自动化，完整实现：Outlook 邮箱注册 → OpenRouter 账号注册 → 邮件验证 → 2FA 验证码 → API Key 创建 → 邮件通知 → Web 管理平台。针对 macOS 优化。

> **免责声明**：本项目仅供学习研究，请遵守相关服务条款。

---

## AI Agent Skills

本项目内置可被 AI 智能体直接使用的 Skill。AI 读取 Skill 文件后，可自主执行全部自动化流程并引导用户配置。

### 可用 Skills

| Skill | 路径 | 描述 |
|-------|------|------|
| **openrouter-register** | `.cursor/skills/openrouter-register/SKILL.md` | OpenRouter 全链路自动化：Outlook 注册 → OpenRouter 注册 → API Key 创建 → 邮件通知 → Web 管理 |

### AI 接入方式

**Cursor IDE：** Skill 会被自动发现，AI 可直接读取并执行。

**其他 AI 智能体：**

```bash
# 1. 克隆项目
git clone https://github.com/Tght1211/AutoRouterKey.git
cd AutoRouterKey

# 2. 阅读 Skill 文件了解全部能力
cat .cursor/skills/openrouter-register/SKILL.md

# 3. 按 Skill 中的快速开始执行安装和配置
```

AI 智能体读取 `SKILL.md` 后应能自主完成：
1. 引导用户安装依赖和配置 SMTP / 代理
2. 根据用户意图选择正确的 CLI 命令执行
3. 遇到 CAPTCHA 时提示用户手动介入
4. 在 Web 平台上展示运行结果

---

## 功能一览

| 功能 | 命令 | 描述 |
|------|------|------|
| Outlook 批量注册 | `python main.py register` | 自动填写注册表单、生成随机账号、并发执行 |
| OpenRouter 全自动注册 | `python main.py openrouter` | Outlook 登录 → 注册 → 邮件验证 → 2FA → 创建 Key |
| API Key 补创 | `python main.py openrouter --create-key` | 为已注册但缺少 Key 的账号自动创建 |
| Web 管理平台 | `python main.py web` | 统计面板 + 账号表格 + Key 日报 + 搜索/导出 |
| 定时日报 | `python main.py scheduler` | 每日 9:30 汇总前一天所有 Key 发送邮件 |
| 系统检查 | `python main.py check` | 检测 Python、浏览器、网络、依赖 |

## 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | macOS 10.14+ |
| Python | 3.10+ |
| 浏览器 | Google Chrome |
| 网络 | 建议配置代理（住宅 IP 优先） |

## 快速开始

### 1. 安装

```bash
git clone https://github.com/Tght1211/AutoRouterKey.git
cd AutoRouterKey

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

或用脚本一键安装：`chmod +x scripts/install.sh && ./scripts/install.sh`

### 2. 配置

```bash
cp config/app.example.json config/app.json
cp data/accounts.example.json data/accounts.json
```

编辑 `config/app.json`：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `browser_path` | Chrome 路径（留空自动检测） | `""` |
| `proxy` | 代理地址（http/socks5） | `""` |
| `use_incognito_mode` | 无痕模式（**必须开启**） | `true` |
| `concurrent_flows` | 并发浏览器数量 | `2` |
| `max_tasks` | 最大任务数 | `4` |
| `email_notify.enabled` | 启用邮件通知 | `false` |
| `email_notify.smtp_host` | SMTP 服务器 | `smtp.qq.com` |
| `email_notify.smtp_port` | SMTP 端口（SSL） | `465` |
| `email_notify.email_user` | 发件邮箱 | `""` |
| `email_notify.email_pass` | SMTP 授权码 | `""` |
| `email_notify.notify_to` | 收件邮箱 | `""` |

### 3. 使用

```bash
# 查看所有命令
python main.py --help

# 注册 Outlook 邮箱
python main.py register
python main.py register --concurrent 3 --max-tasks 10

# 注册 OpenRouter + 创建 API Key（全自动）
python main.py openrouter
python main.py openrouter --max-tasks 5

# 为已注册账号补创 API Key
python main.py openrouter --create-key

# 启动 Web 管理界面
python main.py web
python main.py web --port 8080

# 启动每日日报定时任务
python main.py scheduler

# 立即发送昨日日报
python main.py scheduler --send-now

# 系统环境检查
python main.py check
```

## Web 管理平台

启动后访问 `http://localhost:5010`：

- **统计面板** — 总账号 / 可用 / 已注册 OpenRouter / 已获取 Key / 今日新增 / 已使用
- **账号表格** — 邮箱、密码（可显隐）、状态、OpenRouter 开关、API Key（一键复制）
- **Key 日报** — 按日期分组展示 Key 生成记录 + 纯文本快速复制区（一键全部复制）
- **其他** — 搜索过滤、分页、添加/编辑/删除、导出、暗色模式

### API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/accounts` | 获取所有账号 |
| GET | `/api/accounts/stats` | 统计信息 |
| PUT | `/api/accounts/<id>/status` | 更新状态 |
| PUT | `/api/accounts/<id>/openrouter` | 更新 OpenRouter 状态 |
| PUT | `/api/accounts/<id>/notes` | 更新备注 |
| GET | `/api/accounts/export` | 导出数据 |
| POST | `/api/accounts/refresh` | 刷新数据 |
| GET | `/api/keys/daily` | 按日期分组 Key 记录 |
| GET | `/api/keys/today` | 今日新增 Key |

## 邮件通知

启用 `email_notify.enabled: true` 后：

1. **即时通知** — 每个 API Key 创建成功后自动发邮件
2. **每日日报** — 每日 9:30 汇总前一天所有 Key，包含：
   - 详细表格（序号、账号、Key、时间）
   - **Key 快速复制区**（每行一个 Key，可直接全选复制到共享池）

## 项目结构

```
AutoRouterKey/
├── main.py                       # 统一 CLI 入口
├── requirements.txt              # 依赖包
├── config/
│   ├── app.json                  # 运行时配置（gitignore）
│   └── app.example.json          # 配置模板
├── data/
│   ├── accounts.json             # 账号数据（gitignore）
│   ├── accounts.example.json     # 数据模板
│   └── key_history.json          # Key 生成历史（gitignore）
├── src/
│   ├── core/
│   │   ├── register.py           # Outlook 注册 + 浏览器工具
│   │   └── openrouter.py         # OpenRouter 全流程自动化
│   ├── utils/
│   │   ├── email_notify.py       # SMTP 通知 + Key 历史管理
│   │   ├── scheduler.py          # 定时任务调度
│   │   └── system_check.py       # 系统环境检测
│   └── web/
│       ├── server.py             # Flask API 后端
│       └── templates/
│           └── manager.html      # 管理平台前端
├── scripts/                      # 安装/运行脚本
└── .cursor/skills/               # AI Agent Skills
    └── openrouter-register/
        ├── SKILL.md              # Skill 主文件（AI 入口）
        └── reference.md          # 详细参考文档
```

## 注意事项

- **IP 质量**至关重要，低质量 IP 会导致注册失败
- 必须使用 **Chrome 原生无痕窗口**（`use_incognito_mode: true`）
- 敏感文件（`config/app.json`、`data/accounts.json`、`data/key_history.json`）已在 `.gitignore` 中排除

## 常见问题

**Q: CAPTCHA 无法通过**
A: 确认使用 Chrome 原生无痕（非 Playwright 默认 context），调大 `Bot_protection_wait`。

**Q: OpenRouter 提示 "Couldn't find your account"**
A: 账号未注册成功，用 `python main.py openrouter` 重新注册。

**Q: 邮件通知未收到**
A: 检查 `email_notify.enabled` 是否为 `true`，SMTP 授权码是否正确。

## 技术栈

[Playwright](https://playwright.dev/python/) | [Flask](https://flask.palletsprojects.com/) | [Faker](https://faker.readthedocs.io/) | [schedule](https://schedule.readthedocs.io/)

## License

MIT
