import os
import time
import json
import random
import string
import secrets
import platform
from pathlib import Path
from faker import Faker
from get_token import get_access_token
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor

def generate_strong_password(length=16):

    chars = string.ascii_letters + string.digits + "!@#$%^&*"

    while True:
        password = ''.join(secrets.choice(chars) for _ in range(length))

        if (any(c.islower() for c in password) 
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in "!@#$%^&*" for c in password)):
            return password


def random_email(length):

    first_char = random.choice(string.ascii_lowercase)

    other_chars = []
    for _ in range(length - 1):  
        if random.random() < 0.07:  
            other_chars.append(random.choice(string.digits))
        else: 
            other_chars.append(random.choice(string.ascii_lowercase))

    return first_char + ''.join(other_chars)

def find_browser_on_mac():
    """在macOS上自动查找浏览器"""
    possible_paths = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        '/opt/homebrew/bin/chromium',
        '/usr/local/bin/chromium'
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            return path
    return None

def OpenBrowser():
    try:
        p = sync_playwright().start()
        
        # 声明全局变量
        global browser_path, proxy
        
        # 根据操作系统和配置选择浏览器路径
        browser_executable = browser_path
        
        # 如果没有指定浏览器路径且在macOS上，尝试自动查找
        if not browser_executable and platform.system() == 'Darwin':
            browser_executable = find_browser_on_mac()
            if browser_executable:
                print(f"[Info] - 在macOS上找到浏览器: {browser_executable}")
        
        # 配置代理参数
        proxy_config = None
        if proxy and proxy.strip():
            proxy_config = {
                "server": proxy,
                "bypass": "localhost",
            }
        
        # 基础浏览器参数
        base_args = [
            "--disable-blink-features=AutomationControlled",  # 避免检测
            "--disable-web-security",  # 禁用web安全检查
            "--disable-features=VizDisplayCompositor",  # 禁用某些检测特征
            "--no-first-run",  # 跳过首次运行
            "--no-default-browser-check",  # 不检查默认浏览器
            "--disable-default-apps",  # 禁用默认应用
            "--disable-popup-blocking",  # 禁用弹窗阻止
            "--disable-translate",  # 禁用翻译提示
            "--disable-background-timer-throttling",  # 禁用后台定时器限制
            "--disable-backgrounding-occluded-windows",  # 禁用后台窗口
            "--disable-renderer-backgrounding",  # 禁用渲染器后台
            "--disable-field-trial-config",  # 禁用字段试验配置
            "--disable-ipc-flooding-protection",  # 禁用IPC洪水保护
        ]
        
        # 如果启用无痕模式，添加相应参数  
        global use_incognito_mode
        if use_incognito_mode:
            base_args.append("--incognito")
            print("🕵️ 启用无痕模式以提高人机验证通过率")
        
        # 启动浏览器配置
        launch_options = {
            "headless": False,
            "args": base_args
        }
        
        if proxy_config:
            launch_options["proxy"] = proxy_config
            
        if browser_executable:
            launch_options["executable_path"] = browser_executable
            browser = p.chromium.launch(**launch_options)
        else:
            browser = p.chromium.launch(**launch_options)
        
        # 创建新的隐私浏览上下文
        context = browser.new_context(
            viewport={'width': 1200, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN,zh;q=0.9,en;q=0.8',
            timezone_id='Asia/Shanghai',
            permissions=['geolocation', 'notifications'],
            extra_http_headers={
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        # 注入脚本来隐藏webdriver特征
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // 伪装Chrome插件
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // 伪装语言
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
            });
            
            // 移除webdriver痕迹
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """)
            
        return browser, p, context

    except Exception as e:
        print(f"[Error] - 启动浏览器失败: {e}")
        return None, None, None

def Outlook_register(page, email, password):

    fake = Faker()

    lastname = fake.last_name()
    firstname = fake.first_name()
    year = str(random.randint(1960, 2005))
    month = str(random.randint(1, 12))
    day = str(random.randint(1, 28))

    try:

        page.goto("https://outlook.live.com/mail/0/?prompt=create_account", timeout=20000, wait_until="domcontentloaded")
        page.get_by_text('同意并继续').wait_for(timeout=30000)
        start_time = time.time()
        page.wait_for_timeout(2000)
        page.get_by_text('同意并继续').click(timeout=30000)

    except: 

        print("[Error: IP] - IP质量不佳，无法进入注册界面。 ")
        return False
    
    try:

        page.locator('[aria-label="新建电子邮件"]').type(email,delay=80,timeout=10000)
        page.locator('[data-testid="primaryButton"]').click(timeout=5000)
        page.wait_for_timeout(400)
        page.locator('[type="password"]').type(password,delay=60,timeout=10000)
        page.wait_for_timeout(400)
        page.locator('[data-testid="primaryButton"]').click(timeout=5000)
        
        page.wait_for_timeout(500)
        page.locator('[name="BirthYear"]').fill(year,timeout=10000)

        try:

            page.wait_for_timeout(600)
            page.locator('[name="BirthMonth"]').select_option(value=month,timeout=2000)
            page.wait_for_timeout(1200)
            page.locator('[name="BirthDay"]').select_option(value=day)
        
        except:

            page.locator('[name="BirthMonth"]').click()
            page.wait_for_timeout(400)
            page.locator(f'[role="option"]:text-is("{month}月")').click()
            page.wait_for_timeout(1200)
            page.locator('[name="BirthDay"]').click()
            page.wait_for_timeout(400)
            page.locator(f'[role="option"]:text-is("{day}日")').click()

        page.locator('[data-testid="primaryButton"]').click(timeout=5000)

        page.locator('#lastNameInput').type(lastname,delay=120,timeout=10000)
        page.wait_for_timeout(700)
        page.locator('#firstNameInput').fill(firstname,timeout=10000)

        if time.time() - start_time < bot_protection_wait:
            page.wait_for_timeout((bot_protection_wait - time.time() + start_time)*1000)
        
        page.locator('[data-testid="primaryButton"]').click(timeout=5000)
        page.locator('span > [href="https://go.microsoft.com/fwlink/?LinkID=521839"]').wait_for(state='detached',timeout=22000)

        page.wait_for_timeout(400)

        if page.get_by_text('一些异常活动').count() > 0:
            print("[Error: IP or broswer] - 当前IP注册频率过快。检查IP与是否为指纹浏览器并关闭了无头模式。")
            return False

        if page.locator('iframe#enforcementFrame').count() > 0:
            print("[Error: FunCaptcha] - 验证码类型错误，非按压验证码。 ")
            return False

        page.wait_for_event("request", lambda req: req.url.startswith("blob:https://iframe.hsprotect.net/"), timeout=22000)
        page.wait_for_timeout(800)

        page.keyboard.press('Tab')
        page.keyboard.press('Tab')
        page.wait_for_timeout(100)

        for _ in range(0, max_captcha_retries + 1):

            page.keyboard.press('Enter')
            page.wait_for_timeout(11000)
            page.keyboard.press('Enter')
            page.wait_for_event("request", lambda req: req.url.startswith("https://browser.events.data.microsoft.com"), timeout=40000)

            try:
                page.wait_for_event("request", lambda req: req.url.startswith("blob:https://iframe.hsprotect.net/"), timeout=1700)
 
            except:
                try:
                    page.get_by_text('一些异常活动').wait_for(timeout=1200)
                    print("[Error: Rate limit] - 正常通过验证码，但当前IP注册频率过快。")
                    return False

                except:
                    pass
                page.wait_for_timeout(500)
                break

        else: 
            raise TimeoutError

    except:

        print(f"[Error: IP] - 加载超时或因触发机器人检测导致按压次数达到最大仍未通过。")
        return False  
    
    # 使用pathlib处理跨平台路径
    results_dir = Path('Results')
    filename = results_dir / 'logged_email.txt' if enable_oauth2 else results_dir / 'unlogged_email.txt'
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(f"{email}@outlook.com: {password}\n")
    print(f'[Success: Email Registration] - {email}@outlook.com: {password}')

    if not enable_oauth2:
        return True

    try:
        page.locator('[data-testid="secondaryButton"]').click(timeout=20000) 
        button = page.locator('[data-testid="secondaryButton"]')
        button.wait_for(timeout=5000)

    except:

        print(f"[Error: Timeout] - 无法找到按钮。")
        return False   

    try:

        page.wait_for_timeout(random.randint(1600,2000))
        button.click(timeout=6000)
        button = page.locator('[data-testid="secondaryButton"]')
        button.wait_for(timeout=5000)
        page.wait_for_timeout(random.randint(1600,2000))
        button.click(timeout=6000)
        button = page.locator('[data-testid="secondaryButton"]')
        button.wait_for(timeout=5000)
        page.wait_for_timeout(3000)
        button.click(timeout=6000)

    except:
        pass

    try:

        page.wait_for_timeout(3200)
        if page.get_by_text("保持登录状态?").count() > 0:
            page.get_by_text('否').click(timeout=12000)
        page.locator('.splitPrimaryButton[aria-label="新邮件"]').wait_for(timeout=26000)
        return True

    except:
        print(f'[Error: Timeout] - 邮箱未初始化，无法正常收件。')
        return False

def process_single_flow():

    try:
        browser = None
        p = None
        context = None
        browser, p, context = OpenBrowser()
        
        # 检查浏览器是否成功启动
        if browser is None or p is None or context is None:
            print("[Error] - 无法启动浏览器")
            return False
            
        page = context.new_page()

        email =  random_email(random.randint(12, 14))
        password = generate_strong_password(random.randint(11, 15))
        result = Outlook_register(page, email, password)
        if result and not enable_oauth2:
            # 根据配置决定是否关闭浏览器
            if not close_browser_after_registration:
                print("[Info] - 注册完成，保持浏览器开启状态以便后续操作")
                # 不关闭浏览器，保持页面开启并返回
                page.wait_for_timeout(5000)  # 等待5秒确保页面加载完成
                return True

            return True
        
        elif not result:
            return False
        
        token_result = get_access_token(page, email)
        if token_result[0]:
            refresh_token, access_token, expire_at =  token_result
            # 使用pathlib处理跨平台路径
            token_file = Path('Results') / 'outlook_token.txt'
            with open(token_file, 'a', encoding='utf-8') as f2:
                f2.write(email + "@outlook.com---" + password + "---" + refresh_token + "---" + access_token  + "---" + str(expire_at) + "\n") 
            print(f'[Success: TokenAuth] - {email}@outlook.com')
            
            # 根据配置决定是否关闭浏览器
            if not close_browser_after_registration:
                print("[Info] - 注册完成，保持浏览器开启状态以便后续操作")
                # 不关闭浏览器，保持页面开启并返回
                page.wait_for_timeout(5000)  # 等待5秒确保页面加载完成
                return True
                
            return True
        else:
            return False

    except:
        return False
    
    finally:
        # 根据配置决定是否关闭浏览器
        if close_browser_after_registration:
            # 安全关闭浏览器和playwright
            try:
                if context:
                    context.close()
            except:
                pass
            try:
                if browser:
                    browser.close()
            except:
                pass
            try:
                if p:
                    p.stop()
            except:
                pass
        else:
            print("[Info] - 根据配置，浏览器将保持开启状态")

def main(concurrent_flows=1, max_tasks=1):
    
    task_counter = 0  
    succeeded_tasks = 0 
    failed_tasks = 0 

    with ThreadPoolExecutor(max_workers=concurrent_flows) as executor:
        running_futures = set()

        while task_counter < max_tasks or len(running_futures) > 0:

            done_futures = {f for f in running_futures if f.done()}
            for future in done_futures:
                try:
                    result = future.result()
                    if result:
                        succeeded_tasks += 1
                    else:
                        failed_tasks += 1

                except Exception as e:
                    failed_tasks += 1
                    print(e)

                running_futures.remove(future)
            
            while len(running_futures) < concurrent_flows and task_counter < max_tasks:
                time.sleep(0.2)
                new_future = executor.submit(process_single_flow)
                running_futures.add(new_future)
                task_counter += 1

            time.sleep(0.5)

        print(f"[Info: Result] - 共 {max_tasks} 个，成功 {succeeded_tasks}，失败 {failed_tasks}")
        
        # 如果配置为不关闭浏览器，则保持程序运行
        if not close_browser_after_registration:
            print("[Info] - 程序已完成注册任务，保持运行以维持浏览器开启状态")
            print("[Info] - 按 Ctrl+C 可以停止程序并关闭所有浏览器")
            try:
                # 保持程序运行，直到用户中断
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("[Info] - 程序被用户中断，正在关闭...")

if __name__ == '__main__':
    

    # 使用pathlib处理配置文件
    config_file = Path('config.json')
    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f) 

    # 确保Results目录存在
    results_dir = Path("Results")
    results_dir.mkdir(exist_ok=True)

    browser_path = data['browser_path']
    bot_protection_wait = data['Bot_protection_wait']
    max_captcha_retries = data['max_captcha_retries']
    proxy = data['proxy']
    enable_oauth2 = data['enable_oauth2']
    use_incognito_mode = data.get('use_incognito_mode', True)  # 默认启用无痕模式
    close_browser_after_registration = data.get('close_browser_after_registration', True)  # 默认注册后关闭浏览器
    # 从配置文件读取并发数和任务数
    concurrent_flows = data.get('concurrent_flows', 1)
    max_tasks = data.get('max_tasks', 1)


    main(concurrent_flows, max_tasks)