import os
import time
import json
import random
import string
import secrets
import platform
from pathlib import Path
from faker import Faker
from datetime import datetime
from .oauth import get_access_token
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor

def load_config():
    """加载配置文件"""
    config_file = Path('config/app.json')
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {}

def load_accounts_from_json():
    """从JSON文件加载所有账号数据"""
    data_dir = Path('data')
    accounts_json = data_dir / 'accounts.json'
    
    if not accounts_json.exists():
        return []
    
    try:
        with open(accounts_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('accounts', [])
    except Exception as e:
        print(f"读取JSON文件失败: {e}")
        return []

def save_account_to_json(email, password, oauth_enabled=False, refresh_token='', access_token='', expire_at=0):
    """保存账号到JSON文件"""
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    accounts_json = data_dir / 'accounts.json'
    
    # 加载现有账号
    accounts = load_accounts_from_json()
    
    # 生成新的ID
    max_id = 0
    if accounts:
        max_id = max(account.get('id', 0) for account in accounts)
    new_id = max_id + 1
    
    # 检查是否已存在相同的账号
    for account in accounts:
        if account['email'] == email:
            # 更新现有账号
            account['password'] = password
            account['oauth_enabled'] = oauth_enabled
            account['refresh_token'] = refresh_token
            account['access_token'] = access_token
            account['expire_at'] = expire_at
            account['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            break
    else:
        # 添加新账号
        new_account = {
            'id': new_id,
            'email': email,
            'password': password,
            'status': 'available',
            'openrouter': False,
            'oauth_enabled': oauth_enabled,
            'refresh_token': refresh_token,
            'access_token': access_token,
            'expire_at': expire_at,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'notes': ''
        }
        accounts.append(new_account)
    
    # 保存到JSON文件
    try:
        data = {'accounts': accounts}
        with open(accounts_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存账号数据失败: {e}")
        return False

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

def get_available_browsers():
    """获取所有可用的浏览器"""
    browsers = {}
    browser_paths = {
        'chrome': '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        'edge': '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
        'chromium': '/Applications/Chromium.app/Contents/MacOS/Chromium'
    }
    
    for name, path in browser_paths.items():
        if Path(path).exists():
            browsers[name] = path
    
    return browsers

def _get_browser_executable(preferred_browser=None):
    """获取浏览器可执行路径"""
    config = load_config()
    browser_path = config.get('browser_path', '')
    browser_executable = browser_path

    if preferred_browser and not browser_executable:
        available_browsers = get_available_browsers()
        if preferred_browser in available_browsers:
            browser_executable = available_browsers[preferred_browser]
            print(f"[Info] - 使用指定浏览器: {preferred_browser} ({browser_executable})")

    if not browser_executable and platform.system() == 'Darwin':
        browser_executable = find_browser_on_mac()
        if browser_executable:
            print(f"[Info] - 在macOS上找到浏览器: {browser_executable}")

    return browser_executable


def _get_base_args():
    """获取基础浏览器启动参数"""
    config = load_config()
    args = [
        "--disable-blink-features=AutomationControlled",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-default-apps",
        "--disable-popup-blocking",
        "--disable-translate",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-ipc-flooding-protection",
    ]
    if config.get('use_incognito_mode', True):
        args.append("--incognito")
        print("🕵️ 启用无痕模式")
    return args, config


def OpenBrowser(preferred_browser=None):
    """启动浏览器（launch模式，用于注册等不需要原生无痕的场景）"""
    try:
        p = sync_playwright().start()
        config = load_config()
        browser_executable = _get_browser_executable(preferred_browser)
        proxy = config.get('proxy', '')
        base_args, _ = _get_base_args()

        proxy_config = None
        if proxy and proxy.strip():
            proxy_config = {"server": proxy, "bypass": "localhost"}

        launch_options = {"headless": False, "args": base_args}
        if proxy_config:
            launch_options["proxy"] = proxy_config
        if browser_executable:
            launch_options["executable_path"] = browser_executable

        browser = p.chromium.launch(**launch_options)

        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.160 Safari/537.36',
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

        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
        """)

        return browser, p, context

    except Exception as e:
        print(f"[Error] - 启动浏览器失败: {e}")
        return None, None, None


def OpenBrowserPersistent(playwright_instance=None, user_data_dir=None):
    """使用 persistent context 启动浏览器（真正的 Chrome 原生无痕模式）
    
    Args:
        playwright_instance: 可复用的 Playwright 实例，不传则新建
        user_data_dir: 用户数据目录，不传则用临时目录
    Returns:
        (playwright_instance, context)
    """
    import tempfile
    try:
        p = playwright_instance or sync_playwright().start()
        config = load_config()
        browser_executable = _get_browser_executable()
        proxy = config.get('proxy', '')
        base_args, _ = _get_base_args()

        if user_data_dir is None:
            user_data_dir = tempfile.mkdtemp(prefix='pw_incognito_')

        launch_options = {
            "headless": False,
            "args": base_args,
            "viewport": {'width': 1280, 'height': 900},
            "user_agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.160 Safari/537.36',
            "locale": 'zh-CN',
            "timezone_id": 'Asia/Shanghai',
        }

        proxy_config = None
        if proxy and proxy.strip():
            proxy_config = {"server": proxy, "bypass": "localhost"}
            launch_options["proxy"] = proxy_config

        if browser_executable:
            launch_options["executable_path"] = browser_executable

        context = p.chromium.launch_persistent_context(user_data_dir, **launch_options)

        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        return p, context

    except Exception as e:
        print(f"[Error] - 启动持久浏览器失败: {e}")
        return playwright_instance, None

def Outlook_register(page, email, password):
    # 加载配置
    config = load_config()
    bot_protection_wait = config.get('Bot_protection_wait', 30)
    max_captcha_retries = config.get('max_captcha_retries', 3)
    enable_oauth2 = config.get('enable_oauth2', False)

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
        page.locator('[data-testid="primaryButton"]').click(timeout=5010)
        page.wait_for_timeout(400)
        page.locator('[type="password"]').type(password,delay=60,timeout=10000)
        page.wait_for_timeout(400)
        page.locator('[data-testid="primaryButton"]').click(timeout=5010)
        
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

        page.locator('[data-testid="primaryButton"]').click(timeout=5010)

        page.locator('#lastNameInput').type(lastname,delay=120,timeout=10000)
        page.wait_for_timeout(700)
        page.locator('#firstNameInput').fill(firstname,timeout=10000)

        if time.time() - start_time < bot_protection_wait:
            page.wait_for_timeout((bot_protection_wait - time.time() + start_time)*1000)
        
        page.locator('[data-testid="primaryButton"]').click(timeout=5010)
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
    
    # 保存账号到JSON文件
    if save_account_to_json(f"{email}@outlook.com", password, enable_oauth2):
        print(f'[Success: Email Registration] - {email}@outlook.com: {password}')
    else:
        print(f'[Warning] - 保存账号数据失败: {email}@outlook.com')

    if not enable_oauth2:
        return True

    try:
        page.locator('[data-testid="secondaryButton"]').click(timeout=20000) 
        button = page.locator('[data-testid="secondaryButton"]')
        button.wait_for(timeout=5010)

    except:

        print(f"[Error: Timeout] - 无法找到按钮。")
        return False   

    try:

        page.wait_for_timeout(random.randint(1600,2000))
        button.click(timeout=6000)
        button = page.locator('[data-testid="secondaryButton"]')
        button.wait_for(timeout=5010)
        page.wait_for_timeout(random.randint(1600,2000))
        button.click(timeout=6000)
        button = page.locator('[data-testid="secondaryButton"]')
        button.wait_for(timeout=5010)
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

def process_single_flow(task_id=0):
    # 加载配置
    config = load_config()
    enable_oauth2 = config.get('enable_oauth2', False)
    close_browser_after_registration = config.get('close_browser_after_registration', True)
    
    # 根据任务ID选择不同的浏览器
    available_browsers = get_available_browsers()
    browser_list = list(available_browsers.keys())
    
    if browser_list:
        # 轮流使用不同的浏览器
        preferred_browser = browser_list[task_id % len(browser_list)]
        print(f"[Info] - 任务 {task_id + 1} 使用浏览器: {preferred_browser}")
    else:
        preferred_browser = None

    try:
        browser = None
        p = None
        context = None
        browser, p, context = OpenBrowser(preferred_browser)
        
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
                page.wait_for_timeout(5010)  # 等待5秒确保页面加载完成
                return True

            return True
        
        elif not result:
            return False
        
        token_result = get_access_token(page, email)
        if token_result[0]:
            refresh_token, access_token, expire_at =  token_result
            # 更新JSON文件中的token信息
            if save_account_to_json(f"{email}@outlook.com", password, True, refresh_token, access_token, expire_at):
                print(f'[Success: TokenAuth] - {email}@outlook.com')
            else:
                print(f'[Warning] - 保存token数据失败: {email}@outlook.com')
            
            # 根据配置决定是否关闭浏览器
            if not close_browser_after_registration:
                print("[Info] - 注册完成，保持浏览器开启状态以便后续操作")
                # 不关闭浏览器，保持页面开启并返回
                page.wait_for_timeout(5010)  # 等待5秒确保页面加载完成
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
    # 加载配置
    config = load_config()
    close_browser_after_registration = config.get('close_browser_after_registration', True)
    registration_delay = config.get('registration_delay', 60)
    use_random_delay = config.get('use_random_delay', True)
    
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
                if task_counter > 0:  # 第一个任务不延迟
                    # 添加注册间隔延迟
                    if use_random_delay:
                        delay_time = random.randint(registration_delay//2, registration_delay)
                    else:
                        delay_time = registration_delay
                    print(f"[Info] - 等待 {delay_time} 秒后启动下一个注册任务...")
                    time.sleep(delay_time)
                
                new_future = executor.submit(process_single_flow, task_counter)
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
    # 确保data/results目录存在
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    # 加载配置
    config = load_config()
    
    # 从配置文件读取并发数和任务数
    concurrent_flows = config.get('concurrent_flows', 1)
    max_tasks = config.get('max_tasks', 1)

    main(concurrent_flows, max_tasks)