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

        if proxy and proxy.strip():
            launch_options["proxy"] = {"server": proxy, "bypass": "localhost"}
            base_args.append(f"--proxy-server={proxy}")

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

def _click_next_button(page, timeout=10000):
    """点击微软登录/注册流程中的"下一步"按钮，兼容中英文"""
    btn = page.locator(
        'button:has-text("Next"), button:has-text("下一步"), '
        'input[type="submit"][value="Next"], input[type="submit"][value="下一步"], '
        'button[type="submit"]'
    ).first
    btn.click(timeout=timeout)


def _solve_captcha(page):
    """等待通过 hsprotect 按压验证码，返回 True 表示通过。
    
    输出按钮坐标供 AI 浏览器工具使用。
    按压策略：长按 8-12 秒，期间偶尔短暂松开（50-150ms）再按回去，
    进度条满了立即松开，不要多按。
    """
    try:
        page.wait_for_event(
            "request",
            lambda req: req.url.startswith("blob:https://iframe.hsprotect.net/"),
            timeout=22000,
        )
    except:
        if page.get_by_text('一些异常活动').count() > 0:
            print("[Error: Rate limit] - IP 注册频率过快。")
            return False
        print("[Info] - 未检测到 hsprotect 验证码，可能已跳过")
        return True

    page.wait_for_timeout(1500)

    # 尝试获取 #px-captcha 按钮坐标
    btn_info = ""
    for frame in page.frames:
        if 'hsprotect' in frame.url:
            try:
                el = frame.locator('#px-captcha')
                if el.count() > 0 and el.is_visible():
                    box = el.bounding_box()
                    if box:
                        cx = int(box['x'] + box['width'] / 2)
                        cy = int(box['y'] + box['height'] / 2)
                        btn_info = f"按钮坐标: x={cx}, y={cy}, 宽={int(box['width'])}, 高={int(box['height'])}"
            except:
                pass
            break

    print("=" * 50)
    print("[CAPTCHA] - 检测到验证码，需要在浏览器中长按按钮！")
    if btn_info:
        print(f"[CAPTCHA] - {btn_info}")
    print("[CAPTCHA] - 等待操作，最多 120 秒...")
    print("[CAPTCHA] - 提示: 长按 8-12 秒，偶尔短暂松开再按回，进度条满了立即松开")
    print("=" * 50)

    for _ in range(60):
        page.wait_for_timeout(2000)

        if page.get_by_text('一些异常活动').count() > 0:
            print("[Error: Rate limit] - 通过验证码但 IP 注册频率过快。")
            return False

        has_captcha = False
        for frame in page.frames:
            if 'hsprotect' in frame.url:
                try:
                    el = frame.locator('#px-captcha')
                    if el.count() > 0 and el.is_visible():
                        has_captcha = True
                except:
                    pass
                break

        if not has_captcha:
            print("[CAPTCHA] - 验证码已通过 ✓")
            return True

    print("[Error] - 等待超时，验证码未通过。")
    return False


