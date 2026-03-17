---
name: openrouter-register
version: 1.0.0
description: OpenRouter 全链路自动化 — Outlook 注册 → OpenRouter 注册 → API Key 创建 → 邮件通知 → Web 管理
author: buchi
tags: [openrouter, api-key, automation, playwright, outlook]
prerequisites:
  - macOS 10.14+
  - Python 3.10+
  - Google Chrome
entry_point: python main.py
---

# OpenRouter 自动注册与 API Key 管理

> **给 AI 智能体的说明**：读取此文件后，你将获得完整的 OpenRouter 账号自动化能力。请按照下方"引导用户"章节与用户交互，确认配置后再执行命令。

## 你能做什么（能力清单）

| # | 能力 | 命令 | 说明 |
|---|------|------|------|
| 1 | Outlook 邮箱批量注册 | `python main.py register` | 自动填表、生成随机账号、并发执行（`--concurrent N --max-tasks N`） |
| 2 | OpenRouter 全自动注册 | `python main.py openrouter` | Outlook 登录 → 注册 → 邮件验证 → 2FA → Key 创建（`--max-tasks N`） |
| 3 | 补创 API Key | `python main.py openrouter --create-key` | 为已注册但缺 Key 的账号创建 |
| 4 | 邮件即时通知 | 自动触发 | 每创建一个 Key 自动发邮件 |
| 5 | 每日日报 | `python main.py scheduler` | 每日 9:30 汇总前一天 Key（含纯文本复制区） |
| 6 | 立即发送日报 | `python main.py scheduler --send-now` | 立即发送昨日日报 |
| 7 | Web 管理平台 | `python main.py web` | 统计面板 + 账号表格 + Key 日报 + 搜索/导出 |
| 8 | 系统环境检查 | `python main.py check` | 检测 Python、浏览器、网络、依赖 |

## 引导用户（AI 交互流程）

当用户首次使用或要求执行自动化时，按以下步骤引导：

### 步骤 1：检查环境

```bash
python main.py check
```

确认 Python、Chrome、网络均正常。

### 步骤 2：确认配置

检查 `config/app.json` 是否存在，如不存在则：

```bash
cp config/app.example.json config/app.json
cp data/accounts.example.json data/accounts.json
```

询问用户：
- 是否需要配置**代理**？（填入 `proxy` 字段）
- 是否需要**邮件通知**？如是，需要 SMTP 发件邮箱、授权码、收件邮箱（填入 `email_notify`）

### 步骤 3：根据用户意图执行

| 用户意图 | 你应该执行的命令 |
|----------|------------------|
| "注册 Outlook 邮箱" | `python main.py register` |
| "注册 OpenRouter" / "获取 API Key" | `python main.py openrouter` |
| "给已注册账号创建 Key" | `python main.py openrouter --create-key` |
| "查看账号" / "管理平台" | `python main.py web` 然后告知访问 `http://localhost:5010` |
| "发送日报" / "看看昨天的 Key" | `python main.py scheduler --send-now` |
| "启动定时任务" | `python main.py scheduler` |

### 步骤 4：CAPTCHA 处理

执行过程中如果出现 `[CAPTCHA] - 检测到人机验证` 提示，**立即告知用户**需要手动在浏览器中完成验证，完成后自动继续。

### 步骤 5：结果确认

执行完成后：
- 建议用户启动 Web 平台（`python main.py web`）查看结果
- 或直接查看 `data/accounts.json` 中的 `openrouter_api_key` 字段

## 安装（首次使用）

```bash
# 克隆项目
git clone https://github.com/Tght1211/AutoRouterKey.git
cd AutoRouterKey

# 安装依赖
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

# 初始化配置
cp config/app.example.json config/app.json
cp data/accounts.example.json data/accounts.json
```

## 关键经验（执行前必读）

### 浏览器
- **必须** 使用 `launch_persistent_context` + `--incognito` 启动 Chrome 原生无痕窗口
- Playwright 默认的 `browser.new_context()` 不是真正无痕，会被 Cloudflare Turnstile 检测
- User-Agent 必须匹配真实 Chrome 版本（当前 `Chrome/145.0.7632.160`）
- 禁止 `--disable-web-security`

### 验证流程
- 验证链接必须在 OpenRouter 的**同一个 page** 中打开（保持 Clerk session）
- 邮件验证码从 Outlook 邮件列表项的 **title 属性**提取（比打开正文更快）
- 2FA 用 `keyboard.type(code, delay=100)` 逐字符输入（OpenRouter 用 6 个独立 input）

### UI 陷阱
- "Where did you first hear about OpenRouter?" 问卷弹窗 → 选 "Other" + "Continue"
- 透明 overlay 遮挡按钮 → `force=True` 点击
- 通用弹窗 → 先按 `Escape`

## 配置参考

```json
{
    "browser_path": "",
    "proxy": "http://127.0.0.1:7890",
    "use_incognito_mode": true,
    "concurrent_flows": 2,
    "max_tasks": 4,
    "email_notify": {
        "enabled": true,
        "smtp_host": "smtp.qq.com",
        "smtp_port": 465,
        "email_user": "your_qq@qq.com",
        "email_pass": "your_smtp_auth_code",
        "notify_to": "your_email@163.com"
    }
}
```

## API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/accounts` | 获取所有账号 |
| GET | `/api/accounts/stats` | 统计信息（含 Key 数量、今日新增） |
| PUT | `/api/accounts/<id>/status` | 更新账号状态 |
| PUT | `/api/accounts/<id>/openrouter` | 更新 OpenRouter 注册状态 |
| GET | `/api/keys/daily` | 按日期分组的 Key 历史 |
| GET | `/api/keys/today` | 今日新增 Key |

## 参考文档

详细的流程时序、代码片段和问题排查 → [reference.md](./reference.md)
