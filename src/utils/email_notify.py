"""
邮件通知模块

使用 QQ 邮箱 SMTP 发送通知邮件，支持：
- API Key 诞生即时通知
- 每日 Key 汇总日报

@author buchi
@since 2026-03-18
"""

import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime, timedelta


def _load_email_config():
    """加载邮件配置"""
    config_path = Path(__file__).parent.parent.parent / 'config' / 'app.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('email_notify', {})
    except Exception:
        return {}


def send_email(subject, body_html, to_addr=None):
    """通用邮件发送（QQ 邮箱 SMTP SSL）"""
    cfg = _load_email_config()
    if not cfg.get('enabled', False):
        return False

    smtp_host = cfg.get('smtp_host', 'smtp.qq.com')
    smtp_port = cfg.get('smtp_port', 465)
    user = cfg.get('email_user', '')
    passwd = cfg.get('email_pass', '')
    to = to_addr or cfg.get('notify_to', '')

    if not all([user, passwd, to]):
        print("[Email] - 邮件配置不完整，跳过发送")
        return False

    msg = MIMEMultipart('alternative')
    msg['From'] = f'OpenRouter Monitor <{user}>'
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body_html, 'html', 'utf-8'))

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
            server.login(user, passwd)
            server.sendmail(user, [to], msg.as_string())
        print(f"[Email] - 邮件已发送: {subject}")
        return True
    except Exception as e:
        print(f"[Email] - 发送失败: {e}")
        return False


def notify_new_api_key(email, api_key):
    """Key 诞生即时通知"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    subject = f"[OpenRouter] 新 API Key 已创建 - {email}"
    body = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #1a1a1a; border-bottom: 2px solid #7c5cfc; padding-bottom: 10px;">OpenRouter API Key 创建成功</h2>
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr><td style="padding: 8px 0; color: #666;">账号</td><td style="padding: 8px 0; font-weight: bold;">{email}</td></tr>
            <tr><td style="padding: 8px 0; color: #666;">API Key</td><td style="padding: 8px 0; font-family: monospace; font-size: 13px; word-break: break-all;">{api_key}</td></tr>
            <tr><td style="padding: 8px 0; color: #666;">创建时间</td><td style="padding: 8px 0;">{now}</td></tr>
        </table>
        <p style="color: #999; font-size: 12px;">此邮件由 AutoRouterKey 自动发送</p>
    </div>
    """
    return send_email(subject, body)


def send_daily_report(target_date=None):
    """发送每日 Key 汇总日报（默认汇总昨日数据）"""
    if target_date is None:
        target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    history = load_key_history()
    day_keys = [k for k in history if k.get('date') == target_date]

    if not day_keys:
        print(f"[Email] - {target_date} 无新增 Key，跳过日报")
        return False

    rows = ""
    for i, k in enumerate(day_keys, 1):
        rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #eee; text-align: center;">{i}</td>
            <td style="padding: 8px; border: 1px solid #eee;">{k['email']}</td>
            <td style="padding: 8px; border: 1px solid #eee; font-family: monospace; font-size: 12px; word-break: break-all;">{k['api_key']}</td>
            <td style="padding: 8px; border: 1px solid #eee;">{k.get('created_at', '')}</td>
        </tr>
        """

    plain_keys = "\n".join(k['api_key'] for k in day_keys)

    subject = f"[OpenRouter 日报] {target_date} 新增 {len(day_keys)} 个 API Key"
    body = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #1a1a1a; border-bottom: 2px solid #7c5cfc; padding-bottom: 10px;">OpenRouter Key 日报 - {target_date}</h2>
        <p style="color: #333; font-size: 16px;">今日共新增 <strong style="color: #7c5cfc;">{len(day_keys)}</strong> 个 API Key</p>
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <thead>
                <tr style="background: #f8f8f8;">
                    <th style="padding: 10px; border: 1px solid #eee; width: 40px;">#</th>
                    <th style="padding: 10px; border: 1px solid #eee;">账号</th>
                    <th style="padding: 10px; border: 1px solid #eee;">API Key</th>
                    <th style="padding: 10px; border: 1px solid #eee; width: 160px;">创建时间</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>

        <h3 style="color: #1a1a1a; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 8px;">Key 快速复制区（每行一个，可直接全选复制到共享池）</h3>
        <pre style="background: #f5f5f5; padding: 16px; border-radius: 8px; font-family: 'SF Mono', Monaco, Menlo, monospace; font-size: 12px; line-height: 1.8; word-break: break-all; white-space: pre-wrap; border: 1px solid #e0e0e0; user-select: all;">{plain_keys}</pre>

        <p style="color: #999; font-size: 12px; margin-top: 20px;">此邮件由 AutoRouterKey 定时任务自动发送</p>
    </div>
    """
    return send_email(subject, body)


# === Key 历史记录管理 ===

_KEY_HISTORY_PATH = Path(__file__).parent.parent.parent / 'data' / 'key_history.json'


def load_key_history():
    """加载 Key 历史记录"""
    try:
        if _KEY_HISTORY_PATH.exists():
            with open(_KEY_HISTORY_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return []


def record_new_key(email, api_key):
    """记录新 Key 到历史"""
    history = load_key_history()
    now = datetime.now()
    history.append({
        "date": now.strftime('%Y-%m-%d'),
        "email": email,
        "api_key": api_key,
        "created_at": now.strftime('%Y-%m-%d %H:%M:%S')
    })
    try:
        _KEY_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_KEY_HISTORY_PATH, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Warning] - 记录 Key 历史失败: {e}")
