# OpenRouter 自动化参考文档

## 完整注册流程（单账号）

```
1. 启动 Playwright → 创建两个独立的 Chrome 原生无痕浏览器实例
   - 浏览器 A：Outlook 邮箱操作
   - 浏览器 B：OpenRouter 操作

2. [浏览器 A] 登录 Outlook
   - 导航到 https://login.live.com/login.srf?
   - 输入邮箱 → 输入密码 → 处理可能的 CAPTCHA
   - 等待登录完成，到达 Outlook 收件箱

3. [浏览器 B] 注册 OpenRouter
   - 导航到 https://openrouter.ai/sign-up
   - 输入邮箱和密码 → 勾选 Terms of Service → 点击 Continue
   - 处理 Cloudflare Turnstile CAPTCHA（可能需人工介入）

4. [浏览器 A] 获取验证链接
   - 在 Outlook 收件箱搜索最新的 OpenRouter 验证邮件
   - 从邮件正文提取 Clerk.dev 验证 URL

5. [浏览器 B] 访问验证链接
   - 在 OpenRouter 的同一个 page 中 goto 验证 URL
   - 等待从 clerk.openrouter.ai 自动跳转到 openrouter.ai
   - 如果卡在 Clerk 页面，尝试点击 "Continue" 或手动导航

6. [浏览器 B] 创建 API Key
   - 导航到 https://openrouter.ai/settings/keys
   - 关闭可能出现的问卷弹窗
   - 点击 "Create Key" → 提取生成的 API Key

7. 保存结果
   - 更新 accounts.json（openrouter: true, openrouter_api_key: sk-or-v1-...）
   - 记录到 key_history.json
   - 发送即时邮件通知
```

## 2FA 验证码流程（登录已有账号时触发）

```
1. [浏览器 B] 在 OpenRouter 登录页输入邮箱密码后
2. 页面跳转到 2FA 验证码输入页（6 个独立 input 框）
3. [浏览器 A] 切换到 Outlook，搜索最新的验证码邮件
4. 从邮件标题中提取 6 位数字验证码
5. [浏览器 B] 使用 keyboard.type(code, delay=100) 逐字符输入
6. 点击 "Continue" 完成验证
```

## 浏览器启动方式

```python
# 正确方式：Chrome 原生无痕
context = playwright.chromium.launch_persistent_context(
    user_data_dir=temp_dir,
    executable_path=chrome_path,
    args=['--incognito', '--no-first-run', '--disable-blink-features=AutomationControlled'],
    headless=False,
    user_agent='Mozilla/5.0 ... Chrome/145.0.7632.160 ...',
)

# 错误方式：Playwright 默认 context（会被 CAPTCHA 检测）
browser = playwright.chromium.launch()
context = browser.new_context()  # ← 这不是真正的无痕！
```

## 常见问题与解决方案

### CAPTCHA 无法通过
- 检查是否使用 `launch_persistent_context` + `--incognito`
- 检查 User-Agent 是否与真实 Chrome 版本匹配
- 确保没有 `--disable-web-security` 参数
- 如果仍然失败，使用 `wait_for_human_captcha()` 暂停等待人工操作

### 验证链接打开后未自动登录
- 确保验证链接在 OpenRouter 注册时的同一个 page 对象中打开
- 使用 `wait_until="domcontentloaded"` 而非 `networkidle`
- 如果卡在 Clerk 页面，用 `page.goto("https://openrouter.ai/")` 手动跳转

### API Key 创建失败（需要登录）
- 注册后验证链接的 session 可能已过期
- 使用 `login_and_create_key()` 函数重新登录
- 该函数支持 2FA 验证码自动处理

### 问卷弹窗阻塞操作
- 检测 `text=Where did you first hear about OpenRouter`
- 自动选择 "Other" 并点击 "Continue"
- 使用 `page.keyboard.press("Escape")` 关闭未知弹窗

### 验证码获取到旧数据
- `get_verification_code()` 会对比 `last_code` 确保取到新验证码
- 从邮件列表项的 `title` 属性提取（比打开邮件正文更快）
- 循环等待最多 120 秒

## 配置文件说明

### config/app.json

```json
{
    "browser_path": "",
    "proxy": "",
    "use_incognito_mode": true,
    "email_notify": {
        "enabled": true,
        "smtp_host": "smtp.qq.com",
        "smtp_port": 465,
        "email_user": "sender@qq.com",
        "email_pass": "smtp_authorization_code",
        "notify_to": "receiver@163.com"
    }
}
```

### data/accounts.json

```json
{
    "accounts": [
        {
            "id": 1,
            "email": "xxx@outlook.com",
            "password": "password",
            "status": "available",
            "openrouter": false,
            "openrouter_api_key": "",
            "notes": ""
        }
    ]
}
```

## Web API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/accounts` | GET | 获取所有账号 |
| `/api/accounts/stats` | GET | 统计信息（含 Key 数量） |
| `/api/keys/daily` | GET | 按日期分组的 Key 记录 |
| `/api/keys/today` | GET | 今日新增的 Key |
| `/api/accounts/<id>/status` | PUT | 更新账号状态 |
| `/api/accounts/<id>/openrouter` | PUT | 更新 OpenRouter 状态 |
