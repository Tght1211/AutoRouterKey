#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
macOS系统兼容性检查脚本
检查运行OutlookRegister所需的系统环境
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    version = sys.version_info
    print(f"   当前Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 7:
        print("   ✅ Python版本符合要求 (3.7+)")
        return True
    else:
        print("   ❌ Python版本过低，需要3.7或更高版本")
        return False

def check_operating_system():
    """检查操作系统"""
    print("💻 检查操作系统...")
    os_name = platform.system()
    os_version = platform.release()
    print(f"   操作系统: {os_name} {os_version}")
    
    if os_name == "Darwin":
        print("   ✅ macOS系统检测通过")
        return True
    else:
        print(f"   ⚠️  当前系统为{os_name}，此版本专为macOS优化")
        return True  # 仍可运行，但给出警告

def check_browsers():
    """检查可用浏览器"""
    print("🌐 检查浏览器...")
    browsers = {
        "Chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "Edge": "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "Chromium": "/Applications/Chromium.app/Contents/MacOS/Chromium"
    }
    
    found_browsers = []
    for name, path in browsers.items():
        if Path(path).exists():
            print(f"   ✅ {name}: {path}")
            found_browsers.append(name)
        else:
            print(f"   ❌ {name}: 未安装")
    
    if found_browsers:
        print(f"   ✅ 检测到 {len(found_browsers)} 个可用浏览器")
        return True
    else:
        print("   ⚠️  未检测到Chrome或Edge，将使用Playwright内置浏览器")
        return True

def check_network():
    """检查网络连接"""
    print("📡 检查网络连接...")
    try:
        import socket
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        print("   ✅ 网络连接正常")
        return True
    except socket.error:
        print("   ❌ 网络连接失败，请检查网络设置")
        return False

def check_dependencies():
    """检查Python依赖包"""
    print("📦 检查Python依赖包...")
    required_packages = ["faker", "requests", "playwright"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}: 已安装")
        except ImportError:
            print(f"   ❌ {package}: 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"   ⚠️  缺少依赖包: {', '.join(missing_packages)}")
        print(f"   💡 运行以下命令安装: pip install {' '.join(missing_packages)}")
        return False
    else:
        print("   ✅ 所有依赖包已安装")
        return True

def check_playwright_browsers():
    """检查Playwright浏览器"""
    print("🎭 检查Playwright浏览器...")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # 检查是否已安装chromium
            browser_path = p.chromium.executable_path
            if browser_path and Path(browser_path).exists():
                print(f"   ✅ Playwright Chromium: {browser_path}")
                return True
            else:
                print("   ❌ Playwright Chromium未安装")
                print("   💡 运行以下命令安装: playwright install chromium")
                return False
    except Exception as e:
        print(f"   ❌ Playwright检查失败: {e}")
        return False

def check_config_file():
    """检查配置文件"""
    print("⚙️ 检查配置文件...")
    config_file = Path("config/app.json")
    if config_file.exists():
        print("   ✅ config/app.json 存在")
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("   ✅ config/app.json 格式正确")
            
            # 检查关键配置项
            if 'proxy' in config and config['proxy']:
                print(f"   📡 代理设置: {config['proxy']}")
            else:
                print("   ⚠️  未配置代理")
            
            return True
        except json.JSONDecodeError:
            print("   ❌ config/app.json 格式错误")
            return False
    else:
        print("   ❌ config/app.json 不存在")
        return False

def check_results_directory():
    """检查结果目录"""
    print("📁 检查结果目录...")
    results_dir = Path("data/results")
    if results_dir.exists():
        print("   ✅ data/results目录存在")
    else:
        print("   📁 创建data/results目录...")
        results_dir.mkdir(parents=True, exist_ok=True)
        print("   ✅ data/results目录已创建")
    return True

def main():
    """主检查函数"""
    print("🍎 macOS系统兼容性检查")
    print("=" * 50)
    
    checks = [
        ("Python版本", check_python_version),
        ("操作系统", check_operating_system),
        ("浏览器", check_browsers),
        ("网络连接", check_network),
        ("Python依赖", check_dependencies),
        ("Playwright浏览器", check_playwright_browsers),
        ("配置文件", check_config_file),
        ("结果目录", check_results_directory),
    ]
    
    results = []
    for name, check_func in checks:
        print()
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"   ❌ 检查失败: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("📊 检查结果汇总:")
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 总体评分: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 恭喜！系统环境完全兼容，可以正常运行OutlookRegister。")
    elif passed >= total * 0.7:
        print("⚠️  系统环境基本兼容，但有一些问题需要解决。")
    else:
        print("❌ 系统环境存在较多问题，建议先解决后再运行。")
    
    print("\n💡 如需帮助，请参考README.md或运行 ./install_macos.sh")

if __name__ == "__main__":
    main()