def Outlook_register(page, email, password):
    """注册 Outlook 邮箱，直接走 signup.live.com 注册页面"""
    config = load_config()
    bot_protection_wait = config.get('Bot_protection_wait', 30)

    fake = Faker()
    lastname = fake.last_name()
    firstname = fake.first_name()
    year = str(random.randint(1960, 2005))
    month = str(random.randint(1, 12))
    day = str(random.randint(1, 28))

    SIGNUP_URL = (
        "https://signup.live.com/signup?"
        "wa=wsignin1.0&rpsnv=173&id=292841"
        "&wreply=https%3a%2f%2foutlook.live.com%2fowa%2f%3fnlp%3d1"
        "&cobrandid=90015&lic=1"
    )

    # ── 步骤 1：打开注册页面 ──
    try:
        page.goto(SIGNUP_URL, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # 处理"个人数据导出许可"同意页面（中英文兼容）
        try:
            agree_btn = page.locator(
                'button:has-text("同意并继续"), button:has-text("Agree and continue"), '
                'button:has-text("Accept and continue"), button:has-text("Accept")'
            ).first
            if agree_btn.count() > 0 and agree_btn.is_visible():
                page.wait_for_timeout(1500)
                agree_btn.click(timeout=10000)
                print('[Info] - 已点击"同意并继续"')
                page.wait_for_timeout(3000)
        except:
            pass

        # 等待邮箱输入框出现
        email_input = page.locator(
            '[name="MemberName"], '
            '[name="新建电子邮件"], '
            '[name="New email address"], '
            'input[type="email"]'
        ).first
        email_input.wait_for(state="visible", timeout=20000)
        start_time = time.time()

    except Exception as e:
        try:
            page.screenshot(path="data/debug_register_entry.png")
        except:
            pass
        print(f"[Error] - 无法进入注册页面: {e}")
        return False

    # ── 步骤 2：填写注册表单 ──
    try:
        # 邮箱用户名
        email_input = page.locator(
            '[name="MemberName"], [name="新建电子邮件"], '
            '[name="New email address"], input[type="email"]'
        ).first
        email_input.fill("")
        email_input.type(email, delay=80, timeout=10000)
        page.wait_for_timeout(600)

        _click_next_button(page)
        page.wait_for_timeout(3000)

        # 检查用户名是否可用
        try:
            error_el = page.locator('#MemberNameError')
            if error_el.count() > 0 and error_el.is_visible():
                err_text = error_el.inner_text(timeout=2000).strip()
                if err_text:
                    print(f"[Error] - 邮箱名不可用: {err_text}")
                    return False
        except:
            pass

        # 密码
        pwd_input = page.locator('[name="Password"], [name="PasswordInput"], [type="password"]').first
        pwd_input.wait_for(state="visible", timeout=20000)
        pwd_input.type(password, delay=60, timeout=10000)
        page.wait_for_timeout(500)
        _click_next_button(page)
        page.wait_for_timeout(3000)

        # 国家/地区 + 出生日期
        birth_year_input = page.locator('[name="BirthYear"], input[placeholder="年份"]').first
        birth_year_input.wait_for(state="visible", timeout=15000)
        birth_year_input.fill(year, timeout=10000)
        page.wait_for_timeout(400)

        try:
            page.locator('[name="BirthMonth"]').select_option(value=month, timeout=2000)
            page.wait_for_timeout(800)
            page.locator('[name="BirthDay"]').select_option(value=day)
        except:
            page.locator('[name="BirthMonth"]').click()
            page.wait_for_timeout(400)
            page.locator(f'[role="option"]:text-is("{month}月")').click()
            page.wait_for_timeout(800)
            page.locator('[name="BirthDay"]').click()
            page.wait_for_timeout(400)
            page.locator(f'[role="option"]:text-is("{day}日")').click()
        page.wait_for_timeout(500)

        _click_next_button(page)
        page.wait_for_timeout(3000)

        # 姓名（出生日期之后的步骤）
        lastname_input = page.locator(
            '#lastNameInput, [name="LastName"], '
            'input[aria-label="姓氏"], input[aria-label="Last name"]'
        ).first
        lastname_input.wait_for(state="visible", timeout=15000)
        lastname_input.type(lastname, delay=100, timeout=10000)
        page.wait_for_timeout(500)

        firstname_input = page.locator(
            '#firstNameInput, [name="FirstName"], '
            'input[aria-label="名字"], input[aria-label="First name"]'
        ).first
        firstname_input.fill(firstname, timeout=10000)
        page.wait_for_timeout(500)

        # 确保等够 bot_protection_wait 秒
        if time.time() - start_time < bot_protection_wait:
            wait_left = (bot_protection_wait - (time.time() - start_time)) * 1000
            page.wait_for_timeout(int(wait_left))

        _click_next_button(page)
        page.wait_for_timeout(2000)

    except Exception as e:
        try:
            page.screenshot(path="data/debug_register_form.png")
        except:
            pass
        print(f"[Error] - 填写注册表单失败: {e}")
        return False

    # ── 步骤 3：处理验证码 ──
    try:
        if page.get_by_text('一些异常活动').count() > 0:
            print("[Error: IP] - 当前 IP 注册频率过快。")
            return False

        if page.locator('iframe#enforcementFrame').count() > 0:
            print("[Error: FunCaptcha] - 验证码类型错误，非按压验证码。")
            return False

        if not _solve_captcha(page):
            return False

    except Exception as e:
        print(f"[Error] - 验证码处理失败: {e}")
        return False

    # ── 步骤 4：跳过注册后的向导页面，直到进入邮箱 ──
    page.wait_for_timeout(3000)

    def _is_in_mailbox():
        url = page.url
        return "outlook.live.com/mail" in url or "outlook.live.com/owa" in url

    for _ in range(20):
        if _is_in_mailbox():
            break

        # 如果被重定向到微软宣传页，直接导航到邮箱
        if "microsoft.com/" in page.url and "outlook.live.com" not in page.url:
            try:
                page.goto("https://outlook.live.com/mail/0/", timeout=20000, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)
                continue
            except:
                pass

        # 跳过 / 以后再说
        try:
            skip = page.locator(
                '[data-testid="secondaryButton"], '
                'a:has-text("暂时跳过"), a:has-text("Skip"), '
                'button:has-text("跳过"), button:has-text("Skip")'
            ).first
            if skip.count() > 0 and skip.is_visible():
                skip.click(timeout=3000)
                page.wait_for_timeout(random.randint(1500, 2500))
                continue
        except:
            pass

        # 保持登录？
        try:
            no_btn = page.locator('button:has-text("否"), button:has-text("No")')
            if no_btn.count() > 0 and no_btn.first.is_visible():
                no_btn.first.click(timeout=3000)
                page.wait_for_timeout(2000)
                continue
        except:
            pass

        # 是（保持登录也行）
        try:
            yes_btn = page.locator('button:has-text("是"), button:has-text("Yes")')
            if yes_btn.count() > 0 and yes_btn.first.is_visible():
                yes_btn.first.click(timeout=3000)
                page.wait_for_timeout(2000)
                continue
        except:
            pass

        # 取消（通行密钥等）
        try:
            cancel = page.locator('button:has-text("取消"), button:has-text("Cancel")')
            if cancel.count() > 0 and cancel.first.is_visible():
                cancel.first.click(timeout=3000)
                page.wait_for_timeout(2000)
                continue
        except:
            pass

        # 确定
        try:
            ok_btn = page.locator('button:has-text("确定"), button:has-text("OK")')
            if ok_btn.count() > 0 and ok_btn.first.is_visible():
                ok_btn.first.click(timeout=3000)
                page.wait_for_timeout(2000)
                continue
        except:
            pass

        page.wait_for_timeout(2000)

    # 如果还没到邮箱页面，主动导航
    if not _is_in_mailbox():
        try:
            page.goto("https://outlook.live.com/mail/0/", timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(8000)
        except:
            pass

    # ── 步骤 5：确认注册成功并保存 ──
    if _is_in_mailbox():
        # 排除 440 错误
        try:
            body_text = page.locator('body').inner_text(timeout=3000)
            if 'Something went wrong' in body_text:
                print(f"[Error] - Outlook 报错 440")
                return False
        except:
            pass
        if save_account_to_json(f"{email}@outlook.com", password):
            print(f'[Success: Email Registration] - {email}@outlook.com: {password}')
        else:
            print(f'[Warning] - 保存账号数据失败: {email}@outlook.com')
        return True

    # 验证码已通过，即使没进入邮箱也认为注册大概率成功
    if save_account_to_json(f"{email}@outlook.com", password):
        print(f'[Success: Email Registration] - {email}@outlook.com: {password} (未确认邮箱页面)')
    return True


def process_single_flow(task_id=0):
    """单个注册任务：启动浏览器 → 注册 Outlook → 关闭"""
    config = load_config()
    close_browser = config.get('close_browser_after_registration', True)

    available_browsers = get_available_browsers()
    browser_list = list(available_browsers.keys())
    if browser_list:
        preferred_browser = browser_list[task_id % len(browser_list)]
        print(f"[Info] - 任务 {task_id + 1} 使用浏览器: {preferred_browser}")
    else:
        preferred_browser = None

    p = None
    context = None
    browser = None

    try:
        if config.get('use_incognito_mode', True):
            p, context = OpenBrowserPersistent()
            if context is None:
                print("[Error] - 无法启动浏览器（无痕模式）")
                return False
            page = context.pages[0] if context.pages else context.new_page()
        else:
            browser, p, context = OpenBrowser(preferred_browser)
            if browser is None or p is None or context is None:
                print("[Error] - 无法启动浏览器")
                return False
            page = context.new_page()

        email = random_email(random.randint(12, 14))
        password = generate_strong_password(random.randint(11, 15))
        result = Outlook_register(page, email, password)

        if result and not close_browser:
            print("[Info] - 注册完成，保持浏览器开启")
            page.wait_for_timeout(5000)

        return result

    except Exception as e:
        print(f"[Error] - 任务异常: {e}")
        return False

    finally:
        if close_browser:
            for obj in [context, browser]:
                try:
                    if obj:
                        obj.close()
                except:
                    pass
            try:
                if p:
                    p.stop()
            except:
                pass

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