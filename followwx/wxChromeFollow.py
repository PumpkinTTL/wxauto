import uiautomation as auto
import time
import pyautogui
import os
from datetime import datetime
from win10toast import ToastNotifier
from wxauto import WeChat

# 引入多线程
import threading


def getWechat():
    """获取微信主窗口控件，如果找不到则返回None"""
    wechat = auto.WindowControl(
        searchDepth=1, ClassName="WeChatMainWndForPC", Name="微信"
    )
    return wechat if wechat.Exists() else None


# wxauto获取特特定昵称的微信窗口
def wxautoGetWindowByNickName(nickname="又是一年冬"):
    wx = WeChat(nickname=nickname)
    return wx


# 获取微信chrome窗口根据下标
def getWxChromeWindowByIndex(index=0):
    className = f"Chrome_WidgetWin_{index}"
    wechat_chrome = auto.PaneControl(searchDepth=1, ClassName=className, Name="微信")
    return wechat_chrome if wechat_chrome.Exists(0,0) else None


# 检测头图像是否存在
def checkTargetImageExists(img_path):
    try:
        return pyautogui.locateOnScreen(img_path, confidence=0.8)
    except:
        print(f"❌ 图像识别失败: {img_path}")
        return False


# 根据图片点击
def clickByIMG(image_path="./templates/cv_liao.png", confidence=0.8):
    location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
    if location:
        pyautogui.click(location)
        return True
    else:
        print(f"❌ 未找到目标图像: {image_path}")
        raise Exception(f"图像识别失败: {image_path}")


# 发送内容
def sendContent(content):
    # 清空内容
    auto.SendKeys("{Ctrl}a{Del}")
    auto.SendKeys(content)


# 截图保存
def screenshot():
    # 创建screensfollow目录（如果不存在）
    screens_dir = "screensfollow"
    if not os.path.exists(screens_dir):
        os.makedirs(screens_dir)
        print(f"创建目录: {screens_dir}")

    # 生成时间格式的文件名
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"{timestamp} 直播发送弹幕.png"
    filepath = os.path.join(screens_dir, filename)

    # 截图并保存
    try:
        pyautogui.screenshot(filepath)
        print(f"截图已保存: {filepath}")
        return filepath
    except Exception as e:
        print(f"截图保存失败: {e}")
        return None


# 切换直播间
def switchRoom(chrome, roomName):
    chrome.TabItemControl(Name=roomName).Click()


# 判断是否已经打开直播间
def isRoomOpen(chrome, roomName):
    return chrome.TabItemControl(Name=roomName).Exists(0, 0)


# 系统通知
def showNotification(title, message, duration=5):
    """
    显示Windows系统通知
    :param title: 通知标题
    :param message: 通知内容
    :param duration: 显示时间（秒）
    """
    toaster = ToastNotifier()
    try:
        toaster.show_toast(
            title, message, duration=duration, threaded=True  # 非阻塞模式
        )
        print(f"通知已发送: {title} - {message}")
    except Exception as e:
        print(f"通知发送失败: {e}")


# 获取chrome微信的所有直播间
def getChromeViewRooms(chrome):
    chromeTab = chrome.TabControl(searchDepth=5)
    # 获取所有 TabItem
    tabItems = chromeTab.GetChildren()
    for i, item in enumerate(tabItems):
        if hasattr(item, "Name"):
            print(f"TabItem {i}: {item.Name}")
    return chromeTab


# 查看之直播间是否在播
def RommOff(chrome, roomName):
    switchRoom(chrome, roomName)
    time.sleep(1)
    return chrome.TextControl(Name="直播已结束").Exists(0, 0)


# 直播中按钮是否存在
def topisLiveText(wechatChrome):
    ctrl = wechatChrome.TextControl(Name="直播中")
    return ctrl if ctrl.Exists(2, 0.3) else False


# 点击顶部搜索
def topSearch():
    clickByIMG("./templates/cv_search.png")


