#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoRouterKey - 主入口文件

提供统一的命令行界面来访问所有功能模块。
"""

import sys
import json
import argparse
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def load_config():
    """加载配置文件"""
    config_file = Path(__file__).parent / 'config/app.json'
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {}

def main():
    # 加载配置文件
    config = load_config()
    
    parser = argparse.ArgumentParser(
        description='AutoRouterKey - OpenRouter API Key 自动化管理系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py register                    # 启动账号注册（使用配置文件中的参数）
  python main.py register --concurrent 2     # 覆盖配置文件的并发数
  python main.py web                         # 启动Web管理界面
  python main.py openrouter                  # 注册 OpenRouter（处理所有未注册账号）
  python main.py openrouter --create-key     # 为已注册账号创建 API Key
  python main.py scheduler                   # 启动定时任务（每日9:30发送Key日报）
  python main.py check                       # 系统检查
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 注册命令 - 使用配置文件中的默认值
    register_parser = subparsers.add_parser('register', help='启动账号注册')
    register_parser.add_argument('--concurrent', type=int, 
                                default=config.get('concurrent_flows', 1), 
                                help=f'并发数量 (配置文件默认: {config.get("concurrent_flows", 1)})')
    register_parser.add_argument('--max-tasks', type=int, 
                                default=config.get('max_tasks', 1), 
                                help=f'最大任务数 (配置文件默认: {config.get("max_tasks", 1)})')
    
    # Web界面命令
    web_parser = subparsers.add_parser('web', help='启动Web管理界面')
    web_parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    web_parser.add_argument('--port', type=int, default=5010, help='监听端口')
    web_parser.add_argument('--debug', action='store_true', help='调试模式')
    

    
    # OpenRouter 注册命令
    openrouter_parser = subparsers.add_parser('openrouter', help='自动注册 OpenRouter 并创建 API Key')
    openrouter_parser.add_argument('--max-tasks', type=int, default=0,
                                   help='最大处理账号数 (默认: 0 表示全部)')
    openrouter_parser.add_argument('--create-key', action='store_true',
                                   help='为已注册但没有 API Key 的账号创建 Key')

    # 定时任务命令
    scheduler_parser = subparsers.add_parser('scheduler', help='启动定时任务（每日9:30发送Key日报）')
    scheduler_parser.add_argument('--send-now', action='store_true',
                                  help='立即发送昨日日报（测试用）')

    # 系统检查命令
    check_parser = subparsers.add_parser('check', help='系统检查')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'register':
            from src.core.register import main as register_main
            # 临时修改工作目录以确保相对路径正确
            import os
            os.chdir(Path(__file__).parent)
            register_main(args.concurrent, args.max_tasks)
            
        elif args.command == 'web':
            from src.web.server import app
            import os
            os.chdir(Path(__file__).parent)
            print("🚀 AutoRouterKey Web 管理平台启动中...")
            print(f"📍 Web界面: http://{args.host}:{args.port}")
            print("📍 API文档: http://localhost:5010/api/accounts")
            print("🔄 支持热重载，修改文件后会自动更新")
            app.run(host=args.host, port=args.port, debug=args.debug)
            
        elif args.command == 'check':
            from src.utils.system_check import main as check_main
            check_main()

        elif args.command == 'openrouter':
            from src.core.openrouter import main as openrouter_main
            import os
            os.chdir(Path(__file__).parent)
            mode = 'create_key' if args.create_key else 'register'
            openrouter_main(args.max_tasks, mode=mode)

        elif args.command == 'scheduler':
            import os
            os.chdir(Path(__file__).parent)
            if args.send_now:
                from src.utils.email_notify import send_daily_report
                send_daily_report()
            else:
                from src.utils.scheduler import start_scheduler
                start_scheduler()

    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        print(f"❌ 运行出错: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()