import uiautomation as auto
import time
import cv2
import numpy as np
import pyautogui
import sys
import threading
import subprocess
import random
from datetime import datetime
import os

def add_wechat_contact(account, name):
    """
    微信添加单个好友工具（需提前登录微信）
    :param account: 微信号
    :param name: 好友备注
    """
    # 定位微信主窗口
    wechat_window = auto.WindowControl(
        searchDepth=1, ClassName="WeChatMainWndForPC", Name="微信"
    )
    # 激活微信窗口
    wechat_window.SetActive()
    if not wechat_window.Exists():
        raise RuntimeError("微信主窗口未找到，请确认微信已启动并登录")

    # 统一等待时间配置
    wait_sec = 1
    print(f"正在添加: {account}({name})")

    try:
        # 进入通讯录
        wechat_window.ButtonControl(Name="通讯录").Click()
        time.sleep(wait_sec)

        # 查看是否有取消按钮
        cancelBtn = wechat_window.ButtonControl(Name="取消")
        if cancelBtn.Exists():
            cancelBtn.Click()
            time.sleep(wait_sec)

        # 打开添加界面
        wechat_window.ButtonControl(Name="添加朋友").Click()
        time.sleep(wait_sec * 2)  # 此界面加载需要更多时间
        # 获取输入框控件
        search_box = wechat_window.EditControl(Name="微信号/手机号")
        # 获取焦点 无法获取焦点
        # search_box.SetFocus()
        # 换成点击
        search_box.Click()
        # 全选输入框
        search_box.SendKeys("{Ctrl}a")
        # 输入微信号
        search_box.SendKeys(account)
        time.sleep(wait_sec)

        # 点击搜索按钮
        search_btn = wechat_window.ListItemControl(
            NameRegex=f"搜索[:：]\\s*{account}", searchDepth=10, timeout=15
        )
        # 点击搜索按钮
        search_btn.Click()
        # time.sleep(wait_sec)
        # 无结果
        no_result = wechat_window.TextControl(Name="无法找到该用户，请检查你填写的账号是否正确。", timeout=1)
        # 账号异常
        accountErr = wechat_window.TextControl(Name="被搜账号状态异常，无法显示", timeout=1)
        # 操作频繁
        action_best_all = wechat_window.TextControl(Name="操作过于频繁，请稍后再试", timeout=1)
        # 快速检查结果，避免二次搜索
        try:
            no_result_exists = no_result.Exists(0, 0)  # 不等待，直接检查
            account_err_exists = accountErr.Exists(0, 0)  # 不等待，直接检查
            action_best_all = action_best_all.Exists(0, 0)  # 不等待，直接检查

        except:
            no_result_exists = False
            account_err_exists = False
            action_best_all = False
        print(f"no_result: {no_result_exists}")

        # 无结果是进入
        if no_result_exists:
            print(f"❌ 未找到用户: {account}")
            return False
        if account_err_exists:
            print(f"❌ 搜索的账号异常: {account}")
            return False
        # 操作频繁
        if action_best_all:
            print(f"❌ 微信风控搜索频繁，程序终止")
            return False
        # 定位添加通讯录按钮 - 优先用控件定位，备用图像识别
        try:
            # 尝试用控件定位ibitle
            add_btn = auto.PaneControl(Name="微信", ClassName="ContactProfileWnd")

            if add_btn.Exists():
                add_btn.ButtonControl(Name="添加到通讯录").Click()
                print("✅ 控价定位成功->点击通讯录按钮")
            else:
                # 备用方案：图像识别
                print("🔄 控件定位失败-启用备用视觉引擎-计算按钮位置中")
                click_image("./templates/add_friend_button.png")
        except:
            # 最后备用方案：图像识别
            print("🔄 空间定位失败-启用视觉引擎-计算图片位置后点击")
            click_image("./templates/add_friend_button.png")
        # 申请消息按钮
        time.sleep(wait_sec)
        verify_box = wechat_window.WindowControl(
            searchDepth=1, ClassName="WeUIDialog", Name="添加朋友请求"
        )
        # 取消按钮
        cancelBtn = verify_box.ButtonControl(Name="取消")
        # 确定按钮
        confirm_btn = verify_box.ButtonControl(Name="确定")
        # 问候语按钮
        messageBox = verify_box.EditControl()
        messageBox.Click()
        messageBox.SendKeys("{Ctrl}a")
        messageBox.SendKeys("请求消息")
        # tab键位定位下一行
        auto.SendKeys("{Tab}")
        # 全选
        auto.SendKeys("{Ctrl}a")
        auto.SendKeys("备注信息")
        cancelBtn.Click()

    except Exception as e:

        print(f"添加 {account} 失败: {str(e).split('。')[0]}")
        return False


# 点击任意窗体的确定按钮
def click_confirm_button(window, wait_sec=1):
    window.ButtonControl(Name="确定").Click()
    time.sleep(wait_sec)
    return True

# 点击任意取消按钮
def click_cancel_button(window, wait_sec=1):
    window.ButtonControl(Name="取消").Click()
    time.sleep(wait_sec)
    return True

# opencv点击按钮
def click_by_template(template_path, confidence=0.9):
    # 截屏并转换颜色空间
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # 加载模板
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"模板图片不存在: {template_path}")

    # 多尺度匹配
    res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    if max_val >= confidence:
        # 计算中心点坐标
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2

        # 模拟点击
        pyautogui.click(center_x, center_y)
        return True
    return False


# 模拟人类鼠标移动轨迹
def human_like_move_to(x, y):
    current_x, current_y = pyautogui.position()
    steps = random.choice([2, 3, 4])
    for i in range(1, steps + 1):
        ratio = i / steps
        intermediate_x = int(current_x * (1 - ratio) + x * ratio)
        intermediate_y = int(current_y * (1 - ratio) + y * ratio)
        jitter_x = random.randint(-3, 3)
        jitter_y = random.randint(-3, 3)
        pyautogui.moveTo(intermediate_x + jitter_x, intermediate_y + jitter_y)
        time.sleep(random.uniform(0.1, 0.3))


# 模拟人类点击动作
def human_like_click(x=None, y=None):
    current_x, current_y = pyautogui.position()
    target_x = x if x is not None else current_x
    target_y = y if y is not None else current_y
    human_like_move_to(target_x, target_y)
    time.sleep(random.uniform(0.2, 1))
    final_x = target_x + random.randint(-8, 8)
    final_y = target_y + random.randint(-8, 8)
    pyautogui.click(final_x, final_y)


# 根据pyauto点击 - 优化版本
def click_image(img_path, confidence=0.8, retries=2, delay=1):
    for i in range(retries):
        location = pyautogui.locateOnScreen(img_path, confidence=confidence)
        if location:
            center = pyautogui.center(location)
            human_like_click(center.x, center.y)
            return True
        time.sleep(delay)
    return False


# 使用示例
if __name__ == "__main__":
    # 异常账号 dididifggg
    # 正常账号 dididi
    # 无结果账号 dididifggg77
    # 添加单个好友示例
    add_wechat_contact("dididi", "技术好友")
