"""
follwRoom.py 更新示例
展示如何将硬编码的时间间隔替换为配置文件读取
"""

# 原始代码示例 (带硬编码)
def original_activate_wechat_window(wechat):
    """原始版本 - 使用硬编码时间"""
    time.sleep(1)  # 硬编码
    
    if wechat.WindowState == 2:
        print(f"🔄 [ACTIVATE] 检测到窗口最小化，正在恢复...")
        wechat.ShowWindow(1)
        time.sleep(1)  # 硬编码
        wechat.SetActive()
        time.sleep(1)  # 硬编码
    
    print(f"✅ [ACTIVATE] 微信主窗口激活成功")

# 更新后的代码示例 (使用配置)
from config_utils import get_interval

def updated_activate_wechat_window(wechat):
    """更新版本 - 使用配置文件"""
    time.sleep(get_interval('operation_wait'))  # 从配置读取
    
    if wechat.WindowState == 2:
        print(f"🔄 [ACTIVATE] 检测到窗口最小化，正在恢复...")
        wechat.ShowWindow(1)
        time.sleep(get_interval('window_switch_wait'))  # 从配置读取
        wechat.SetActive()
        time.sleep(get_interval('operation_wait'))  # 从配置读取
    
    print(f"✅ [ACTIVATE] 微信主窗口激活成功")

# 更多示例
def original_switch_room_and_send_content():
    """原始版本 - 硬编码示例"""
    time.sleep(3)  # 等待Chrome加载
    time.sleep(2)  # 等待页面加载
    time.sleep(1)  # 等待标签页切换完成

def updated_switch_room_and_send_content():
    """更新版本 - 使用配置"""
    time.sleep(get_interval('chrome_load_wait'))     # Chrome加载等待
    time.sleep(get_interval('page_load_wait'))       # 页面加载等待
    time.sleep(get_interval('tab_switch_wait'))      # 标签切换等待

# 建议的完整更新列表
HARDCODED_REPLACEMENTS = {
    # 原硬编码值 -> 配置项名称
    "time.sleep(1)": "time.sleep(get_interval('operation_wait'))",
    "time.sleep(2)": "time.sleep(get_interval('page_load_wait'))",
    "time.sleep(3)": "time.sleep(get_interval('chrome_load_wait'))",
    "time.sleep(0.5)": "time.sleep(get_interval('element_wait'))",
    "time.sleep(5)": "time.sleep(get_interval('network_timeout') // 6)",  # 5秒约为30秒超时的1/6
}

# 需要在文件开头添加的导入
REQUIRED_IMPORTS = """
from config_utils import (
    get_interval, 
    get_feature, 
    get_timeout,
    is_screenshot_enabled,
    is_notifications_enabled,
    is_detailed_logs_enabled
)
"""

print("📋 更新建议:")
print("1. 在 follwRoom.py 开头添加配置工具导入")
print("2. 将所有硬编码的 time.sleep() 替换为配置读取")
print("3. 将功能开关的硬编码替换为配置读取")
print("4. 测试更新后的功能是否正常")