def initEnterRoom(wechat, roomName):
    if getWxChromeWindowByIndex(0) is None:
        wechat.SetActive()
        wechat.ButtonControl(Name="视频号").Click()
        time.sleep(1)
    # 获取微信的webview
    wechatChrome = getWxChromeWindowByIndex(0)
    wechatChrome.SetActive()
    # 检测webview内是否存在了当前直播间的tabitem
    isOpen = isRoomOpen(wechatChrome, f"{roomName}的直播")
    if isOpen:
        print("✅ 直播间已经打开")
        switchRoom(wechatChrome, f"{roomName}的直播")
        # 检测是否已经结束直播
        if(liveEnd(wechatChrome)):
            print("❌ 检测到直播已结束，尝试刷新界面")
            refreshPage()
            # 再次检测
            if(liveEnd(wechatChrome)):
                print("❌ 重试仍然结束,关闭直播间")
                closeTabByTitle(wechatChrome, f"{roomName}的直播")
                return False
        clickByIMG("./templates/cv_liao.png")
        sendContent("看起来很好玩的样子")
        time.sleep(2)
        # clickByIMG("./templates/cv_send_btn.png")
        return True
    # 未打开启用头部搜索方式进入直播间
    topSearch()
    # 输入搜索内容
    sendContent(roomName)
    # 回车
    auto.SendKeys("{Enter}")
    # 休眠3秒
    time.sleep(3)
    # 查找搜索界面的正在直播文字是否存在
    isLiving = topisLiveText(wechatChrome)
    if not isLiving:
        print("❌ 直播间未找到，可能未在播")
        # 关闭标签
        closeTabByTitle(wechatChrome, f'{roomName} - 搜一搜')
        return False
    else:
        # 点击直播中文字
        isLiving.Click()
        # 休眠3秒
        time.sleep(3)
        # 切换到直播间
        switchRoom(wechatChrome, f"{roomName}的直播")
        if isRoomOpen(wechatChrome, f"{roomName}的直播"):
            print("✅ 直播间已经打开")
            closeTabByTitle(wechatChrome, f"{roomName} - 搜一搜")
            switchRoom(wechatChrome, f"{roomName}的直播")
            time.sleep(2)
            # 点击发送弹幕的按钮
            clickByIMG("./templates/cv_liao.png")
            time.sleep(2)
            # 输入内容
            sendContent("很想试试呀~")
            time.sleep(2)
            # 发送按钮
            # clickByIMG("./templates/cv_send_btn.png")
            return True
        else:
            print("❌未找到当前用户的直播")
            return False


# 点击弹幕发送按钮

def clickSendBtn():
    clickByIMG("./templates/cv_send_btn.png")

# 刷新界面
def refreshPage():
    auto.SendKeys("{CTRL}r")
    time.sleep(3)

# pyautogui检测图片是否存在
def checkImageExists(image_path):
    try:
        location = pyautogui.locateOnScreen(image_path, confidence=0.8)
        return location is not None
    except:
        raise Exception(f"图像识别失败: {image_path}")
        return False

# 查询是否已经直播间是否已经结束
def liveEnd(chrome):
    # 直播间已结束
    return chrome.TextControl(Name="直播已结束").Exists(0,0) is not None
    

# 点击搜索
def search():
    try:
        clickByIMG("./templates/cv_search_wrap.png")
        print("✅ 点击搜索成功")
    except:
        print("❌ 点击搜索失败，尝试其他方式...")
        try:
            clickByIMG("./templates/cv_search_wrap_active.png")
            print("✅ 点击聚焦后的搜索输入框成功")
        except:
            print("❌ 聚焦的搜索区域未找到，尝试清空重试...")
            try:
                clickByIMG("./templates/cv_clear_btn.png")
                print("✅ 点击清空按钮成功")
            except:
                print("❌ 备选方案点击搜索失败")


# 备选方案使用tab定位搜索
def clickSearchByTab():
    auto.SendKeys("{Tab}")
    auto.SendKeys("{CTRL}a{DEL}")


# 根据标签名称关闭
def closeTabByTitle(chrome, title):
    chrome.TabItemControl(Name=title).Click()
    auto.SendKeys("{CTRL}w")

# 跟播函数
def followLiveTask():
    with auto.UIAutomationInitializerInThread():  # ✅ 加这句初始化 COM
        initEnterRoom(getWechat(), roomName="星光漫游12")


if __name__ == "__main__":
    # 参半牙膏工厂店
    # 线上销售渠道4号
    initEnterRoom(getWechat(), roomName="线上销售渠道4号")
