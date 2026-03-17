"""
定时任务调度器

每日 9:30 发送前一天的 Key 汇总日报邮件。

@author buchi
@since 2026-03-18
"""

import time
import schedule
from .email_notify import send_daily_report


def daily_report_job():
    """每日日报任务"""
    print("[Scheduler] - 开始发送昨日 Key 日报...")
    send_daily_report()


def start_scheduler():
    """启动定时调度器（阻塞运行）"""
    schedule.every().day.at("09:30").do(daily_report_job)

    print("[Scheduler] - 定时任务已启动")
    print("[Scheduler] - 每日 09:30 发送前一天的 Key 汇总日报")
    print("[Scheduler] - 按 Ctrl+C 退出")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n[Scheduler] - 已停止")
