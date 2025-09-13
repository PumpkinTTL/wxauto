from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

# 设置用户数据目录
user_data_dir = os.path.join(os.getcwd(), 'chrome_profile_tmall')
os.makedirs(user_data_dir, exist_ok=True)

options = Options()
options.add_argument(f"--user-data-dir={user_data_dir}")
options.add_argument("--profile-directory=Default")
options.add_experimental_option('detach', True)

# 添加防检测参数
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options)

# 执行JavaScript隐藏webdriver特征
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': '''
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
    '''
})

driver.get("https://www.tmall.com/")