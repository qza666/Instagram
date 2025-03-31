from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from random_data import generate_random_user_data, generate_gmail_alias
from selenium.webdriver.support.ui import Select
from gmail_verification import authenticate_gmail, fetch_verification_code
from selenium.common.exceptions import TimeoutException
from urllib.parse import quote
from datetime import datetime
import random
from config import CAPTCHA_PATH, PROXY_URL, GMAMI
from email_api import buy_email, latest


class BrowserAutomator():
    def __init__(self): 
        self.browser = None
        self.user_data = None
        self.orderId =  None
    
    def initialize_browser(self):
        """初始化浏览器并加载扩展（含无头模式和防检测）"""
        chrome_options = Options()
        chrome_options.add_argument("--disable-webgl")  # 彻底禁用WebGL

        # 加载扩展
        chrome_options.add_extension(CAPTCHA_PATH)

        # 配置代理
        if PROXY_URL:
            chrome_options.add_argument(f"--proxy-server={PROXY_URL}")
            #print(f"使用代理：{PROXY_URL}")

        # 无头模式配置
        #chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        
        # 防检测配置
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # 忽略SSL证书错误
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--accept-insecure-certs") 
        
        # 禁用自动化特征
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # 初始化驱动
        service = Service(ChromeDriverManager().install())
        self.browser = webdriver.Chrome(service=service, options=chrome_options)
        
        # 执行防检测脚本
        self.browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.navigator.chrome = {runtime: {}, app: {}};
            """
        })

        # # 等待扩展加载
        # extension_url = "chrome-extension://hlifkpholllijblknnmbfagnkjneagid/popup/popup.html"
        # self.browser.get(extension_url)
        # WebDriverWait(self.browser, 10).until(
        #     EC.presence_of_element_located((By.TAG_NAME, "body"))
        # )
        # print("✅ 浏览器扩展加载完成") 
        
        return self.browser

    def register_instagram_account(self):
        # 打开Instagram注册页面
        self.browser.get("https://www.instagram.com/")
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("✅ Instagram页面加载完成")

        # 执行注册操作
        self._click_register_button()

        # 购买邮箱
        self.orderId, email = buy_email()
        if not self.orderId:
            print("❌ 购买邮箱失败")
            return False, None
        self.user_data = generate_random_user_data(False, email)
        print("注册信息:", self.user_data)

        self._fill_registration_form()
        self._submit_form()
        return self._handle_birthday_selection()

    def _click_register_button(self):
        """点击注册按钮"""
        register_button = WebDriverWait(self.browser, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div:nth-child(2) > span > p > a"))
        )
        register_button.click()
        print("✅ 已点击注册按钮")

    def _fill_registration_form(self):
        """填写注册表单"""
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.NAME, "emailOrPhone"))
        )

        form_fields = {
            "emailOrPhone": self.user_data["email"],
            "password": self.user_data["password"],
            "fullName": self.user_data["fullName"],
            "username": self.user_data["username"]
        }

        for field, value in form_fields.items():
            self.browser.find_element(By.NAME, field).send_keys(value)
        print("✅ 注册表单填写完成")

    def _submit_form(self):
        """提交注册表单"""
        next_button = WebDriverWait(self.browser, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div:nth-child(10) > div > button"))
        )
        next_button.click()
        print("✅ 已提交注册表单")

    def _handle_birthday_selection(self):
        """处理生日选择界面"""
        # 等待生日选择元素加载
        WebDriverWait(self.browser, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select[title='年：']"))
        )
        print("✅ 进入生日选择界面")

        # 生成符合要求的随机生日
        birth_year, birth_month, birth_day = self._generate_random_birthday()
        print(f"生成的生日：{birth_year}-{birth_month:02d}-{birth_day:02d}")

        # 选择月份
        Select(self.browser.find_element(By.CSS_SELECTOR, "select[title='月：']")
              ).select_by_value(str(birth_month))
        
        # 选择日期
        Select(self.browser.find_element(By.CSS_SELECTOR, "select[title='日：']")
              ).select_by_value(str(birth_day))
        
        # 选择年份
        Select(self.browser.find_element(By.CSS_SELECTOR, "select[title='年：']")
              ).select_by_value(str(birth_year))

        print("✅ 已填写生日信息")
        email = self._click_next_after_birthday()
        if email:
            return True, self.user_data["username"], self.user_data["password"], email
        return False, None, None, None

    def _generate_random_birthday(self):
        """生成18-60岁之间的随机生日"""
        current_year = datetime.now().year
        birth_year = random.randint(current_year-60, current_year-18)
        birth_month = random.randint(1, 12)
        
        # 根据月份确定最大天数（简化处理闰年）
        month_days = {
            1:31, 2:28, 3:31, 4:30, 5:31, 6:30,
            7:31, 8:31, 9:30, 10:31, 11:30, 12:31
        }
        birth_day = random.randint(1, month_days[birth_month])
        
        return birth_year, birth_month, birth_day

    def _click_next_after_birthday(self):
        """点击生日选择后的下一步按钮并处理整个验证流程"""

        # 检查sessionid是否存在
        def wait_for_sessionid_cookie(browser, timeout=30):
            WebDriverWait(browser, timeout).until(
                lambda driver: driver.get_cookie("sessionid") is not None
            )

        try:
            # 第一次点击提交生日信息
            next_button = WebDriverWait(self.browser, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '下一步')]"))
            )
            next_button.click()
            print("✅ 已提交生日信息")

            # 处理reCAPTCHA验证
            next_after_recaptcha = WebDriverWait(self.browser, 120).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '下一步')]"))
            )
            next_after_recaptcha.click()
            print("✅ 已通过reCAPTCHA验证并点击下一步")

            # 等待验证码输入界面加载
            verification_input = WebDriverWait(self.browser, 60).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@aria-label, '验证码')]"))
            )
            print("✅ 进入验证码输入界面")

            # 获取验证码
            print(self.orderId)
            code = latest(self.orderId)
            print(f"✅ 获取到验证码: {code}")
            if code:
                # 输入验证码
                verification_input.send_keys(code)
                print(f"✅ 已输入验证码: {code}")

                # 提交验证码
                email_code = WebDriverWait(self.browser, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "form > * > div:nth-child(2) > div"))
                )
                email_code.click()
                print("✅ 已提交验证码")

                # 智能等待，等待页面加载完成
                try:
                    wait_for_sessionid_cookie(self.browser, timeout=60)
                    print("✅ 页面已加载完毕")

                    # 页面加载完成后获取参数并构建URL
                    account_id = str(int(time.time() * 1000000))
                    print(f"生成的时间戳: {account_id}")

                    # URL编码邮箱
                    encoded_email = quote(self.user_data['email'].lower())

                    # 构建新URL
                    new_url = (
                        f"https://accountscenter.instagram.com/personal_info/contact_points/"
                        f"?contact_point_type=email"
                        f"&contact_point_value={encoded_email}"
                        f"&dialog_type=contact_detail"
                    )
                    print(f"✅ 已构建新URL: {new_url}")

                    # 打开新URL
                    self.browser.get(new_url)
                    print(f"✅ 已打开新URL: {new_url}")

                    # 等待并点击“删除邮箱”按钮
                    delete_email_button = WebDriverWait(self.browser, 60).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[text()='删除邮箱']"))
                    )
                    delete_email_button.click()
                    print("✅ 已点击'删除邮箱'按钮")

                    # 等待并点击“删除”确认按钮
                    confirm_delete_button = WebDriverWait(self.browser, 30).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[text()='删除']"))
                    )
                    confirm_delete_button.click()
                    print("✅ 已点击'删除'确认按钮")

                    # 等待并点击“替换邮箱”按钮
                    replace_email_button = WebDriverWait(self.browser, 30).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[text()='替换邮箱']"))
                    )
                    replace_email_button.click()
                    print("✅ 已点击'替换邮箱'按钮")

                    # 等待新邮箱输入框加载
                    new_email_input = WebDriverWait(self.browser, 30).until(
                        EC.presence_of_element_located((By.XPATH, "//label[contains(text(),'输入邮箱')]/preceding-sibling::input"))
                    )
                    
                    # 生成新的Gmail别名邮箱（使用第二个域名）
                    new_email = generate_gmail_alias(True, GMAMI)
                    new_email_input.send_keys(new_email)
                    print(f"✅ 已输入新邮箱地址: {new_email}")

                    # 点击继续按钮（第一个匹配的继续按钮）
                    WebDriverWait(self.browser, 20).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "span.x1lliihq.x193iq5w.x6ikm8r.x10wlt62.xlyipyv.xuxw1ft"))
                    ).click()
                    print("✅ 已提交新邮箱地址")

                    # 等待验证码输入框加载
                    WebDriverWait(self.browser, 30).until(
                        EC.presence_of_element_located((By.XPATH, "//label[contains(text(),'输入验证码')]"))
                    )

                    # 获取新邮箱的验证码
                    service = authenticate_gmail()
                    print(new_email.lower())
                    verification_code = fetch_verification_code(
                        service, 
                        new_email,
                        retries=8,
                        delay=5
                    )

                    print(f"✅ 获取到验证码: {verification_code}")

                    if verification_code:
                        # 输入验证码
                        code_input = WebDriverWait(self.browser, 20).until(
                            EC.presence_of_element_located((
                                By.XPATH,
                                "//input[@autocomplete='one-time-code' and @inputmode='numeric']"
                            ))
                        )
                        code_input.send_keys(verification_code)
                        print(f"✅ 已输入新邮箱验证码: {verification_code}")

                        # 提交验证码（改进的继续按钮点击逻辑）
                        try:
                            continue_buttons = WebDriverWait(self.browser, 20).until(
                                EC.presence_of_all_elements_located(
                                    (By.CSS_SELECTOR, '[role="button"] .x1lliihq')
                                )
                            )
                            
                            target_button = continue_buttons[-1]
                            # 智能等待按钮可点击（处理可能的遮罩等情况）
                            WebDriverWait(self.browser, 10).until(
                                EC.element_to_be_clickable(target_button)
                            )
                            
                            try:
                                target_button.click()
                            except:
                                self.browser.execute_script("arguments[0].click();", target_button)
                                
                            print("✅ 已提交验证码")

                        except Exception as e:
                            raise Exception(f"无法点击继续按钮: {str(e)}")

                        # 最终检查点
                        WebDriverWait(self.browser, 30).until(
                            EC.url_contains("accountscenter")
                        )
                        time.sleep(5)
                        print("✅ 邮箱替换流程完成")
                        return new_email
                    else:
                        print("❌ 未能获取新邮箱验证码")

                except TimeoutException as e:
                    print(f"⚠️ 流程超时: {str(e)}")

        except Exception as e:
            print(f"发生错误: {e}")

    def close(self):
        """关闭浏览器"""
        if self.browser:
            self.browser.quit()
            print("✅ 浏览器已关闭")
