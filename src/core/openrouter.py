import time
import json
import re
from pathlib import Path
from datetime import datetime
from .register import OpenBrowser, OpenBrowserPersistent, load_accounts_from_json, load_config, generate_strong_password


def mark_account_failed(email, reason=""):
    """标记账号为失败状态"""
    accounts_json = Path('data/accounts.json')
    try:
        with open(accounts_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for account in data['accounts']:
            if account['email'] == email:
                account['openrouter'] = False
                account['status'] = 'unavailable'
                account['notes'] = f"OpenRouter注册失败: {reason}"
                account['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                break

        with open(accounts_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[Info] - 已标记 {email} 为失败状态: {reason}")
        return True

    except Exception as e:
        print(f"[Error] - 更新账号状态失败: {e}")
        return False


def wait_for_human_captcha(page, context_hint=""):
    """检测人机验证并等待用户手动处理"""
    captcha_keywords = [
        'captcha', 'challenge', 'verify you are human', 'robot',
        'recaptcha', 'hcaptcha', 'turnstile', 'cf-challenge',
        'are you a human', 'security check', 'bot detection',
    ]
    try:
        url = page.url.lower()
        body_text = page.locator('body').inner_text(timeout=3000).lower()
        has_captcha = any(kw in url or kw in body_text for kw in captcha_keywords)

        iframe_captcha = page.locator('iframe[src*="captcha"], iframe[src*="challenge"], iframe[src*="recaptcha"], iframe[src*="hcaptcha"], iframe[src*="turnstile"]')
        if iframe_captcha.count() > 0:
            has_captcha = True

        if has_captcha:
            print(f"\n{'!'*60}")
            print(f"[⚠️ 人机检测] - {context_hint}")
            print(f"[⚠️ 人机检测] - 请在浏览器中手动完成验证！")
            print(f"[⚠️ 人机检测] - 完成后程序将自动继续...")
            print(f"{'!'*60}\n")
            for _ in range(120):
                page.wait_for_timeout(3000)
                try:
                    new_body = page.locator('body').inner_text(timeout=3000).lower()
                    still_captcha = any(kw in new_body for kw in captcha_keywords)
                    new_iframe = page.locator('iframe[src*="captcha"], iframe[src*="challenge"], iframe[src*="recaptcha"], iframe[src*="hcaptcha"], iframe[src*="turnstile"]')
                    if not still_captcha and new_iframe.count() == 0:
                        print("[Info] - 人机检测已通过，继续执行...")
                        return True
                except:
                    pass
            print("[Error] - 等待人机检测超时（6分钟）")
            return False
    except:
        pass
    return True


def login_outlook(page, email, password):
    """登录 Outlook 邮箱 Web 版（直接访问 Outlook 登录）"""
    try:
        page.goto("https://login.live.com/login.srf?wa=wsignin1.0&rpsnv=173&id=292841&wreply=https%3a%2f%2foutlook.live.com%2fowa%2f%3fnlp%3d1&cobrandid=90015",
                   timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        if "outlook.live.com/mail" in page.url:
            print(f"[Info] - {email} 已经登录 Outlook")
            return page

        wait_for_human_captcha(page, "Outlook 登录页")

        page.locator('input[type="email"]').fill(email, timeout=15000)
        page.wait_for_timeout(800)
        page.get_by_role("button", name="下一步").click(timeout=10000)
        page.wait_for_timeout(3000)

        wait_for_human_captcha(page, "输入邮箱后")

        page.locator('input[type="password"]').wait_for(state="visible", timeout=15000)
        page.locator('input[type="password"]').fill(password, timeout=10000)
        page.wait_for_timeout(800)

        # 密码页面按钮可能是"登录"、"下一步"或"Sign in"
        signin_btn = page.locator('button:has-text("登录"), button:has-text("下一步"), button:has-text("Sign in")').first
        signin_btn.click(timeout=10000)
        page.wait_for_timeout(3000)

        wait_for_human_captcha(page, "输入密码后")

        for _ in range(15):
            if "outlook.live.com/mail" in page.url:
                break

            # "保持登录状态?" -> 点"否"
            try:
                no_btn = page.get_by_role("button", name="否")
                if no_btn.count() > 0 and no_btn.is_visible():
                    no_btn.click(timeout=5000)
                    page.wait_for_timeout(3000)
                    continue
            except:
                pass

            # "是" 也行（保持登录）
            try:
                yes_btn = page.get_by_role("button", name="是")
                if yes_btn.count() > 0 and yes_btn.is_visible():
                    yes_btn.click(timeout=5000)
                    page.wait_for_timeout(3000)
                    continue
            except:
                pass

            # "暂时跳过"
            try:
                skip_link = page.locator('a:has-text("暂时跳过"), a:has-text("Skip")')
                if skip_link.count() > 0 and skip_link.first.is_visible():
                    skip_link.first.click(timeout=5000)
                    page.wait_for_timeout(3000)
                    continue
            except:
                pass

            # "取消"（通行密钥相关）
            try:
                cancel_btn = page.get_by_role("button", name="取消")
                if cancel_btn.count() > 0 and cancel_btn.is_visible():
                    cancel_btn.click(timeout=5000)
                    page.wait_for_timeout(3000)
                    continue
            except:
                pass

            # "确定"
            try:
                ok_btn = page.get_by_role("button", name="确定")
                if ok_btn.count() > 0 and ok_btn.is_visible():
                    ok_btn.click(timeout=5000)
                    page.wait_for_timeout(3000)
                    continue
            except:
                pass

            # Something went wrong / Error 440 -> 需要重试
            try:
                error_text = page.locator('body').inner_text(timeout=2000)
                if 'Something went wrong' in error_text or 'Error: 440' in error_text:
                    print(f"[Warning] - Outlook 出现 440 错误，尝试刷新...")
                    page.goto("https://outlook.live.com/mail/0/", timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(5000)
                    continue
            except:
                pass

            wait_for_human_captcha(page, "登录后中间页面")
            page.wait_for_timeout(2000)

        # 最终检查是否到了邮箱页面
        if "outlook.live.com/mail" not in page.url:
            page.goto("https://outlook.live.com/mail/0/", timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(8000)

        if "outlook.live.com/mail" in page.url or "outlook.live.com/owa" in page.url:
            # 检查是否是 440 错误页面
            try:
                body = page.locator('body').inner_text(timeout=3000)
                if 'Something went wrong' in body:
                    print(f"[Error] - {email} Outlook 报错 440，可能是 UA/Cookie 问题")
                    return None
            except:
                pass
            print(f"[Success] - {email} 登录 Outlook 成功")
            return page

        print(f"[Error] - {email} 登录 Outlook 失败，最终 URL: {page.url}")
        return None

    except Exception as e:
        print(f"[Error] - {email} 登录 Outlook 失败: {e}")
        return None


def get_verification_link(page, max_wait=180):
    """从 Outlook 收件箱获取最新的 OpenRouter 验证链接"""
    print("[Info] - 等待验证邮件...")
    start_time = time.time()
    found_old_mail = False

    while time.time() - start_time < max_wait:
        try:
            page.reload(wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(3000)

            # 找到所有 OpenRouter 相关邮件
            all_mails = page.locator('[role="listbox"] [role="option"]').filter(
                has=page.locator('text=OpenRouter')
            )
            mail_count = all_mails.count()

            if mail_count == 0:
                # 备选匹配
                all_mails = page.locator('[role="listbox"] [role="option"]').filter(
                    has=page.locator('text=sign up link')
                )
                mail_count = all_mails.count()

            if mail_count > 0:
                # 点击第一封（最新的，Outlook 默认最新在上面）
                latest_mail = all_mails.nth(0)
                print(f"[Info] - 找到 {mail_count} 封 OpenRouter 邮件，点击最新一封")
                latest_mail.click(timeout=5000)
                page.wait_for_timeout(3000)

                # 检查是否是未读/最新的验证邮件
                # 从邮件正文中提取验证链接
                try:
                    signup_link = page.locator('[role="document"] a:has-text("Sign up to OpenRouter")').first
                    if signup_link.count() > 0:
                        href = signup_link.get_attribute('href')
                        if href and 'clerk.openrouter.ai/v1/verify' in href:
                            print(f"[Success] - 获取到验证链接")
                            return href
                except:
                    pass

                try:
                    click_here = page.locator('[role="document"] a:has-text("click here")').first
                    if click_here.count() > 0:
                        href = click_here.get_attribute('href')
                        if href and 'clerk.openrouter.ai/v1/verify' in href:
                            print(f"[Success] - 获取到验证链接(click here)")
                            return href
                except:
                    pass

                # 尝试从邮件 HTML 里用正则提取任何验证链接
                try:
                    doc = page.locator('[role="document"]')
                    all_links = doc.locator('a[href*="clerk.openrouter.ai/v1/verify"]')
                    if all_links.count() > 0:
                        href = all_links.first.get_attribute('href')
                        if href:
                            print(f"[Success] - 获取到验证链接（通过 href 匹配）")
                            return href
                except:
                    pass

                if not found_old_mail:
                    found_old_mail = True
                    print("[Info] - 找到了 OpenRouter 邮件但可能是旧邮件，等待最新邮件...")

            elapsed = int(time.time() - start_time)
            print(f"[Info] - 未找到新验证邮件，等待 10 秒后重试...（已等 {elapsed}s）")
            page.wait_for_timeout(10000)

        except Exception as e:
            print(f"[Warning] - 获取验证链接时出错: {e}")
            page.wait_for_timeout(5000)

    print("[Error] - 等待验证邮件超时")
    return None


def click_verification_link(page, verification_url):
    """在同一个 OpenRouter 页面中打开验证链接（保持 session 连续）"""
    try:
        print("[Info] - 在 OpenRouter 窗口中访问验证链接...")
        page.goto(verification_url, timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        for i in range(20):
            current_url = page.url
            # clerk_status=verified 表示邮箱已验证
            if "clerk_status=verified" in current_url or "__clerk_created_session" in current_url:
                print(f"[Success] - 邮箱验证通过: {current_url[:100]}")
                # 可能停在 sign-up/continue 页面，等待自动跳转或手动导航
                page.wait_for_timeout(5000)
                # 检查是否有继续按钮
                try:
                    for btn_text in ["Continue", "Get started", "完成", "Go to dashboard"]:
                        btn = page.locator(f'button:has-text("{btn_text}"), a:has-text("{btn_text}")').first
                        if btn.count() > 0 and btn.is_visible():
                            print(f"[Info] - 点击 '{btn_text}' 按钮...")
                            btn.click(timeout=5000)
                            page.wait_for_timeout(3000)
                            break
                except:
                    pass
                # 直接导航到 OpenRouter 首页确认登录态
                if "sign-up" in page.url or "sign-in" in page.url:
                    page.goto("https://openrouter.ai/", timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3000)
                return page

            if "openrouter.ai" in current_url and "clerk" not in current_url and "sign-up" not in current_url and "verify" not in current_url:
                print(f"[Success] - 验证成功，已登录 OpenRouter: {current_url}")
                page.wait_for_timeout(2000)
                return page

            page.wait_for_timeout(3000)

        print(f"[Warning] - 验证链接访问后未自动跳转，当前URL: {page.url}")
        return page if "openrouter.ai" in page.url else None

    except Exception as e:
        print(f"[Error] - 访问验证链接失败: {e}")
        return None


def register_openrouter(page, email, password):
    """在 OpenRouter 注册页面填写表单并提交"""
    try:
        page.goto("https://openrouter.ai/sign-up", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        wait_for_human_captcha(page, "OpenRouter 注册页")

        # 填写邮箱
        email_input = page.get_by_role("textbox", name="Email address")
        email_input.fill(email, timeout=10000)
        page.wait_for_timeout(500)

        # 填写密码
        password_input = page.get_by_role("textbox", name="Password")
        password_input.fill(password, timeout=10000)
        page.wait_for_timeout(500)

        # 勾选同意条款
        try:
            checkbox = page.locator('input[type="checkbox"], [role="checkbox"]').first
            if checkbox.count() > 0:
                if not checkbox.is_checked():
                    checkbox.click(timeout=5000)
                    page.wait_for_timeout(300)
                    if checkbox.is_checked():
                        print("[Info] - 已勾选同意条款")
                    else:
                        print("[Warning] - 勾选条款可能未成功，尝试 JS 点击")
                        checkbox.evaluate("el => el.click()")
                        page.wait_for_timeout(300)
                else:
                    print("[Info] - 条款已勾选")
            else:
                print("[Warning] - 未找到 checkbox 元素")
        except Exception as e:
            print(f"[Warning] - 勾选条款异常: {e}")

        page.wait_for_timeout(500)

        # 点击 Continue
        try:
            continue_btn = page.get_by_role("button", name="Continue")
            if continue_btn.count() > 0:
                continue_btn.click(timeout=10000)
                print("[Info] - 已点击 Continue 按钮")
            else:
                print("[Warning] - 未找到 Continue 按钮")
                return 'error'
        except Exception as e:
            print(f"[Error] - 点击 Continue 失败: {e}")
            return 'error'

        # 等待 Continue 按钮加载完成（最多等60秒）
        print("[Info] - 等待注册请求完成...")
        for wait_i in range(20):
            page.wait_for_timeout(3000)

            current_url = page.url
            if "verify-email-address" in current_url or "sign-up" not in current_url:
                print(f"[Info] - 页面已跳转: {current_url}")
                break

            # 检查 Continue 按钮是否还在 loading
            try:
                btn = page.get_by_role("button", name="Continue")
                if btn.count() > 0 and btn.is_enabled():
                    print(f"[Debug] - Continue 按钮重新可用（{(wait_i+1)*3}s），可能有错误")
                    break
            except:
                pass

            # 检查页面是否出现了错误或验证相关内容
            try:
                body = page.locator('body').inner_text(timeout=2000)
                if 'already' in body.lower() and ('exists' in body.lower() or 'taken' in body.lower()):
                    print("[Warning] - 该邮箱已在 OpenRouter 注册过")
                    return 'already_exists'
                if 'Verify your email' in body or 'verify-email' in current_url:
                    print("[Info] - 需要验证邮箱")
                    return 'need_link_verification'
            except:
                pass

            if wait_i % 5 == 4:
                print(f"[Info] - 仍在等待注册请求...({(wait_i+1)*3}s)")

        page.wait_for_timeout(2000)

        # 截图保存以便调试
        try:
            screenshot_path = str(Path('data') / 'openrouter_after_submit.png')
            page.screenshot(path=screenshot_path)
            print(f"[Debug] - 截图已保存: {screenshot_path}")
        except:
            pass

        # 检查是否有 Turnstile/Cloudflare 验证
        try:
            turnstile = page.locator('iframe[src*="turnstile"], iframe[src*="challenges.cloudflare.com"], [data-sitekey], .cf-turnstile')
            if turnstile.count() > 0:
                print("\n[⚠️ 人机检测] - 检测到 Cloudflare Turnstile 验证！")
                print("[⚠️ 人机检测] - 请在浏览器中手动完成验证！")
                for _ in range(60):
                    page.wait_for_timeout(3000)
                    if turnstile.count() == 0 or page.url != "https://openrouter.ai/sign-up":
                        print("[Info] - Turnstile 验证已完成")
                        break
                page.wait_for_timeout(3000)
        except:
            pass

        # 再检查一次页面文本
        try:
            all_text = page.locator('body').inner_text(timeout=3000)
            form_errors = [line.strip() for line in all_text.split('\n')
                          if line.strip() and ('error' in line.lower() or 'invalid' in line.lower()
                                              or 'already' in line.lower() or 'verify' in line.lower()
                                              or 'check' in line.lower() or 'too many' in line.lower())]
            if form_errors:
                print(f"[Debug] - 页面消息: {form_errors}")
        except:
            pass

        wait_for_human_captcha(page, "OpenRouter 注册提交后")

        # 等待页面跳转或状态变化（最多再等30秒）
        for i in range(10):
            current_url = page.url

            if "verify-email-address" in current_url:
                print("[Info] - 需要邮箱验证（链接方式）")
                return 'need_link_verification'

            if "openrouter.ai" in current_url and "sign-up" not in current_url:
                print("[Success] - OpenRouter 注册成功（无需验证）")
                return 'success'

            try:
                body = page.locator('body').inner_text(timeout=3000)
                if 'already exists' in body.lower() or 'already been taken' in body.lower():
                    print("[Warning] - 该邮箱已在 OpenRouter 注册过")
                    return 'already_exists'
                if 'verify' in body.lower() and 'email' in body.lower() and 'sign-up' not in current_url:
                    print("[Info] - 需要邮箱验证")
                    return 'need_link_verification'
                if 'Verify your email' in body or 'verify your email' in body:
                    print("[Info] - 需要验证邮箱")
                    return 'need_link_verification'
            except:
                pass

            if i == 0:
                print(f"[Debug] - 提交后 URL: {current_url}")

            page.wait_for_timeout(3000)

        current_url = page.url
        print(f"[Info] - 页面状态未知，URL: {current_url}")
        if "sign-up" in current_url:
            try:
                page_text = page.locator('body').inner_text(timeout=3000)
                # 显示页面上的错误信息
                error_lines = [l.strip() for l in page_text.split('\n') if l.strip() and len(l.strip()) < 200]
                print(f"[Debug] - 页面内容片段: {error_lines[:10]}")
            except:
                pass
            print("[Warning] - 仍在注册页面，可能提交失败或被拦截")
            return 'error'
        return 'need_link_verification'

    except Exception as e:
        print(f"[Error] - OpenRouter 注册失败: {e}")
        return 'error'


def get_verification_code(page, max_wait=120):
    """从 Outlook 收件箱获取最新的 OpenRouter 验证码（6位数字）。
    邮件标题格式: 'XXXXXX is your verification code'
    """
    print("[Info] - 等待最新 OpenRouter 验证码邮件...")
    start_time = time.time()
    last_code = None

    while time.time() - start_time < max_wait:
        try:
            page.reload(wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(3000)

            # 匹配包含 "verification code" 的邮件（标题中含验证码数字）
            all_mails = page.locator('[role="listbox"] [role="option"]').filter(
                has=page.locator('text=verification code')
            )
            if all_mails.count() == 0:
                all_mails = page.locator('[role="listbox"] [role="option"]').filter(
                    has=page.locator('text=OpenRouter')
                )

            if all_mails.count() > 0:
                # 先从邮件列表项的标题文本中直接提取验证码（避免点击后正文未切换的问题）
                latest_mail = all_mails.nth(0)
                try:
                    mail_text = latest_mail.inner_text(timeout=3000)
                    title_match = re.search(r'(\d{6})\s*is your verificat', mail_text)
                    if not title_match:
                        title_match = re.search(r'(\d{6})', mail_text)
                    if title_match:
                        code = title_match.group(1)
                        if code != last_code:
                            print(f"[Success] - 从邮件标题获取到最新验证码: {code}")
                            return code
                        else:
                            print(f"[Info] - 验证码 {code} 与之前相同，等待新邮件...")
                except:
                    pass

                # 备用：点击邮件读正文
                latest_mail.click(timeout=5000)
                page.wait_for_timeout(3000)
                try:
                    doc = page.locator('[role="document"]')
                    if doc.count() > 0:
                        body_text = doc.inner_text(timeout=5000)
                        code_match = re.search(r'\b(\d{6})\b', body_text)
                        if code_match:
                            code = code_match.group(1)
                            if code != last_code:
                                print(f"[Success] - 从邮件正文获取到验证码: {code}")
                                return code
                            last_code = code
                except:
                    pass

            elapsed = int(time.time() - start_time)
            print(f"[Info] - 未找到新验证码，等待 8 秒后重试...（已等 {elapsed}s）")
            page.wait_for_timeout(8000)

        except Exception as e:
            print(f"[Warning] - 获取验证码时出错: {e}")
            page.wait_for_timeout(5000)

    print("[Error] - 等待验证码邮件超时")
    return None


def login_and_create_key(page, email, password, outlook_page=None, key_name="auto-key"):
    """通过 OpenRouter 登录页面登录后创建 API Key，支持 factor-two 邮件验证码"""
    try:
        page.goto("https://openrouter.ai/sign-in", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        wait_for_human_captcha(page, "OpenRouter 登录页")

        email_input = page.get_by_role("textbox", name="Email address")
        if email_input.count() > 0:
            email_input.fill(email, timeout=5000)
            page.wait_for_timeout(500)

        pwd_input = page.get_by_role("textbox", name="Password")
        if pwd_input.count() > 0:
            pwd_input.fill(password, timeout=5000)
            page.wait_for_timeout(500)

        page.get_by_role("button", name="Continue").click(timeout=10000)
        print("[Info] - 等待 OpenRouter 登录...")
        page.wait_for_timeout(5000)

        # 检查是否需要 factor-two 邮件验证码
        if "factor-two" in page.url or "factor" in page.url:
            print("[Info] - 需要邮件验证码（factor-two），等待邮件发送...")
            if outlook_page is None:
                print("[Warning] - 没有 Outlook 页面，无法获取验证码")
                return None

            # 等几秒让验证码邮件发出并到达
            page.wait_for_timeout(5000)

            # 去 Outlook 获取验证码
            outlook_page.bring_to_front()
            code = get_verification_code(outlook_page)
            if not code:
                print("[Error] - 获取验证码失败")
                return None

            # 回到 OpenRouter 填入验证码（6个独立输入框，需逐字符输入）
            page.bring_to_front()
            page.wait_for_timeout(1000)

            # 先点击第一个验证码输入框获取焦点
            code_input = page.get_by_role("textbox", name="Enter verification code")
            if code_input.count() == 0:
                code_input = page.locator('input[type="text"]').first
            if code_input.count() > 0:
                code_input.click(timeout=5000)
                page.wait_for_timeout(500)

            # 逐字符键入验证码（自动跳到下一个输入框）
            page.keyboard.type(code, delay=100)
            print(f"[Info] - 已输入验证码: {code}")
            page.wait_for_timeout(2000)

            # 点击 Continue（可能自动提交了）
            try:
                cont_btn = page.get_by_role("button", name="Continue")
                if cont_btn.count() > 0 and cont_btn.is_enabled():
                    cont_btn.click(timeout=5000)
            except:
                pass
            page.wait_for_timeout(5000)

            # 截图看提交后的状态
            try:
                page.screenshot(path=str(Path('data') / 'openrouter_after_code.png'))
                print(f"[Debug] - 验证码提交后 URL: {page.url}")
            except:
                pass

        # 等待登录完成
        for _ in range(10):
            page.wait_for_timeout(3000)
            wait_for_human_captcha(page, "OpenRouter 登录中")
            if "sign-in" not in page.url and "factor" not in page.url:
                break

        if "sign-in" not in page.url and "factor" not in page.url:
            print("[Success] - OpenRouter 登录成功")
            return create_api_key(page, key_name)

        print("[Warning] - OpenRouter 登录失败")
        try:
            page.screenshot(path=str(Path('data') / 'openrouter_login_failed.png'))
        except:
            pass
        return None

    except Exception as e:
        print(f"[Error] - OpenRouter 登录创建 Key 失败: {e}")
        return None


def _extract_api_key(page):
    """从页面中提取 API Key"""
    # 方式1: 从 code 元素
    try:
        for code_el in page.locator('code').all():
            text = code_el.inner_text(timeout=2000)
            if text and text.startswith("sk-or-"):
                return text
    except:
        pass

    # 方式2: 正则匹配页面文本
    try:
        page_text = page.inner_text("body", timeout=3000)
        key_match = re.search(r'(sk-or-v1-[a-f0-9]{64})', page_text)
        if key_match:
            return key_match.group(1)
        key_match = re.search(r'(sk-or-[a-zA-Z0-9-]{20,})', page_text)
        if key_match:
            return key_match.group(1)
    except:
        pass

    # 方式3: 从 input/textarea
    try:
        for inp in page.locator('input[readonly], input[type="text"], textarea').all():
            val = inp.input_value(timeout=2000)
            if val and val.startswith("sk-or-"):
                return val
    except:
        pass

    # 方式4: 从 dialog/modal 中
    try:
        for el in page.locator('[role="dialog"] code, [role="dialog"] input, #headlessui-portal-root code, #headlessui-portal-root input').all():
            text = el.inner_text(timeout=1000) if el.evaluate("e => e.tagName") == 'CODE' else el.input_value(timeout=1000)
            if text and text.startswith("sk-or-"):
                return text
    except:
        pass

    return None


def create_api_key(page, key_name="auto-key"):
    """登录后创建 API Key"""
    try:
        # 先确认 OpenRouter 登录状态
        if "openrouter.ai/settings/keys" not in page.url:
            page.goto("https://openrouter.ai/settings/keys", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        # 如果被重定向到登录页，可能 session 还没完全建立，等一下重试
        if "sign-in" in page.url:
            print("[Info] - 被重定向到登录页，等待后重试...")
            page.go_back()
            page.wait_for_timeout(3000)
            page.goto("https://openrouter.ai/settings/keys", timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

        if "sign-in" in page.url:
            print("[Warning] - 需要登录才能创建 API Key，跳过")
            return None

        # 处理可能的弹出层（如 "Where did you first hear about OpenRouter?" 问卷）
        try:
            page.screenshot(path=str(Path('data') / 'openrouter_keys_page.png'))

            # 如果有来源问卷弹窗，随便选一个然后点 Continue
            survey_btn = page.locator('button:has-text("Other"), button:has-text("Not sure")').first
            if survey_btn.count() > 0 and survey_btn.is_visible():
                survey_btn.click(timeout=3000)
                page.wait_for_timeout(500)
                continue_btn = page.locator('button:has-text("Continue")').first
                if continue_btn.count() > 0 and continue_btn.is_visible():
                    continue_btn.click(timeout=3000)
                    page.wait_for_timeout(2000)
                    print("[Info] - 已关闭来源问卷弹窗")

            # 按 Escape 关闭其他弹窗
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)
        except:
            pass

        # 尝试多种方式找到创建按钮
        create_btn = None
        for selector in [
            'button:has-text("Create Key")',
            'button:has-text("Create")',
            'button:has-text("New Key")',
            'button:has-text("Generate")',
            'a:has-text("Create Key")',
            'a:has-text("Create")',
        ]:
            el = page.locator(selector).first
            if el.count() > 0 and el.is_visible():
                create_btn = el
                break

        if not create_btn:
            print("[Warning] - 未找到创建 Key 按钮，尝试截图调试")
            try:
                body = page.locator('body').inner_text(timeout=3000)
                print(f"[Debug] - Keys 页面内容: {body[:300]}")
            except:
                pass
            return None

        # 用 force 点击，避免被覆盖层阻挡
        create_btn.click(timeout=10000, force=True)
        page.wait_for_timeout(3000)

        # 截图看弹窗状态
        try:
            page.screenshot(path=str(Path('data') / 'openrouter_after_create_click.png'))
        except:
            pass

        # 填写 Key 名称（可能在模态框中）
        name_filled = False
        for name_sel in [
            'input[name="name"]',
            'input[placeholder*="Name"]',
            'input[placeholder*="name"]',
            'input[placeholder*="key"]',
            'input[placeholder*="Key"]',
            'dialog input[type="text"]',
            '[role="dialog"] input[type="text"]',
            '#headlessui-portal-root input[type="text"]',
        ]:
            inp = page.locator(name_sel).first
            if inp.count() > 0:
                try:
                    inp.fill(key_name, timeout=3000)
                    name_filled = True
                    print(f"[Info] - 已填写 Key 名称: {key_name}")
                    break
                except:
                    continue
        if not name_filled:
            name_input2 = page.get_by_role("textbox").first
            if name_input2.count() > 0:
                try:
                    name_input2.fill(key_name, timeout=3000)
                    name_filled = True
                except:
                    pass
        page.wait_for_timeout(500)

        # 确认创建（模态框中的提交按钮）
        submitted = False
        for selector in [
            'button:has-text("Create Key")',
            'button[type="submit"]',
            '[role="dialog"] button:has-text("Create")',
            '#headlessui-portal-root button:has-text("Create")',
            'button:has-text("Create")',
            'button:has-text("Generate")',
        ]:
            btn = page.locator(selector).first
            try:
                if btn.count() > 0 and btn.is_visible():
                    btn.click(timeout=5000, force=True)
                    submitted = True
                    print(f"[Info] - 点击了确认创建按钮")
                    break
            except:
                continue

        if not submitted:
            # 可能没有名称填写步骤，Create 按钮直接创建了
            print("[Info] - 可能已直接创建（无需确认按钮）")

        page.wait_for_timeout(5000)

        # 截图看创建后的状态
        try:
            page.screenshot(path=str(Path('data') / 'openrouter_after_key_created.png'))
        except:
            pass

        # 获取生成的 API Key - 多种方式
        api_key = _extract_api_key(page)
        if api_key:
            print(f"[Success] - 创建 API Key 成功: {api_key[:20]}...")
            return api_key

        print("[Error] - 未能获取到 API Key")
        try:
            body = page.locator('body').inner_text(timeout=3000)
            print(f"[Debug] - 页面内容: {body[:500]}")
        except:
            pass
        return None

    except Exception as e:
        print(f"[Error] - 创建 API Key 失败: {e}")
        return None


def update_account_openrouter(email, api_key, status="available"):
    """更新 accounts.json 中的 openrouter 状态和 api_key，并触发邮件通知"""
    accounts_json = Path('data/accounts.json')
    try:
        with open(accounts_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for account in data['accounts']:
            if account['email'] == email:
                account['openrouter'] = True if api_key else False
                account['openrouter_api_key'] = api_key if api_key else ""
                account['status'] = status
                account['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                break

        with open(accounts_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[Success] - 已更新 {email} 的 OpenRouter 信息")

        if api_key:
            try:
                from ..utils.email_notify import notify_new_api_key, record_new_key
                record_new_key(email, api_key)
                notify_new_api_key(email, api_key)
            except Exception as e:
                print(f"[Warning] - 邮件通知/记录失败（不影响主流程）: {e}")

        return True

    except Exception as e:
        print(f"[Error] - 更新账号信息失败: {e}")
        return False


def process_single_account(account):
    """处理单个账号的完整流程：登录Outlook -> 注册OpenRouter -> 获取验证链接 -> 创建API Key
    使用两个独立的 Chrome 原生无痕窗口，避免 Cookie 冲突和 CAPTCHA 问题。
    """
    email = account['email']
    password = account['password']

    print(f"\n{'='*60}")
    print(f"[Start] - 开始处理账号: {email}")
    print(f"{'='*60}")

    pw = None
    outlook_ctx = None
    openrouter_ctx = None

    try:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()

        # 步骤1: 启动第一个无痕窗口，登录 Outlook
        print("[Info] - 启动 Outlook 无痕窗口...")
        pw, outlook_ctx = OpenBrowserPersistent(playwright_instance=pw)
        if outlook_ctx is None:
            print("[Error] - 无法启动 Outlook 浏览器")
            mark_account_failed(email, "无法启动浏览器")
            return False

        outlook_page = outlook_ctx.pages[0] if outlook_ctx.pages else outlook_ctx.new_page()
        outlook_page = login_outlook(outlook_page, email, password)
        if outlook_page is None:
            print(f"[Error] - {email} Outlook 登录失败，跳过此账号")
            mark_account_failed(email, "Outlook登录失败")
            return False

        # 步骤2: 用同一个 Playwright 实例启动第二个独立无痕窗口
        print("[Info] - 启动 OpenRouter 独立无痕窗口...")
        pw, openrouter_ctx = OpenBrowserPersistent(playwright_instance=pw)
        if openrouter_ctx is None:
            print("[Error] - 无法启动 OpenRouter 浏览器")
            mark_account_failed(email, "无法启动浏览器")
            return False

        openrouter_page = openrouter_ctx.pages[0] if openrouter_ctx.pages else openrouter_ctx.new_page()
        result = register_openrouter(openrouter_page, email, password)

        if result == 'error':
            print(f"[Error] - {email} OpenRouter 注册出错")
            mark_account_failed(email, "OpenRouter注册出错")
            return False

        if result == 'already_exists':
            print(f"[Info] - {email} 已注册过 OpenRouter，尝试直接创建 API Key")
            api_key = create_api_key(openrouter_page)
            update_account_openrouter(email, api_key or '', "available")
            return True

        verified_page = None
        if result == 'need_link_verification':
            # 步骤3: 切回 Outlook 获取验证链接
            print("[Info] - 需要链接验证，切回 Outlook 收件箱...")
            outlook_page.bring_to_front()
            verification_link = get_verification_link(outlook_page)

            if not verification_link:
                print(f"[Error] - {email} 获取验证链接失败")
                mark_account_failed(email, "获取验证链接失败")
                return False

            # 步骤4: 在 OpenRouter 同一个页面中访问验证链接（保持 session）
            verified_page = click_verification_link(openrouter_page, verification_link)
            if not verified_page:
                print(f"[Error] - {email} 验证链接访问失败")
                mark_account_failed(email, "验证链接访问失败")
                return False

        elif result == 'need_code_verification':
            print("[Warning] - 需要验证码方式，当前使用链接验证，跳过")
            mark_account_failed(email, "需要验证码方式")
            return False

        # 步骤5: 登录 OpenRouter 后创建 API Key
        print("[Info] - 登录 OpenRouter 并创建 API Key...")
        key_page = verified_page or openrouter_page
        # 先尝试直接创建，如果未登录则先登录
        api_key = create_api_key(key_page)
        if api_key is None:
            # 尝试用邮箱密码登录 OpenRouter（带 Outlook 页面以支持 factor-two 验证码）
            print("[Info] - 尝试通过登录页面获取 session...")
            api_key = login_and_create_key(key_page, email, password, outlook_page=outlook_page)

        if not api_key:
            print(f"[Warning] - {email} 注册成功但未能创建 API Key")
            update_account_openrouter(email, '', "available")
            return True

        # 步骤6: 更新账号信息
        update_account_openrouter(email, api_key, "available")
        print(f"[Success] - {email} 全部流程完成，API Key: {api_key[:20]}...")
        return True

    except Exception as e:
        print(f"[Error] - 处理 {email} 时出错: {e}")
        mark_account_failed(email, f"处理异常: {str(e)[:50]}")
        return False

    finally:
        for ctx in [openrouter_ctx, outlook_ctx]:
            try:
                if ctx:
                    ctx.close()
            except:
                pass
        try:
            if pw:
                pw.stop()
        except:
            pass


def process_existing_account(account):
    """处理已注册 OpenRouter 但没有 API Key 的账号：登录 Outlook -> 登录 OpenRouter (含邮件验证码) -> 创建 API Key"""
    email = account['email']
    password = account['password']

    print(f"\n{'='*60}")
    print(f"[Start] - 为已注册账号创建 API Key: {email}")
    print(f"{'='*60}")

    pw = None
    outlook_ctx = None
    openrouter_ctx = None

    try:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()

        # 步骤1: 启动 Outlook 无痕窗口并登录
        print("[Info] - 启动 Outlook 无痕窗口...")
        pw, outlook_ctx = OpenBrowserPersistent(playwright_instance=pw)
        if outlook_ctx is None:
            print("[Error] - 无法启动 Outlook 浏览器")
            return False

        outlook_page = outlook_ctx.pages[0] if outlook_ctx.pages else outlook_ctx.new_page()
        outlook_page = login_outlook(outlook_page, email, password)
        if outlook_page is None:
            print(f"[Error] - {email} Outlook 登录失败")
            return False

        # 步骤2: 启动 OpenRouter 无痕窗口，登录并处理 factor-two 验证码
        print("[Info] - 启动 OpenRouter 无痕窗口...")
        pw, openrouter_ctx = OpenBrowserPersistent(playwright_instance=pw)
        if openrouter_ctx is None:
            print("[Error] - 无法启动 OpenRouter 浏览器")
            return False

        openrouter_page = openrouter_ctx.pages[0] if openrouter_ctx.pages else openrouter_ctx.new_page()

        # 步骤3: 登录 OpenRouter（含 factor-two 邮件验证码） + 创建 API Key
        api_key = login_and_create_key(openrouter_page, email, password, outlook_page=outlook_page)

        if api_key:
            update_account_openrouter(email, api_key, "available")
            print(f"[Success] - {email} API Key 创建成功: {api_key[:20]}...")
            return True
        else:
            print(f"[Warning] - {email} 未能创建 API Key")
            return False

    except Exception as e:
        print(f"[Error] - 处理 {email} 时出错: {e}")
        return False

    finally:
        for ctx in [openrouter_ctx, outlook_ctx]:
            try:
                if ctx:
                    ctx.close()
            except:
                pass
        try:
            if pw:
                pw.stop()
        except:
            pass


def main(max_tasks=0, mode='register'):
    """主函数
    mode='register': 注册新账号
    mode='create_key': 为已注册但没有 API Key 的账号创建 Key
    """
    accounts = load_accounts_from_json()
    if not accounts:
        print("[Error] - 没有找到任何账号")
        return

    if mode == 'create_key':
        # 筛选已注册 OpenRouter 但没有 API Key 的账号（必须有 openrouter_api_key 字段）
        pending = [a for a in accounts
                   if a.get('openrouter', False)
                   and 'openrouter_api_key' in a
                   and not a.get('openrouter_api_key')
                   and a.get('status') != 'unavailable']
        if not pending:
            print("[Info] - 没有需要创建 API Key 的账号")
            return
        process_func = process_existing_account
        print(f"[Info] - 模式: 为已注册账号创建 API Key")
    else:
        # 筛选 openrouter=false 且状态不是 unavailable 的账号，从末尾开始
        pending = [a for a in accounts if not a.get('openrouter', False) and a.get('status') != 'unavailable']
        pending.reverse()
        if not pending:
            print("[Info] - 所有账号都已注册 OpenRouter")
            return
        process_func = process_single_account
        print(f"[Info] - 模式: 注册新账号")

    if max_tasks > 0:
        pending = pending[:max_tasks]

    print(f"[Info] - 共 {len(pending)} 个账号待处理")

    succeeded = 0
    failed = 0

    for account in pending:
        result = process_func(account)
        if result:
            succeeded += 1
        else:
            failed += 1

        config = load_config()
        delay = config.get('registration_delay', 30)
        if len(pending) > 1 and account != pending[-1]:
            print(f"[Info] - 等待 {delay} 秒后处理下一个账号...")
            time.sleep(delay)

    print(f"\n[Result] - 共处理 {succeeded + failed} 个，成功 {succeeded}，失败 {failed}")
