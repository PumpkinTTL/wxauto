import uiautomation as auto
import time
import os
import sqlite3
from datetime import datetime
from win10toast import ToastNotifier
import json
import os

# 🔥 可选导入pyautogui
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("⚠️ pyautogui模块不可用，图像识别功能将受限")

# 🔥 新增：导入跟播进度日志功能
try:
    from apis import add_follow_progress_log, update_follow_progress_status, sync_print
    PROGRESS_LOG_AVAILABLE = True
except ImportError:
    PROGRESS_LOG_AVAILABLE = False
    print("⚠️ 跟播进度日志功能不可用")
    # 如果导入失败，创建一个空的sync_print函数
    def sync_print(message, log_type="info", room_name=None, operation=None):
        print(f"[SYNC_PRINT_FALLBACK] {message}")
        # 尝试手动调用进度日志
        try:
            import sys
            sys.path.append('.')
            from apis import add_follow_progress_log
            add_follow_progress_log(message, log_type, None, operation, room_name)
        except:
            pass

def follow_print(message, log_type="info", progress=None, step=None, room_name=None):
    """
    跟播专用打印函数 - 同时输出到控制台和进度窗口

    Args:
        message: 日志消息
        log_type: 日志类型 (info, success, warning, error)
        progress: 进度百分比 (0-100)
        step: 当前步骤描述
        room_name: 直播间名称
    """
    # 打印到控制台
    print(message)

    # 如果进度日志功能可用，同时发送到进度窗口
    if PROGRESS_LOG_AVAILABLE:
        try:
            add_follow_progress_log(message, log_type, progress, step, room_name)
        except Exception as e:
            print(f"⚠️ 发送进度日志失败: {e}")


def activate_progress_window_by_title(window_title):
    """
    通过窗口标题激活跟播监听窗口 - 使用uiautomation

    Args:
        window_title: 窗口标题

    Returns:
        bool: 是否成功激活窗口
    """
    try:
        # 🔥 使用uiautomation查找并激活窗口，就像激活微信一样
        progress_window = auto.WindowControl(searchDepth=1, Name=window_title)

        if progress_window.Exists():
            print(f"✅ 找到监听窗口: {window_title}")

            # 激活窗口（就像激活微信窗口一样）
            progress_window.SetActive()

            # 🔥 如果窗口被最小化，需要额外处理
            if hasattr(progress_window, 'WindowState') and progress_window.WindowState == 2:  # 2表示最小化状态
                print(f"🔄 检测到监听窗口最小化，正在恢复...")
                progress_window.ShowWindow(1)  # 1表示正常显示
                time.sleep(0.5)
                progress_window.SetActive()

            print(f"✅ 监听窗口已激活: {window_title}")
            return True
        else:
            # 尝试模糊匹配
            print(f"🔍 精确匹配失败，尝试模糊匹配...")

            # 查找包含关键词的窗口
            if "跟播进度监控" in window_title:
                # 尝试查找任何包含"跟播进度监控"的窗口
                all_windows = auto.GetRootControl().GetChildren()
                for window in all_windows:
                    if hasattr(window, 'Name') and window.Name and "跟播进度监控" in window.Name:
                        print(f"✅ 找到匹配窗口: {window.Name}")
                        window.SetActive()
                        return True

            print(f"❌ 未找到监听窗口: {window_title}")
            return False

    except Exception as e:
        print(f"❌ 激活监听窗口失败: {str(e)}")
        return False

def update_follow_status(is_following=None, current_room=None, progress=None, step=None,
                        room_count=None, completed_count=None):
    """
    更新跟播状态
    """
    if PROGRESS_LOG_AVAILABLE:
        try:
            update_follow_progress_status(is_following, current_room, progress, step,
                                        room_count, completed_count)
        except Exception as e:
            print(f"⚠️ 更新跟播状态失败: {e}")

def follow_log_detailed(message, log_type="info", room_name=None, operation=None, progress=None):
    """
    详细的跟播日志记录函数，专门用于记录操作细节
    
    Args:
        message: 日志消息
        log_type: 日志类型 (info, success, warning, error)
        room_name: 直播间名称
        operation: 操作类型 (如：图片检测、弹幕发送、页面切换等)
        progress: 进度百分比
    """
    import datetime
    
    # 🔥 检查详细日志功能是否开启
    try:
        config = loadConfig()
        features = config.get("system_config", {}).get("features", {})
        detailed_logs_enabled = features.get("enable_detailed_logs", True)
        
        if not detailed_logs_enabled:
            # 如果详细日志关闭，只输出error和warning级别的日志
            if log_type not in ["error", "warning"]:
                return
    except Exception as e:
        print(f"⚠️ [DETAILED_LOG] 读取详细日志配置失败: {e}")
        # 配置读取失败时默认输出详细日志
    
    # 格式化消息，添加操作类型和时间戳
    if operation:
        formatted_message = f"[{operation}] {message}"
    else:
        formatted_message = message
        
    if room_name:
        formatted_message = f"【{room_name}】{formatted_message}"
    
    # 调用标准的follow_print
    follow_print(formatted_message, log_type, progress=progress, room_name=room_name)

# sync_print函数已从apis.py导入，不需要重复定义


def showToast(title, message, duration=3):
    """
    封装的Toast通知方法 - 支持多通知并发显示

    Args:
        title: 通知标题
        message: 通知内容
        duration: 显示时长（秒）
    """
    import threading
    import time
    import uuid
    
    # 先打印消息到控制台
    print(f"🔔 [TOAST] {title}: {message}")
    
    # 🔥 检查通知功能是否开启
    try:
        config = loadConfig()
        features = config.get("system_config", {}).get("features", {})
        notifications_enabled = features.get("enable_notifications", True)
        
        if not notifications_enabled:
            print(f"🔕 [TOAST] 通知功能已关闭，跳过显示")
            return
    except Exception as e:
        print(f"⚠️ [TOAST] 读取通知配置失败: {e}")
        # 配置读取失败时默认显示通知

    def _show_concurrent_toast():
        """在独立线程中显示通知，支持多个通知并发"""
        try:
            from win10toast import ToastNotifier
            
            # 🔥 为每个通知创建独立的ToastNotifier实例
            # 使用唯一ID避免实例冲突，支持真正的并发显示
            toaster = ToastNotifier()
            
            # 在独立线程中显示通知
            toaster.show_toast(
                title=title,
                msg=message,
                duration=duration,
                threaded=False  # 在我们自己的线程中，不需要再次threaded
            )
            
            print(f"✅ [TOAST] win10toast 并发通知显示完成")
            return True
            
        except ImportError:
            print(f"⚠️ [TOAST] win10toast 库未安装，使用备用方案")
        except Exception as e:
            print(f"⚠️ [TOAST] win10toast 显示失败: {str(e)}，使用备用方案")
            
            # 🔥 备用方案：PowerShell通知（每个通知独立进程，支持并发）
            try:
                import subprocess
                
                # 创建独立的PowerShell进程，每个通知一个进程，实现真正并发
                ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
$notification = New-Object System.Windows.Forms.NotifyIcon
$notification.Icon = [System.Drawing.SystemIcons]::Information
$notification.BalloonTipTitle = "{title}"
$notification.BalloonTipText = "{message}"
$notification.Visible = $true
$notification.ShowBalloonTip({duration * 1000})

# 等待通知显示完成后清理资源
Start-Sleep -Seconds {duration + 1}
$notification.Dispose()
"""
                
                # 🔥 每个通知独立的PowerShell进程，实现并发
                subprocess.Popen(
                    ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                print(f"✅ [TOAST] PowerShell 并发通知启动成功")
                return True
                
            except Exception as ps_e:
                print(f"❌ [TOAST] PowerShell通知也失败: {ps_e}")
                return False
    
    # 🔥 关键：在独立线程中显示通知，实现真正的并发
    # 每次调用showToast都会创建新线程，多个通知可以同时显示
    toast_thread = threading.Thread(
        target=_show_concurrent_toast,
        daemon=True,  # 守护线程，不阻塞主程序退出
        name=f"ConcurrentToast-{uuid.uuid4().hex[:8]}"  # 唯一线程名
    )
    
    toast_thread.start()
    
    # 🔥 立即返回，不等待通知完成，支持快速连续调用
    print(f"✅ [TOAST] 并发通知线程已启动")
    return True


from wxauto import WeChat

# 引入多线程
import threading


def loadConfig():
    """
    读取配置文件 - 新的统一配置格式

    Returns:
        dict: 配置信息
    """
    try:
        import json
        config_path = "config.json"
        if not os.path.exists(config_path):
            print(f"⚠️ [CONFIG] 配置文件不存在: {config_path}")
            # 返回默认配置
            default_config = {
                "system_config": {
                    "intervals": {
                        "bullet_screen_send": 500,
                        "bullet_screen_retry": 10,
                        "follow_task_retry": 60,
                        "image_recognition_retry": 60,
                        "live_room_check": 300
                    },
                    "retry_config": {
                        "max_bullet_retry": 3,
                        "max_image_retry": 5,
                        "max_follow_retry": 10,
                        "enable_auto_retry": True
                    },
                                            "features": {
                            "enable_screenshot": True,
                            "enable_notifications": True,
                            "enable_detailed_logs": True,
                            "enable_auto_scroll": True,
                            "enable_error_recovery": True,
                            "enable_performance_monitoring": False,
                            "enable_real_danmu_send": False
                        },
                    "quality": {
                        "screenshot_quality": 80,
                        "image_match_confidence": 0.8,
                        "log_level": "info"
                    }
                },
                "ui_config": {
                    "theme": "default",
                    "auto_scroll": True,
                    "show_notifications": True,
                    "animation_enabled": True
                }
            }
            # 创建默认配置文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            return default_config

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        print(f"✅ [CONFIG] 配置文件加载成功")
        
        # 显示系统配置摘要
        if 'system_config' in config:
            sys_config = config['system_config']
            # 兼容新的配置结构
            intervals = sys_config.get('intervals', {})
            features = sys_config.get('features', {})
            
            bullet_interval = intervals.get('bullet_screen_send', sys_config.get('bullet_screen_interval', 500))
            screenshot = features.get('enable_screenshot', sys_config.get('is_screenshot', True))
            detailed_logs = features.get('enable_detailed_logs', True)
            
            print(f"📊 [CONFIG] 弹幕间隔: {bullet_interval}秒")
            print(f"📸 [CONFIG] 截图功能: {screenshot}")
            print(f"📝 [CONFIG] 详细日志: {detailed_logs}")
        
        return config

    except Exception as e:
        print(f"❌ [CONFIG] 读取配置文件失败: {str(e)}")
        # 返回默认配置
        return {
            "system_config": {
                "intervals": {
                    "bullet_screen_send": 500,
                    "bullet_screen_retry": 10,
                    "follow_task_retry": 60,
                    "image_recognition_retry": 60,
                    "live_room_check": 300
                },
                "retry_config": {
                    "max_bullet_retry": 3,
                    "max_image_retry": 5,
                    "max_follow_retry": 10,
                    "enable_auto_retry": True
                },
                                        "features": {
                            "enable_screenshot": True,
                            "enable_notifications": True,
                            "enable_detailed_logs": True,
                            "enable_auto_scroll": True,
                            "enable_error_recovery": True,
                            "enable_performance_monitoring": False,
                            "enable_real_danmu_send": False
                        },
                "quality": {
                    "screenshot_quality": 80,
                    "image_match_confidence": 0.8,
                    "log_level": "info"
                }
            },
            "ui_config": {
                "theme": "default",
                "auto_scroll": True,
                "show_notifications": True,
                "animation_enabled": True
            }
        }


def getBulletScreenInterval():
    """
    获取弹幕发送间隔时间（秒）

    Returns:
        int: 间隔时间（秒）
    """
    try:
        config = loadConfig()
        system_config = config.get("system_config", {})
        
        # 新结构优先，兼容旧结构
        intervals = system_config.get("intervals", {})
        
        interval = intervals.get("bullet_screen_send", system_config.get("bullet_screen_interval", 500))

        print(f"⏰ [CONFIG] 弹幕间隔: {interval}秒")

        return interval

    except Exception as e:
        print(f"❌ [CONFIG] 获取弹幕间隔失败: {str(e)}")
        return 500


# getCurrentEnvMode函数已删除，不再需要环境模式区分


def getImageRecognitionRetryInterval():
    """
    获取图像识别重试间隔时间（秒）

    Returns:
        int: 间隔时间（秒）
    """
    try:
        config = loadConfig()
        system_config = config.get("system_config", {})

        intervals = system_config.get("intervals", {})
        interval = intervals.get("image_recognition_retry", 60)

        print(f"⏰ [CONFIG] 图像识别重试间隔: {interval}秒")

        return interval

    except Exception as e:
        print(f"❌ [CONFIG] 获取图像识别重试间隔失败: {str(e)}")
        return 60


def isRealDanmuSendEnabled():
    """
    是否启用真实发送弹幕（OCR点击发送按钮）

    Returns:
        bool: True=使用OCR点击发送按钮，False=使用回车键（测试模式）
    """
    try:
        config = loadConfig()
        system_config = config.get("system_config", {})
        features = system_config.get("features", {})

        enabled = features.get("enable_real_danmu_send", False)

        print(f"📤 [CONFIG] 真实发送弹幕: {'✅ 启用(OCR点击)' if enabled else '❌ 禁用(回车键测试)'}")

        return enabled

    except Exception as e:
        print(f"❌ [CONFIG] 获取真实发送弹幕配置失败: {str(e)}")
        return False  # 默认使用测试模式


def sendDanmuByConfig(room_name=""):
    """
    根据配置发送弹幕

    Args:
        room_name: 直播间名称（用于日志）

    Returns:
        bool: 发送是否成功
    """
    try:
        real_send_enabled = isRealDanmuSendEnabled()

        if real_send_enabled:
            # 真实发送模式：使用OCR点击发送按钮
            sync_print(f"📤 [真实发送] 使用OCR点击发送按钮...", "info", room_name, "弹幕发送")
            try:
                clickByIMG("./templates/cv_send_btn.png")
                sync_print(f"✅ [真实发送] OCR点击发送按钮成功", "success", room_name, "弹幕发送")
                return True
            except Exception as ocr_e:
                sync_print(f"❌ [真实发送] OCR点击发送按钮失败: {str(ocr_e)}", "error", room_name, "弹幕发送")
                return False
        else:
            # 测试模式：使用回车键
            sync_print(f"📤 [测试模式] 使用回车键发送...", "info", room_name, "弹幕发送")
            auto.SendKeys("{Enter}")
            sync_print(f"✅ [测试模式] 回车键发送成功", "success", room_name, "弹幕发送")
            return True

    except Exception as e:
        sync_print(f"❌ 弹幕发送失败: {str(e)}", "error", room_name, "弹幕发送")
        return False


def getRetryConfig():
    """
    获取重试配置

    Returns:
        dict: 包含重试配置的字典
    """
    try:
        config = loadConfig()
        system_config = config.get("system_config", {})
        retry_config = system_config.get("retry_config", {})
        
        return {
            "max_bullet_retry": retry_config.get("max_bullet_retry", 3),
            "max_image_retry": retry_config.get("max_image_retry", 5),
            "max_follow_retry": retry_config.get("max_follow_retry", 10),
            "enable_auto_retry": retry_config.get("enable_auto_retry", True)
        }
    except Exception as e:
        print(f"❌ [CONFIG] 获取重试配置失败: {str(e)}")
        return {
            "max_bullet_retry": 3,
            "max_image_retry": 5,
            "max_follow_retry": 10,
            "enable_auto_retry": True
        }


def getIntervalConfig():
    """
    获取时间间隔配置

    Returns:
        dict: 包含时间间隔配置的字典
    """
    try:
        config = loadConfig()
        system_config = config.get("system_config", {})
        intervals = system_config.get("intervals", {})
        
        return {
            "bullet_screen_send": intervals.get("bullet_screen_send", 500),
            "bullet_screen_retry": intervals.get("bullet_screen_retry", 10),
            "follow_task_retry": intervals.get("follow_task_retry", 60),
            "image_recognition_retry": intervals.get("image_recognition_retry", 20),
            "live_room_check": intervals.get("live_room_check", 300)
        }
    except Exception as e:
        print(f"❌ [CONFIG] 获取时间间隔配置失败: {str(e)}")
        return {
            "bullet_screen_send": 500,
            "bullet_screen_retry": 10,
            "follow_task_retry": 60,
            "image_recognition_retry": 60,
            "live_room_check": 300
        }


def isScreenshotEnabled():
    """
    检查截图功能是否开启

    Returns:
        bool: 是否开启截图功能
    """
    try:
        config = loadConfig()
        system_config = config.get("system_config", {})
        
        # 新结构优先，兼容旧结构
        features = system_config.get("features", {})
        is_enabled = features.get("enable_screenshot", system_config.get("is_screenshot", True))
        
        print(f"📸 [CONFIG] 截图功能: {'开启' if is_enabled else '关闭'}")
        return is_enabled

    except Exception as e:
        print(f"❌ [CONFIG] 获取截图配置失败: {str(e)}")
        return False


def forceActivateWechatWindow():
    """
    强制激活微信窗口 - 处理最小化状态

    Returns:
        tuple: (wechat_window, chrome_window) 或 (None, None)
    """
    try:
        print(f"🔥 [ACTIVATE] 开始强制激活微信窗口...")

        # 1. 获取微信主窗口
        wechat = getWechat()
        if not wechat:
            print(f"❌ [ACTIVATE] 微信主窗口未找到")
            return None, None

        # 2. 强制激活微信主窗口（处理最小化）
        try:
            print(f"🖥️ [ACTIVATE] 激活微信主窗口...")
            wechat.SetActive()
            time.sleep(1)

            # 🔥 如果窗口被最小化，需要额外处理
            if wechat.WindowState == 2:  # 2表示最小化状态
                print(f"🔄 [ACTIVATE] 检测到窗口最小化，正在恢复...")
                wechat.ShowWindow(1)  # 1表示正常显示
                time.sleep(1)
                wechat.SetActive()
                time.sleep(1)

            print(f"✅ [ACTIVATE] 微信主窗口激活成功")
        except Exception as main_e:
            print(f"⚠️ [ACTIVATE] 微信主窗口激活失败: {str(main_e)}")

        # 3. 获取并激活Chrome窗口
        chrome_window = getWxChromeWindowByIndex(0)
        if not chrome_window:
            print(f"❌ [ACTIVATE] 微信Chrome窗口未找到")
            return wechat, None

        try:
            print(f"🖥️ [ACTIVATE] 激活微信Chrome窗口...")
            chrome_window.SetActive()
            time.sleep(1)
            print(f"✅ [ACTIVATE] 微信Chrome窗口激活成功")
        except Exception as chrome_e:
            print(f"⚠️ [ACTIVATE] 微信Chrome窗口激活失败: {str(chrome_e)}")

        print(f"🎉 [ACTIVATE] 窗口激活流程完成")
        return wechat, chrome_window

    except Exception as e:
        print(f"❌ [ACTIVATE] 强制激活微信窗口失败: {str(e)}")
        return None, None


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
    return wechat_chrome if wechat_chrome.Exists(0, 0) else None


# 检测图像是否存在 这里很重要需要检测目标触发任务行为
def checkTargetImageExists(img_path):
    try:
        if not PYAUTOGUI_AVAILABLE:
            print(f"⚠️ pyautogui不可用，跳过图像识别: {img_path}")
            return False
        return pyautogui.locateOnScreen(img_path, confidence=0.8)
    except:
        print(f"❌ 图像识别失败: {img_path}")
        return False


# 根据图片点击
def clickByIMG(image_path="./templates/cv_liao.png", confidence=0.8):
    if not PYAUTOGUI_AVAILABLE:
        print(f"⚠️ pyautogui不可用，跳过图像点击: {image_path}")
        return False

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


# 清空输入框内容
def clearInputContent():
    """清空输入框内容"""
    auto.SendKeys("{Ctrl}a{Del}")
    print("📝 输入框内容已清空")


# 输入内容但不清空现有内容
def inputContentOnly(content):
    """只输入内容，不清空现有内容"""
    auto.SendKeys(content)


# 测试所有绑定话术（不发送）
def testAllSpeeches(room_id, interval_seconds=7):
    """
    测试所有绑定的话术，但不实际发送

    Args:
        room_id: 直播间ID
        interval_seconds: 每条话术间隔时间（秒）

    Returns:
        bool: 测试是否成功完成
    """
    try:
        print(f"🧪 开始测试直播间 {room_id} 的所有绑定话术")
        print(f"⏰ 间隔时间: {interval_seconds} 秒")
        print(f"⚠️ 注意: 只测试输入，不会实际发送")

        # 获取直播间的话术
        import sqlite3

        conn = sqlite3.connect("system.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT s.content, s.id
            FROM room_speeches rs
            JOIN speech s ON rs.speech_id = s.id
            WHERE rs.room_id = ? AND rs.status = 1 AND s.status = 1
            ORDER BY rs.create_time ASC
        """

        cursor.execute(query, (room_id,))
        speeches = cursor.fetchall()
        conn.close()

        if not speeches:
            print(f"⚠️ 直播间 {room_id} 没有绑定的话术")
            return False

        print(f"💬 找到 {len(speeches)} 条话术，开始测试...")

        for i, speech in enumerate(speeches):
            content = speech["content"]

            print(
                f"\n📝 [{i+1}/{len(speeches)}] 测试话术: {content[:50]}{'...' if len(content) > 50 else ''}"
            )

            # 先清空输入框
            clearInputContent()
            time.sleep(0.5)

            # 输入话术内容
            inputContentOnly(content)
            print(f"✅ 话术已输入到输入框")

            # 等待一秒让用户看到内容
            time.sleep(1)

            # 清空输入框（模拟发送后的清空）
            clearInputContent()

            # 等待间隔时间（除了最后一条）
            if i < len(speeches) - 1:
                print(f"⏰ 等待 {interval_seconds} 秒后继续下一条...")
                for remaining in range(interval_seconds, 0, -1):
                    print(f"  借剩 {remaining} 秒", end="\r")
                    time.sleep(1)
                print()  # 换行

        print(f"\n🎉 所有话术测试完成！")
        print(f"📋 总计测试了 {len(speeches)} 条话术")
        print(f"ℹ️ 注意: 所有话术都只是输入测试，没有实际发送")

        return True

    except Exception as e:
        print(f"❌ 测试话术失败: {str(e)}")
        return False


# 查询并打印直播间数据
def query_and_print_room_data(room_id, room_name):
    """
    查询并打印直播间绑定的商品、图片和话术信息

    Args:
        room_id: 直播间ID
        room_name: 直播间名称
    """
    try:
        print(f"\n🔍 [DEBUG] 正在装配直播间 '{room_name}' (ID: {room_id}) 的数据...")
        print(
            f"[DEBUG] 函数参数检查: room_id={room_id} (类型: {type(room_id)}), room_name='{room_name}'"
        )

        # 参数验证
        if not room_id or not room_name:
            print(f"❌ [ERROR] 参数无效: room_id={room_id}, room_name='{room_name}'")
            return None

        # 导入数据查询模块
        import sys
        import os

        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.append(current_dir)

        print(f"[DEBUG] 开始导入 room_data_query 模块...")
        from room_data_query import get_room_complete_data, print_room_data_summary

        print(f"[DEBUG] 模块导入成功")

        # 查询完整数据
        print(f"[DEBUG] 调用 get_room_complete_data({room_id})...")
        room_data = get_room_complete_data(room_id)
        print(f"[DEBUG] 数据查询完成: {type(room_data)}")

        if room_data:
            print(
                f"[DEBUG] 数据内容: has_data={room_data.get('has_data')}, product={bool(room_data.get('product'))}, images={len(room_data.get('images', []))}, speeches={len(room_data.get('speeches', []))}"
            )

        # 🔥 新增：读取并显示配置信息
        follow_print(f"📋 读取系统配置信息...", "info", step="配置读取", room_name=room_name)
        
        try:
            import json
            with open("config.json", 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            system_config = config.get("system_config", {})
            intervals = system_config.get("intervals", {})
            
            # 显示关键配置信息
            bullet_interval = intervals.get("bullet_screen_send", 500)
            image_interval = intervals.get("image_recognition_retry", 60)
            follow_interval = intervals.get("follow_task_retry", 60)
            
            follow_print(f"⚙️ 配置信息读取成功:", "success", step="配置读取", room_name=room_name)
            follow_print(f"   📨 弹幕发送间隔: {bullet_interval}秒", "info", step="配置详情", room_name=room_name)
            follow_print(f"   🖼️ 图像识别间隔: {image_interval}秒", "info", step="配置详情", room_name=room_name)
            follow_print(f"   🔄 跟播重试间隔: {follow_interval}秒", "info", step="配置详情", room_name=room_name)
            
        except Exception as config_error:
            follow_print(f"⚠️ 读取配置文件失败: {str(config_error)}", "warning", step="配置读取", room_name=room_name)

        # 打印格式化汇总
        print(f"[DEBUG] 开始打印数据汇总...")
        print_room_data_summary(room_data)
        print(f"[DEBUG] 数据汇总打印完成")

        # 根据数据完整性给出提示
        if room_data and room_data.get("has_data"):
            print(f"\n✅ 直播间 '{room_name}' 数据装配完成，准备开始操作弹幕")
        else:
            print(f"\n⚠️ 直播间 '{room_name}' 没有绑定数据，建议在后台配置商品和话术")

        print(f"[DEBUG] 函数执行完成，返回数据")
        return room_data

    except Exception as e:
        print(f"❌ [ERROR] 查询直播间数据失败: {str(e)}")
        import traceback

        print(f"[DEBUG] 错误堆栈: {traceback.format_exc()}")
        return None


# 改进的跟播初始化函数（支持测试模式）
def initEnterRoomWithTest(
    wechat, roomName, room_id=None, test_mode=False, interval_seconds=7
):
    """
    改进的直播间初始化函数，支持测试模式

    Args:
        wechat: 微信窗口对象
        roomName: 直播间名称
        room_id: 直播间ID（用于获取话术）
        test_mode: 是否为测试模式（不实际发送）
        interval_seconds: 话术间隔时间

    Returns:
        bool: 是否成功
    """
    try:
        # 执行原有的进入直播间逻辑
        success = initEnterRoom(wechat, roomName, room_id)

        if success and test_mode and room_id:
            print(f"\n🧪 进入测试模式，开始测试话术...")
            # 执行话术测试
            testAllSpeeches(room_id, interval_seconds)

        return success

    except Exception as e:
        print(f"❌ 改进的跟播初始化失败: {str(e)}")
        return False


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


def screenshotAfterDanmu(room_name, content, chrome_window=None):
    """
    弹幕发送后截图保存 - 优化版

    Args:
        room_name: 直播间名称
        content: 发送的弹幕内容（用于文件名）
        chrome_window: 微信Chrome窗口对象（可选，用于窗口截图）

    Returns:
        str: 截图文件路径，失败返回None
    """
    try:
        # 🔥 首先检查截图功能是否开启
        if not isScreenshotEnabled():
            print(f"📸 [SCREENSHOT] 当前截图功能未开启，不进行截图")
            print(f"💡 [SCREENSHOT] 可在配置文件中启用截图功能")
            sync_print(f"📸 当前截图功能未开启，跳过截图", "warning", room_name, "截图功能")
            sync_print(f"💡 可在配置文件中启用截图功能", "info", room_name, "截图功能")
            return None
        else:
            print(f"📸 [SCREENSHOT] 截图功能已开启，准备进行截图")
            sync_print(f"📸 截图功能已开启，准备进行截图", "info", room_name, "截图功能")

        # 创建screensfollow目录（如果不存在）
        screens_dir = "screensfollow"
        if not os.path.exists(screens_dir):
            os.makedirs(screens_dir)
            print(f"📁 创建截图目录: {screens_dir}")

        # 生成动态文件名：时间-直播间名称-发送弹幕.png
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 清理直播间名称，移除"的直播"后缀
        clean_room_name = room_name.replace("的直播", "")

        # 确保文件名安全（移除特殊字符）
        import re

        safe_room_name = re.sub(r'[<>:"/\\|?*]', "", clean_room_name)

        filename = f"{timestamp}-{safe_room_name}-发送弹幕.png"
        filepath = os.path.join(screens_dir, filename)

        print(f"📸 正在截图...")

        # 🔥 优化：优先使用窗口截图，否则使用全屏截图
        screenshot_success = False
        screenshot_method = ""

        # 方法1: 尝试窗口截图（如果提供了chrome_window）
        if chrome_window:
            try:
                print(f"🖥️ 尝试微信Chrome窗口截图...")

                # 确保窗口激活
                chrome_window.SetActive()
                time.sleep(0.5)

                # 获取窗口位置和大小
                rect = chrome_window.BoundingRectangle
                left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom

                print(f"📊 窗口位置: ({left}, {top}) -> ({right}, {bottom})")

                # 截取窗口区域
                window_screenshot = pyautogui.screenshot(
                    region=(left, top, right - left, bottom - top)
                )
                window_screenshot.save(filepath)

                screenshot_success = True
                screenshot_method = "窗口截图"
                print(f"✅ 微信Chrome窗口截图成功")

            except Exception as window_e:
                print(f"⚠️ 窗口截图失败: {str(window_e)}")
                print(f"🔄 尝试全屏截图...")

        # 方法2: 全屏截图（备用方案）
        if not screenshot_success:
            try:
                print(f"🖥️ 执行全屏截图...")
                pyautogui.screenshot(filepath)
                screenshot_success = True
                screenshot_method = "全屏截图"
                print(f"✅ 全屏截图成功")

            except Exception as full_e:
                print(f"❌ 全屏截图也失败: {str(full_e)}")
                return None

        if screenshot_success:
            print(f"✅ [SCREENSHOT] 截图保存成功: {filename} ({screenshot_method})")
            print(f"📁 [SCREENSHOT] 文件路径: {filepath}")
            print(f"🎯 [SCREENSHOT] 截图方式: {screenshot_method}")
            print(f"📊 [SCREENSHOT] 文件大小: {os.path.getsize(filepath) / 1024:.1f}KB")
            
            # 🔥 同步输出到监听窗口
            sync_print(f"✅ 截图保存成功: {filename}", "success", room_name, "截图完成")
            sync_print(f"🎯 截图方式: {screenshot_method}", "info", room_name, "截图完成")
            sync_print(f"📊 文件大小: {os.path.getsize(filepath) / 1024:.1f}KB", "info", room_name, "截图完成")

            # 🔥 显示截图成功提示
            showToast(
                "📸 截图成功！",
                f"直播间: {clean_room_name}\n弹幕: {content[:20]}{'...' if len(content) > 20 else ''}\n方式: {screenshot_method}",
            )

            return filepath
        else:
            print(f"❌ [SCREENSHOT] 截图失败，未能保存文件")
            sync_print(f"❌ 截图失败，未能保存文件", "error", room_name, "截图失败")
            return None

    except Exception as e:
        print(f"❌ 弹幕发送后截图失败: {str(e)}")
        showToast("❌ 截图失败", f"无法保存截图\n错误: {str(e)[:30]}...")
        return None


# 切换直播间
def switchRoom(chrome, roomName):
    chrome.TabItemControl(Name=roomName).Click()


# 判断是否已经打开直播间
def isRoomOpenByTabName(chrome, roomName):
    return chrome.TabItemControl(Name=roomName).Exists(0, 0)


# 系统通知
def showNotification(title, message, duration=5):
    """
    显示Windows系统通知
    :param title: 通知标题
    :param message: 通知内容
    :param duration: 显示时间（秒）
    """
    # 🔥 检查通知功能是否开启
    try:
        config = loadConfig()
        features = config.get("system_config", {}).get("features", {})
        notifications_enabled = features.get("enable_notifications", True)
        
        if not notifications_enabled:
            print(f"🔕 [NOTIFICATION] 通知功能已关闭: {title} - {message}")
            return
    except Exception as e:
        print(f"⚠️ [NOTIFICATION] 读取通知配置失败: {e}")
        # 配置读取失败时默认显示通知
    
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


# 直播中按钮是否存在 - 改进版本
def topisLiveText(wechatChrome, room_name=""):
    """
    检测搜索页面是否显示"直播中"状态

    Args:
        wechatChrome: 微信Chrome窗口对象
        room_name: 直播间名称（用于日志输出）

    Returns:
        控件对象或False
    """
    try:
        # 🔥 改进：更准确的直播状态检测，输出到监听窗口
        sync_print("🔍 正在检测直播状态...", "info", room_name, "直播检测")

        # 首先检查是否存在"直播中"文字
        live_ctrl = wechatChrome.TextControl(Name="直播中")
        if live_ctrl.Exists(maxSearchSeconds=3, searchIntervalSeconds=0.5):
            sync_print("🔴 找到'直播中'文字", "info", room_name, "直播检测")

            # 🔥 重要：检查控件是否真的可用（BoundingRectangle不为空）
            try:
                bounding_rect = live_ctrl.BoundingRectangle
                if bounding_rect.width() == 0 or bounding_rect.height() == 0:
                    sync_print("⚠️ '直播中'控件无效（BoundingRectangle为空），当前未在直播", "warning", room_name, "直播检测")
                    return False
                else:
                    sync_print(f"✅ '直播中'控件有效，边界: {bounding_rect}", "info", room_name, "直播检测")
            except Exception as rect_e:
                sync_print(f"⚠️ 无法获取'直播中'控件边界: {str(rect_e)}", "warning", room_name, "直播检测")
                return False

            # 🔥 新增：额外检查是否存在"直播已结束"文字
            end_ctrl = wechatChrome.TextControl(Name="直播已结束")
            if end_ctrl.Exists(maxSearchSeconds=1, searchIntervalSeconds=0.3):
                sync_print("📺 检测到'直播已结束'，直播间未在播", "error", room_name, "直播检测")
                return False

            # 🔥 新增：检查是否存在"暂未开播"文字
            not_started_ctrl = wechatChrome.TextControl(Name="暂未开播")
            if not_started_ctrl.Exists(maxSearchSeconds=1, searchIntervalSeconds=0.3):
                sync_print("⏸️ 检测到'暂未开播'，直播间未在播", "error", room_name, "直播检测")
                return False

            sync_print("✅ 确认直播正在进行中", "success", room_name, "直播检测")
            return live_ctrl
        else:
            # 🔥 新增：如果没找到"直播中"，尝试查找其他状态文字来确认
            sync_print("❌ 未找到'直播中'文字，检查其他状态...", "warning", room_name, "直播检测")

            # 检查是否有"直播已结束"
            end_ctrl = wechatChrome.TextControl(Name="直播已结束")
            if end_ctrl.Exists(maxSearchSeconds=1, searchIntervalSeconds=0.3):
                sync_print("📺 确认检测到'直播已结束'", "error", room_name, "直播检测")
                return False

            # 检查是否有"暂未开播"
            not_started_ctrl = wechatChrome.TextControl(Name="暂未开播")
            if not_started_ctrl.Exists(maxSearchSeconds=1, searchIntervalSeconds=0.3):
                sync_print("⏸️ 确认检测到'暂未开播'", "error", room_name, "直播检测")
                return False

            # 检查是否有"回放"
            replay_ctrl = wechatChrome.TextControl(Name="回放")
            if replay_ctrl.Exists(maxSearchSeconds=1, searchIntervalSeconds=0.3):
                sync_print("📼 确认检测到'回放'，非实时直播", "error", room_name, "直播检测")
                return False

            sync_print("❌ 未找到任何直播状态标识，直播间可能未在播", "error", room_name, "直播检测")
            return False

    except Exception as e:
        sync_print(f"❌ 检测直播状态异常: {str(e)}", "error", room_name, "直播检测")
        return False


# 点击顶部搜索
def topSearch():
    clickByIMG("./templates/cv_search.png")


def initEnterRoom(wechat, roomName, room_id=70):
    # 🔥 新增：输出当前配置信息到监听窗口
    try:
        # 读取配置信息
        bullet_interval = getBulletScreenInterval()
        image_interval = getImageRecognitionRetryInterval()
        screenshot_enabled = isScreenshotEnabled()
        real_danmu_enabled = isRealDanmuSendEnabled()

        # 从配置文件读取功能开关
        config = loadConfig()
        system_config = config.get("system_config", {})
        features = system_config.get("features", {})

        image_enabled = features.get("enable_image_recognition", True)
        bullet_enabled = features.get("enable_bullet_screen", True)

        # 输出配置信息到监听窗口
        sync_print("📋 当前跟播配置信息:", "info", roomName, "配置信息")
        sync_print(f"🖼️ 图像识别重试间隔: {image_interval}秒", "info", roomName, "配置信息")
        sync_print(f"💬 弹幕发送间隔: {bullet_interval}秒", "info", roomName, "配置信息")
        sync_print(f"🔍 图像识别功能: {'✅ 已开启' if image_enabled else '❌ 已关闭'}", "info", roomName, "配置信息")
        sync_print(f"📢 弹幕发送功能: {'✅ 已开启' if bullet_enabled else '❌ 已关闭'}", "info", roomName, "配置信息")
        sync_print(f"📸 截图功能: {'✅ 已开启' if screenshot_enabled else '❌ 已关闭'}", "info", roomName, "配置信息")

    except Exception as config_e:
        sync_print(f"⚠️ 读取配置信息失败: {str(config_e)}", "warning", roomName, "配置信息")

    # 🔥 新增：激活跟播监听窗口，确保用户能看到跟播进度
    try:
        sync_print("🪟 正在激活跟播监听窗口...", "info", roomName, "窗口管理")

        # 导入必要的模块
        from apis import PROGRESS_WINDOW_MANAGER

        # 检查是否有该直播间的监听窗口
        if roomName in PROGRESS_WINDOW_MANAGER["active_windows"]:
            window_info = PROGRESS_WINDOW_MANAGER["active_windows"][roomName]
            window_title = window_info.get("title", f"跟播进度监控 - {roomName}")

            try:
                # 使用Windows API激活窗口
                activate_result = activate_progress_window_by_title(window_title)

                if activate_result:
                    sync_print("✅ 跟播监听窗口已激活，请查看屏幕右上角", "success", roomName, "窗口管理")
                    sync_print("💡 监听窗口位置：屏幕右上角，可拖拽调整位置", "info", roomName, "窗口管理")

                    # 🔥 短暂延迟后再激活微信窗口，确保用户能看到监听窗口
                    time.sleep(1)
                    sync_print("🔄 监听窗口激活完成，现在激活微信窗口继续跟播", "info", roomName, "窗口管理")
                else:
                    sync_print("⚠️ 无法激活监听窗口，请手动查看右上角", "warning", roomName, "窗口管理")

            except Exception as activate_e:
                sync_print(f"⚠️ 激活监听窗口失败: {str(activate_e)}", "warning", roomName, "窗口管理")
        else:
            sync_print("💡 未找到该直播间的监听窗口，可能需要手动创建", "info", roomName, "窗口管理")

    except Exception as window_e:
        sync_print(f"⚠️ 激活监听窗口过程中出现异常: {str(window_e)}", "warning", roomName, "窗口管理")

    # 🔥 更新跟播状态
    update_follow_status(current_room=roomName, step="正在进入直播间")

    # 检测微信chrome是否已经被打开
    if getWxChromeWindowByIndex(0) is None:
        follow_print(f"🔧 正在打开微信视频号...", "info", room_name=roomName)
        wechat.SetActive()
        wechat.ButtonControl(Name="视频号").Click()
        time.sleep(1)
    # 获取微信的webview
    wechatChrome = getWxChromeWindowByIndex(0)
    wechatChrome.SetActive()
    # 检测webview内是否存在了当前直播间的tabitem
    isOpen = isRoomOpenByTabName(wechatChrome, f"{roomName}的直播")
    if isOpen:
        follow_print("✅ 直播间已经打开", "success", room_name=roomName)
        # 激活当前标签直播间
        switchRoom(wechatChrome, f"{roomName}的直播")
        # 检测是否已经结束直播
        if liveEnd(wechatChrome, roomName):
            sync_print("❌ 检测到直播已结束，尝试刷新界面", "warning", roomName, "直播检测")
            refreshPage()
            # 再次检测
            if liveEnd(wechatChrome, roomName):
                sync_print("❌ 重试仍然结束,关闭直播间", "error", roomName, "直播检测")
                sync_print("🔄 正在关闭直播间标签...", "warning", roomName, "标签管理")
                try:
                    closeTabByTitle(wechatChrome, f"{roomName}的直播")
                    sync_print("✅ 直播间标签已关闭", "success", roomName, "标签管理")
                except Exception as close_e:
                    sync_print(f"⚠️ 关闭直播间标签失败: {str(close_e)}", "warning", roomName, "标签管理")
                return False
        clickChatBtn()
        sendContent("定位弹幕发送成功~测试弹幕不发送~")
        time.sleep(2)
        # clickByIMG("./templates/cv_send_btn.png")

        # 🔥 重要：确保切换到当前直播间标签页，为图像识别做准备
        try:
            follow_print(f"🔄 确保切换到直播间标签页: {roomName}的直播", "info", room_name=roomName)
            switchRoom(wechatChrome, f"{roomName}的直播")
            time.sleep(1)  # 等待标签页切换完成
            follow_print(f"✅ 已切换到目标直播间标签页", "success", room_name=roomName)
        except Exception as switch_error:
            follow_print(f"⚠️ 切换直播间标签页失败: {str(switch_error)}", "warning", room_name=roomName)

        # 🔥 新增：直播间正确打开后，查询并打印绑定的商品、图片和话术信息
        if room_id:
            follow_print(f"📊 正在查询直播间数据...", "info", step="查询直播间配置", room_name=roomName)
            query_and_print_room_data(room_id, roomName)
            # 🎯 新增：创建图像识别任务（从配置文件读取间隔）
            follow_print(f"📅 创建图像识别定时任务...", "info", step="创建识别任务", room_name=roomName)
            task_created = createImageRecognitionTask(
                room_id=room_id,
                room_name=roomName,
                # 间隔时间和测试模式从配置文件自动读取
            )

            if task_created:
                # 🔥 修复：显示正确的图像识别间隔，而不是弹幕间隔
                interval = getImageRecognitionRetryInterval()
                follow_print(
                    f"✅ 图像识别任务创建成功，将每{interval}秒尝试一次图像匹配",
                    "success", step="任务创建完成", room_name=roomName
                )
            else:
                follow_print(f"⚠️ 图像识别任务创建失败", "warning", room_name=roomName)

        return True
    # 未打开启用头部搜索方式进入直播间
    follow_print(f"🔍 开始搜索直播间: {roomName}", "info", step="搜索直播间", room_name=roomName)
    topSearch()
    # 输入搜索内容
    sendContent(roomName)
    # 回车
    auto.SendKeys("{Enter}")
    # 休眠3秒
    time.sleep(3)
    # 查找搜索界面的正在直播文字是否存在
    isLiving = topisLiveText(wechatChrome, roomName)
    if not isLiving:
        # 🔥 重要：当前未在直播，创建重试任务并提示用户
        sync_print("❌ 当前未在直播", "error", roomName, "直播检测")
        sync_print("📺 检测到直播间未在播或控件无效", "warning", roomName, "直播检测")

        # 🔥 创建重试跟播任务
        try:
            # 获取房间ID（如果有的话）
            room_id = roomName  # 简化处理，使用房间名作为ID

            # 创建下次识别任务
            next_task_info = createNextRecognitionTask(room_id, roomName)

            if next_task_info:
                # 🔥 关键：在监听窗口显示重试时间信息
                next_time_display = next_task_info['next_time'].split(' ')[1]  # 只显示时间部分
                sync_print("🔄 已创建重试跟播任务", "warning", roomName, "重试安排")
                sync_print(f"⏰ 将在 {next_time_display} 重试进行跟播", "info", roomName, "重试安排")
                sync_print(f"⏱️ 重试间隔: {next_task_info['interval']}秒", "info", roomName, "重试配置")
                sync_print("💡 请确保网络通畅和微信处于运行状态", "info", roomName, "重试提示")

                # 计算并显示倒计时
                try:
                    from datetime import datetime
                    next_datetime = datetime.strptime(next_task_info['next_time'], '%Y-%m-%d %H:%M:%S')
                    now = datetime.now()
                    time_diff = next_datetime - now
                    if time_diff.total_seconds() > 0:
                        minutes = int(time_diff.total_seconds() // 60)
                        seconds = int(time_diff.total_seconds() % 60)
                        sync_print(f"⏳ 距离下次重试: {minutes}分{seconds}秒", "info", roomName, "倒计时")
                except:
                    pass
            else:
                sync_print("❌ 重试跟播任务创建失败", "error", roomName, "重试失败")
                sync_print("💡 请手动重新启动跟播", "warning", roomName, "重试失败")

        except Exception as retry_e:
            sync_print(f"❌ 创建重试任务异常: {str(retry_e)}", "error", roomName, "重试异常")

        # 关闭搜索标签
        sync_print("🔄 正在关闭搜索标签...", "warning", roomName, "标签管理")
        try:
            closeTabByTitle(wechatChrome, f"{roomName} - 搜一搜")
            sync_print("✅ 搜索标签已关闭", "success", roomName, "标签管理")
        except Exception as close_e:
            sync_print(f"⚠️ 关闭搜索标签失败: {str(close_e)}", "warning", roomName, "标签管理")

        return False
    else:
        follow_print("✅ 找到正在直播的房间", "success", room_name=roomName)

        # 点击直播中文字
        try:
            sync_print("🖱️ 正在点击'直播中'控件...", "info", roomName, "直播检测")
            isLiving.Click()
            sync_print("✅ 成功点击'直播中'控件", "success", roomName, "直播检测")
        except Exception as click_e:
            sync_print(f"❌ 点击'直播中'控件失败: {str(click_e)}", "error", roomName, "直播检测")

            # 🔥 点击失败时也创建重试任务
            try:
                room_id = roomName
                next_task_info = createNextRecognitionTask(room_id, roomName)

                if next_task_info:
                    next_time_display = next_task_info['next_time'].split(' ')[1]
                    sync_print("🔄 点击失败，已创建重试跟播任务", "warning", roomName, "重试安排")
                    sync_print(f"⏰ 将在 {next_time_display} 重试进行跟播", "info", roomName, "重试安排")
                    sync_print("💡 请确保网络通畅和微信处于运行状态", "info", roomName, "重试提示")
                else:
                    sync_print("❌ 重试跟播任务创建失败", "error", roomName, "重试失败")
            except Exception as retry_e:
                sync_print(f"❌ 创建重试任务异常: {str(retry_e)}", "error", roomName, "重试异常")

            return False
        # 休眠3秒
        time.sleep(3)
        # 切换到直播间
        switchRoom(wechatChrome, f"{roomName}的直播")
        if isRoomOpenByTabName(wechatChrome, f"{roomName}的直播"):
            follow_print("✅ 直播间已经打开", "success", room_name=roomName)
            closeTabByTitle(wechatChrome, f"{roomName} - 搜一搜")
            switchRoom(wechatChrome, f"{roomName}的直播")
            time.sleep(2)
            # 点击发送弹幕的按钮
            follow_print("🎯 正在定位弹幕输入框...", "info", step="定位弹幕输入框", room_name=roomName)
            clickChatBtn()
            time.sleep(2)
            # 输入内容
            sendContent("测试定位弹幕输入框成功~测试弹幕不发送~")
            time.sleep(2)
            # 发送按钮
            # clickByIMG("./templates/cv_send_btn.png")

            # 🔥 重要：确保切换到当前直播间标签页，为图像识别做准备
            try:
                follow_print(f"🔄 确保切换到直播间标签页: {roomName}的直播", "info", room_name=roomName)
                switchRoom(wechatChrome, f"{roomName}的直播")
                time.sleep(1)  # 等待标签页切换完成
                follow_print(f"✅ 已切换到目标直播间标签页", "success", room_name=roomName)
            except Exception as switch_error:
                follow_print(f"⚠️ 切换直播间标签页失败: {str(switch_error)}", "warning", room_name=roomName)

            # 🔥 新增：直播间正确打开后，查询并打印绑定的商品、图片和话术信息
            if room_id:
                follow_print(f"📊 正在查询直播间数据...", "info", step="查询直播间配置", room_name=roomName)
                query_and_print_room_data(room_id, roomName)

                # 🎯 新增：创建图像识别任务（从配置文件读取间隔）
                follow_print(f"📅 创建图像识别定时任务...", "info", step="创建识别任务", room_name=roomName)
                task_created = createImageRecognitionTask(
                    room_id=room_id,
                    room_name=roomName,
                    # 间隔时间和测试模式从配置文件自动读取
                )

                if task_created:
                    # 🔥 修复：显示正确的图像识别间隔，而不是弹幕间隔
                    interval = getImageRecognitionRetryInterval()
                    follow_print(
                        f"✅ 图像识别任务创建成功，将每{interval}秒尝试一次图像匹配",
                        "success", step="任务创建完成", room_name=roomName
                    )
                else:
                    follow_print(f"⚠️ 图像识别任务创建失败", "warning", room_name=roomName)

            return True
        else:
            follow_print("❌未找到当前用户的直播", "error", room_name=roomName)
            return False


# 点击弹幕发送按钮


def clickSendBtn():
    clickByIMG("./templates/cv_send_btn.png")


# 点击聊一聊


def clickChatBtn():
    clickByIMG("./templates/cv_liao.png")


# 刷新界面
def refreshPage():
    auto.SendKeys("{CTRL}r")
    time.sleep(3)


# 选择直播间并且发送弹幕
def createDanmuTaskAfterImageMatch(room_id, room_name, matched_image_path, chrome_view):
    """
    图像匹配成功后创建弹幕任务

    Args:
        room_id: 直播间ID
        room_name: 直播间名称
        matched_image_path: 匹配成功的图片路径
        chrome_view: 微信Chrome窗口对象

    Returns:
        bool: 是否成功创建任务
    """
    try:
        follow_print(f"🎉 图像匹配成功！开始创建弹幕任务", "success", step="图像匹配成功", room_name=room_name)
        follow_print(f"🖼️ 匹配图片: {matched_image_path}", "info", room_name=room_name)
        follow_print(f"📺 直播间: {room_name} (ID: {room_id})", "info", room_name=room_name)

        # 🔥 新增：输出当前弹幕配置到监听窗口
        try:
            bullet_interval = getBulletScreenInterval()

            # 从配置文件读取功能开关
            config = loadConfig()
            system_config = config.get("system_config", {})
            features = system_config.get("features", {})
            bullet_enabled = features.get("enable_bullet_screen", True)

            sync_print(f"💬 弹幕发送间隔: {bullet_interval}秒", "info", room_name, "任务配置")
            sync_print(f"💬 弹幕发送功能: {'✅ 已开启' if bullet_enabled else '❌ 已关闭'}", "info", room_name, "任务配置")

        except Exception as config_e:
            sync_print(f"⚠️ 读取弹幕配置失败: {str(config_e)}", "warning", room_name, "任务配置")

        # 🔥 直接清理现有弹幕任务，重新创建
        follow_print(f"🧹 清理现有弹幕任务，准备重新创建...", "info", step="清理旧任务", room_name=room_name)
        cleared_count = clearAllDanmuTasks(room_id)
        if cleared_count > 0:
            follow_print(f"✅ 已清理 {cleared_count} 个现有弹幕任务", "success", room_name=room_name)
            showToast(
                "🧹 任务清理完成",
                f"直播间: {room_name}\n已清理{cleared_count}个旧任务\n准备创建新任务",
            )
        else:
            follow_print(f"💡 没有现有弹幕任务需要清理", "info", room_name=room_name)

        # 获取直播间的话术
        follow_print(f"📝 正在获取直播间话术...", "info", step="获取话术配置", room_name=room_name)
        speeches = getRoomSpeeches(room_id)
        if not speeches:
            follow_print(f"⚠️ 直播间 {room_name} 没有绑定话术，无法创建弹幕任务", "warning", room_name=room_name)
            showToast("⚠️ 话术未配置", f"直播间: {room_name}\n请先配置弹幕话术")
            return False

        follow_print(f"💬 获取到 {len(speeches)} 条话术", "success", room_name=room_name)

        # 🔥 从配置文件读取弹幕间隔
        interval_seconds = getBulletScreenInterval()
        # 环境模式已移除，不再需要区分
        interval_minutes = interval_seconds / 60

        follow_print(f"⏰ 弹幕发送间隔: {interval_seconds}秒", "info", room_name=room_name)

        # # 🔥 图像识别成功提示 - 已注释
        # showToast(
        #     "🎉 图像识别成功！",
        #     f"直播间: {room_name}\n识别图片: {os.path.basename(matched_image_path)}\n开始创建弹幕任务",
        # )

        # 🔥 为每条话术创建独立的弹幕任务
        follow_print(f"🔧 正在为 {len(speeches)} 条话术创建弹幕任务...", "info", step="创建弹幕任务", room_name=room_name)
        created_tasks = createDanmuTasksForAllSpeeches(
            room_id, room_name, matched_image_path, speeches, interval_seconds
        )

        if not created_tasks:
            follow_print(f"❌ 弹幕任务创建失败", "error", room_name=room_name)
            # showToast("❌ 弹幕任务创建失败", f"直播间: {room_name}\n数据库记录失败")
            return False

        follow_print(f"✅ 成功创建 {len(created_tasks)} 个弹幕任务", "success", step="任务创建完成", room_name=room_name)

        # 🔥 将任务注册到TaskManager
        try:
            from task_manager import get_task_manager

            task_manager = get_task_manager()

            if task_manager:
                # 🔥 确保TaskManager已启动
                if not task_manager.is_running:
                    sync_print(f"🚀 TaskManager未运行，正在启动...", "info", room_name, "任务管理器")
                    task_manager.start()
                    sync_print(f"✅ TaskManager已启动: {task_manager.is_running}", "success", room_name, "任务管理器")

                if task_manager.is_running:
                    registered_count = 0
                    for task_id in created_tasks:
                        # 从数据库读取执行时间
                        import sqlite3

                        conn = sqlite3.connect("system.db")
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT run_time FROM tasks WHERE task_id = ?", (task_id,)
                        )
                        result = cursor.fetchone()
                        conn.close()

                        if result:
                            from datetime import datetime

                            run_time = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
                            if task_manager.register_danmu_task(task_id, run_time):
                                registered_count += 1

                    sync_print(
                        f"✅ 成功注册 {registered_count}/{len(created_tasks)} 个弹幕任务到调度器",
                        "success", room_name, "任务注册"
                    )

                    # 验证调度器中的任务
                    if hasattr(task_manager, "scheduler") and task_manager.scheduler:
                        jobs = task_manager.scheduler.get_jobs()
                        danmu_jobs = [
                            job for job in jobs if job.id.startswith("danmu_task_")
                        ]
                        sync_print(f"📊 调度器中的弹幕任务: {len(danmu_jobs)} 个", "info", room_name, "任务统计")

                    # showToast(
                    #     "🎉 弹幕任务创建成功",
                    #     f"直播间: {room_name}\n创建{len(created_tasks)}个任务\n每{interval_seconds}秒自动发送",
                    # )
                else:
                    sync_print(f"❌ TaskManager启动失败", "error", room_name, "任务管理器")
                    # showToast(
                    #     "❌ TaskManager启动失败", f"弹幕任务已创建\n但无法自动执行"
                    # )
            else:
                sync_print(f"❌ 无法获取TaskManager实例", "error", room_name, "任务管理器")
                # showToast(
                #     "❌ TaskManager获取失败", f"弹幕任务已创建\n但无法注册到调度器"
                # )

        except Exception as e:
            sync_print(f"⚠️ 注册任务到调度器失败: {str(e)}", "warning", room_name, "任务注册")
            # showToast("⚠️ 注册失败", f"弹幕任务已创建\n但调度器注册失败")

        return True

    except Exception as e:
        sync_print(f"❌ 创建弹幕任务失败: {str(e)}", "error", room_name, "任务创建")
        # showToast("❌ 弹幕任务异常", f"直播间: {room_name}\n错误: {str(e)[:50]}")
        return False


def clearAllDanmuTasks(room_id):
    """
    清理指定直播间的所有弹幕任务

    Args:
        room_id: 直播间ID

    Returns:
        int: 清理的任务数量
    """
    try:
        import sqlite3

        conn = sqlite3.connect("system.db")
        cursor = conn.cursor()

        # 查询要删除的任务
        cursor.execute(
            """
            SELECT task_id FROM tasks 
            WHERE room_id = ? AND task_type = 'danmu_task'
        """,
            (room_id,),
        )

        tasks_to_delete = cursor.fetchall()
        task_count = len(tasks_to_delete)

        if task_count > 0:
            print(f"🧹 正在清理直播间 {room_id} 的所有弹幕任务...")

            # 删除所有弹幕任务
            cursor.execute(
                """
                DELETE FROM tasks 
                WHERE room_id = ? AND task_type = 'danmu_task'
            """,
                (room_id,),
            )

            conn.commit()
            print(f"✅ 已清理 {task_count} 个弹幕任务")

            # 显示清理的任务
            for i, (task_id,) in enumerate(tasks_to_delete[:5], 1):
                print(f"   {i}. 🗑️ {task_id}")
            if task_count > 5:
                print(f"   ... 等共 {task_count} 个任务")
        else:
            print(f"💡 直播间 {room_id} 没有弹幕任务需要清理")

        conn.close()
        return task_count

    except Exception as e:
        print(f"❌ 清理弹幕任务失败: {str(e)}")
        return 0


def checkExistingDanmuTask(room_id, force_recreate=False):
    """
    检查是否已存在有效的弹幕任务，清理过期任务

    Args:
        room_id: 直播间ID
        force_recreate: 是否强制重新创建（清理所有现有任务）

    Returns:
        bool: 是否存在有效任务（未来时间的任务）
    """
    try:
        # 🔥 如果强制重新创建，直接清理所有任务
        if force_recreate:
            print(f"🔄 强制重新创建模式，清理所有现有弹幕任务...")
            cleared_count = clearAllDanmuTasks(room_id)
            if cleared_count > 0:
                print(f"✅ 强制清理完成，可以重新创建弹幕任务")
            return False  # 返回False表示可以创建新任务

        import sqlite3
        from datetime import datetime

        conn = sqlite3.connect("system.db")
        cursor = conn.cursor()

        # 查询该直播间所有弹幕任务（status=0为可执行）
        cursor.execute(
            """
            SELECT task_id, status, create_time, run_time
            FROM tasks 
            WHERE room_id = ? AND task_type = 'danmu_task' AND status = 0
            ORDER BY run_time ASC
        """,
            (room_id,),
        )

        results = cursor.fetchall()

        if not results:
            conn.close()
            print(f"✅ 无弹幕任务，可以创建")
            return False

        current_time = datetime.now()
        valid_tasks = []
        expired_tasks = []

        print(f"🔍 检查 {len(results)} 个弹幕任务的执行时间...")

        # 检查每个任务的执行时间
        for task_id, status, create_time, run_time in results:
            try:
                # 解析执行时间
                task_run_time = datetime.strptime(run_time, "%Y-%m-%d %H:%M:%S")

                if task_run_time > current_time:
                    # 未来时间，有效任务
                    valid_tasks.append((task_id, task_run_time))
                    print(
                        f"   ✅ 有效任务: {task_id} -> {task_run_time.strftime('%H:%M:%S')}"
                    )
                else:
                    # 过期任务
                    expired_tasks.append(task_id)
                    print(
                        f"   ❌ 过期任务: {task_id} -> {task_run_time.strftime('%H:%M:%S')} (已过期)"
                    )

            except Exception as parse_e:
                print(f"⚠️ 解析任务时间失败: {task_id} - {str(parse_e)}")
                expired_tasks.append(task_id)

        # 🔥 清理过期任务
        if expired_tasks:
            print(f"🧹 发现 {len(expired_tasks)} 个过期弹幕任务，正在清理...")

            for task_id in expired_tasks:
                cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
                print(f"   🗑️ 已删除过期任务: {task_id}")

            conn.commit()
            print(f"✅ 过期任务清理完成")

        conn.close()

        # 检查是否还有有效任务
        if valid_tasks:
            print(f"📋 发现 {len(valid_tasks)} 个有效弹幕任务（未来时间）:")
            for task_id, run_time in valid_tasks[:3]:  # 只显示前3个
                print(f"   • {task_id}: {run_time.strftime('%H:%M:%S')}")
            if len(valid_tasks) > 3:
                print(f"   • ... 等共 {len(valid_tasks)} 个任务")

            # 🔥 计算最晚的任务时间，给用户提示
            latest_task = max(valid_tasks, key=lambda x: x[1])
            latest_time = latest_task[1]
            print(f"💡 最后一个弹幕任务将在 {latest_time.strftime('%H:%M:%S')} 执行")

            return True
        else:
            print(f"✅ 无有效弹幕任务（未来时间），可以创建")
            return False

    except Exception as e:
        print(f"❌ 检查弹幕任务失败: {str(e)}")
        return False


def createDanmuTasksForAllSpeeches(
    room_id, room_name, matched_image_path, speeches, interval_seconds
):
    """
    为每条话术创建独立的弹幕任务

    Args:
        room_id: 直播间ID
        room_name: 直播间名称
        matched_image_path: 匹配的图片路径
        speeches: 话术列表
        interval_seconds: 发送间隔（秒）

    Returns:
        list: 创建成功的任务ID列表
    """
    try:
        import sqlite3
        from datetime import datetime, timedelta

        print(f"📝 为 {len(speeches)} 条话术创建独立的弹幕任务...")
        
        # 🔥 增强：输出更详细的弹幕任务创建信息
        print(f"📊 [DANMU_TASK] ===== 弹幕任务批量创建详情 =====")
        print(f"🏠 [DANMU_TASK] 直播间: {room_name} (ID: {room_id})")
        print(f"🖼️ [DANMU_TASK] 触发图片: {os.path.basename(matched_image_path)}")
        print(f"📝 [DANMU_TASK] 话术数量: {len(speeches)}条")
        print(f"⏱️ [DANMU_TASK] 发送间隔: {interval_seconds}秒")
        print(f"🕐 [DANMU_TASK] 当前时间: {datetime.now().strftime('%H:%M:%S')}")
        
        # 🔥 新增：向监听窗口输出弹幕任务创建开始信息
        sync_print(f"📝 开始创建弹幕任务", "info", room_name, "弹幕任务")
        sync_print(f"   📊 待创建任务数量: {len(speeches)}条", "info", room_name, "任务统计")
        sync_print(f"   🖼️ 触发图片: {os.path.basename(matched_image_path)}", "info", room_name, "触发条件")
        sync_print(f"   ⏱️ 弹幕发送间隔: {interval_seconds}秒", "info", room_name, "发送间隔")

        created_tasks = []
        current_time = datetime.now()
        
        # 🔥 新增：显示当前时间和配置信息
        sync_print(f"🕐 当前时间: {current_time.strftime('%H:%M:%S')}", "info", room_name, "时间信息")

        conn = sqlite3.connect("system.db")
        cursor = conn.cursor()

        # 确保tasks表存在
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                task_type TEXT NOT NULL,
                room_id INTEGER,
                run_time TEXT NOT NULL,
                create_time TEXT NOT NULL,
                status INTEGER DEFAULT 1,
                remark TEXT
            )
        """
        )

        for i, speech in enumerate(speeches):
            # 🔥 修复：计算每个任务的执行时间，第一个任务也要有延迟
            # 从配置文件读取首次弹幕发送延迟
            config = loadConfig()
            system_config = config.get("system_config", {})
            intervals = system_config.get("intervals", {})
            first_delay = intervals.get("bullet_screen_send", 500)  # 使用弹幕间隔作为首次延迟
            
            # 第一个任务延迟first_delay秒，后续任务按间隔递增
            run_time = current_time + timedelta(seconds=first_delay + (i * interval_seconds))

            # 生成任务ID
            timestamp = int(run_time.timestamp())
            task_id = f"danmu_task_{room_id}_{timestamp}_{i+1}"

            # 构建任务备注
            # 环境模式已移除，不再需要区分
            remark = f"弹幕发送任务 {i+1}/{len(speeches)}\n"
            remark += f"直播间: {room_name} (ID: {room_id})\n"
            remark += f"匹配图片: {os.path.basename(matched_image_path)}\n"
            remark += f"话术内容: {speech['content'][:50]}{'...' if len(speech['content']) > 50 else ''}\n"
            remark += f"执行时间: {run_time.strftime('%H:%M:%S')}\n"
            remark += f"间隔时间: {interval_seconds}秒\n"
            remark += f"任务说明: 图像识别成功后定时发送第{i+1}条弹幕"

            try:
                # 创建task_data，包含话术内容
                import json

                task_data = {
                    "room_id": room_id,
                    "room_name": room_name,
                    "speech_content": speech["content"],
                    "speech_id": speech.get("id", i + 1),
                    "matched_image": matched_image_path,
                    "interval_seconds": interval_seconds,
                    "task_index": i + 1,
                    "total_tasks": len(speeches),
                }
                task_data_json = json.dumps(task_data, ensure_ascii=False)

                # 插入任务记录（status=0表示可执行，包含task_data）
                cursor.execute(
                    """
                    INSERT INTO tasks (task_id, task_type, room_id, run_time, create_time, status, remark, task_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        task_id,
                        "danmu_task",
                        room_id,
                        run_time.strftime("%Y-%m-%d %H:%M:%S"),
                        current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        0,
                        remark,
                        task_data_json,
                    ),
                )

                created_tasks.append(
                    {
                        "task_id": task_id,
                        "speech": speech,
                        "run_time": run_time,
                        "index": i + 1,
                    }
                )

                print(f"  ✅ 任务 {i+1}: {task_id} -> {run_time.strftime('%H:%M:%S')}")
                
                # 🔥 修复：向监听窗口输出每个任务的详细信息，格式正确
                if i == 0:  # 第一条任务特别标注
                    sync_print(f"📋 第{i+1}条弹幕任务 (首条): {run_time.strftime('%H:%M:%S')}", "success", room_name, "任务创建")
                else:
                    sync_print(f"📋 第{i+1}条弹幕任务: {run_time.strftime('%H:%M:%S')}", "info", room_name, "任务创建")
                
                sync_print(f"   💬 话术内容: {speech['content'][:30]}{'...' if len(speech['content']) > 30 else ''}", "info", room_name, "话术内容")
                sync_print(f"   🆔 任务ID: {task_id}", "info", room_name, "任务标识")

            except Exception as task_e:
                print(f"  ❌ 任务 {i+1} 创建失败: {str(task_e)}")
                continue

        conn.commit()
        conn.close()

        print(f"✅ 成功创建 {len(created_tasks)}/{len(speeches)} 个弹幕任务")
        
        # 🔥 增强：输出详细的任务创建完成信息
        if created_tasks:
            first_task = created_tasks[0]
            last_task = created_tasks[-1]
            print(f"📊 [DANMU_TASK] ===== 弹幕任务创建完成汇总 =====")
            print(f"✅ [DANMU_TASK] 创建成功: {len(created_tasks)}条/{len(speeches)}条")
            print(f"⏰ [DANMU_TASK] 首条执行: {first_task['run_time'].strftime('%H:%M:%S')}")
            if len(created_tasks) > 1:
                print(f"⏰ [DANMU_TASK] 末条执行: {last_task['run_time'].strftime('%H:%M:%S')}")
                total_duration = (last_task['run_time'] - first_task['run_time']).total_seconds()
                print(f"⏳ [DANMU_TASK] 执行时长: {int(total_duration)}秒 ({int(total_duration/60)}分钟)")
            print(f"🎯 [DANMU_TASK] 状态: 所有任务已安排完毕，等待定时执行")
            print(f"📊 [DANMU_TASK] =======================================")
        else:
            print(f"❌ [DANMU_TASK] 未能创建任何弹幕任务")
        
        # 🔥 新增：向监听窗口输出任务创建完成汇总
        sync_print(f"✅ 弹幕任务创建完成", "success", room_name, "任务汇总")
        sync_print(f"📊 成功创建: {len(created_tasks)}条/{len(speeches)}条弹幕任务", "success", room_name, "创建结果")
        
        if created_tasks:
            first_task = created_tasks[0]
            last_task = created_tasks[-1]
            
            # 🔥 重点：首条发送时间推送到监听窗口
            sync_print(f"⏰ 首条弹幕发送时间: {first_task['run_time'].strftime('%H:%M:%S')}", "info", room_name, "首条时间")
            sync_print(f"💬 首条弹幕内容: {first_task['speech']['content'][:30]}{'...' if len(first_task['speech']['content']) > 30 else ''}", "info", room_name, "首条内容")
            
            if len(created_tasks) > 1:
                sync_print(f"⏰ 末条弹幕发送时间: {last_task['run_time'].strftime('%H:%M:%S')}", "info", room_name, "末条时间")
                total_duration = (last_task['run_time'] - first_task['run_time']).total_seconds()
                sync_print(f"⏳ 弹幕发送总时长: {int(total_duration)}秒 ({int(total_duration/60)}分钟)", "info", room_name, "时长统计")
            
            sync_print(f"📋 所有弹幕任务已安排完毕，等待定时执行", "info", room_name, "任务状态")

        # 打印装配信息
        printDanmuTasksInfo(room_id, room_name, created_tasks, interval_seconds)

        return [task["task_id"] for task in created_tasks]

    except Exception as e:
        print(f"❌ 创建弹幕任务失败: {str(e)}")
        return []


def createDanmuTaskToDatabase(
    room_id, room_name, matched_image_path, speeches, interval_seconds
):
    """
    创建弹幕任务到数据库

    Args:
        room_id: 直播间ID
        room_name: 直播间名称
        matched_image_path: 匹配的图片路径
        speeches: 话术列表
        interval_seconds: 发送间隔（秒）

    Returns:
        str: 任务ID，失败返回None
    """
    try:
        import sqlite3
        from datetime import datetime

        # 生成任务ID
        timestamp = int(datetime.now().timestamp())
        task_id = f"danmu_task_{room_id}_{timestamp}"

        print(f"📝 创建弹幕任务到数据库: {task_id}")

        conn = sqlite3.connect("system.db")
        cursor = conn.cursor()

        # 确保tasks表存在
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                task_type TEXT NOT NULL,
                room_id INTEGER,
                run_time TEXT NOT NULL,
                create_time TEXT NOT NULL,
                status INTEGER DEFAULT 1,
                remark TEXT
            )
        """
        )

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_time = current_time  # 立即开始

        # 构建任务备注
        remark = f"弹幕发送任务 - 开发环境\n"
        remark += f"直播间: {room_name} (ID: {room_id})\n"
        remark += f"匹配图片: {os.path.basename(matched_image_path)}\n"
        remark += f"话术数量: {len(speeches)} 条\n"
        remark += f"发送间隔: {interval_seconds}秒\n"
        remark += f"任务说明: 图像识别成功后自动发送弹幕话术"

        # 插入任务记录（status=0表示可执行）
        cursor.execute(
            """
            INSERT INTO tasks (task_id, task_type, room_id, run_time, create_time, status, remark)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (task_id, "danmu_task", room_id, run_time, current_time, 0, remark),
        )

        conn.commit()
        conn.close()

        print(f"✅ 弹幕任务已写入数据库: {task_id}")

        # 🔥 装配完成后打印统计信息
        printDanmuTaskInfo(task_id, room_id, room_name, speeches, interval_seconds)

        return task_id

    except Exception as e:
        print(f"❌ 创建弹幕任务数据库记录失败: {str(e)}")
        return None


def printDanmuTasksInfo(room_id, room_name, created_tasks, interval_seconds):
    """
    打印多个弹幕任务装配信息 - 基于数据库查询

    Args:
        room_id: 直播间ID
        room_name: 直播间名称
        created_tasks: 创建的任务列表
        interval_seconds: 发送间隔
    """
    try:
        import sqlite3

        print(f"\n📊 =================== 弹幕任务装配完成 ===================")

        # 查询数据库确认任务已创建
        conn = sqlite3.connect("system.db")
        cursor = conn.cursor()

        task_ids = [task["task_id"] for task in created_tasks]
        placeholders = ",".join(["?" for _ in task_ids])

        cursor.execute(
            f"""
            SELECT task_id, status, run_time, remark
            FROM tasks 
            WHERE task_id IN ({placeholders}) AND task_type = 'danmu_task'
            ORDER BY run_time ASC
        """,
            task_ids,
        )

        db_tasks = cursor.fetchall()
        conn.close()

        print(f"✅ 数据库验证: 成功创建 {len(db_tasks)} 个弹幕任务")
        print(f"📋 任务详情:")
        print(f"   • 直播间: {room_name} (ID: {room_id})")
        print(f"   • 任务类型: danmu_task")
        print(f"   • 发送间隔: {interval_seconds} 秒")
        print(f"   • 状态: 所有任务 status=0 (可执行)")

        print(f"\n💬 弹幕任务列表:")
        for i, (task_id, status, run_time, remark) in enumerate(db_tasks, 1):
            # 从备注中提取话术内容
            lines = remark.split("\n")
            speech_line = next(
                (line for line in lines if line.startswith("话术内容:")),
                "话术内容: 未知",
            )
            speech_content = speech_line.replace("话术内容: ", "")

            print(f"   {i}. {run_time} - {speech_content}")

        print(f"\n🔄 执行逻辑:")
        print(f"   • 执行检查: 每个任务执行前检查 status=0")
        print(f"   • 时间安排: 从现在开始，每{interval_seconds}秒执行一个任务")
        print(f"   • 任务总数: {len(db_tasks)} 个独立任务")
        print(f"   • 完成时间: 大约 {len(db_tasks) * interval_seconds} 秒后全部完成")

        # 显示接下来的执行计划
        if db_tasks:
            print(f"\n⏰ 执行时间表:")
            for i, (task_id, status, run_time, remark) in enumerate(db_tasks[:5], 1):
                status_text = "准备执行" if status == 0 else "已失效"
                print(f"   {i}. {run_time} ({status_text}) - 任务{i}")

            if len(db_tasks) > 5:
                print(f"   ... 等共 {len(db_tasks)} 个任务")

        print(f"=================== 装配信息结束 ===================\n")

    except Exception as e:
        print(f"❌ 打印弹幕任务信息失败: {str(e)}")


def printDanmuTaskInfo(task_id, room_id, room_name, speeches, interval_seconds):
    """
    打印弹幕任务装配信息 - 基于数据库查询

    Args:
        task_id: 任务ID
        room_id: 直播间ID
        room_name: 直播间名称
        speeches: 话术列表
        interval_seconds: 发送间隔
    """
    try:
        import sqlite3
        from datetime import datetime, timedelta

        print(f"\n📊 =================== 弹幕任务装配完成 ===================")

        # 查询数据库确认任务已创建
        conn = sqlite3.connect("system.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT task_id, status, create_time, remark
            FROM tasks 
            WHERE task_id = ? AND task_type = 'danmu_task'
        """,
            (task_id,),
        )

        task_record = cursor.fetchone()
        conn.close()

        if not task_record:
            print(f"❌ 数据库中未找到任务记录: {task_id}")
            return

        print(f"✅ 数据库任务状态: {'有效' if task_record[1] == 1 else '无效'}")
        print(f"📋 任务详情:")
        print(f"   • 任务ID: {task_record[0]}")
        print(f"   • 直播间: {room_name} (ID: {room_id})")
        print(f"   • 创建时间: {task_record[2]}")
        print(f"   • 任务状态: status={task_record[1]}")

        print(f"\n💬 弹幕装配统计:")
        print(f"   • 装配话术数量: {len(speeches)} 条")
        print(f"   • 发送间隔: {interval_seconds} 秒")

        # 计算发送时间表
        print(f"\n⏰ 弹幕发送时间表（前5条）:")
        current_time = datetime.now()
        for i in range(min(5, len(speeches))):
            send_time = current_time + timedelta(seconds=i * interval_seconds)
            speech_preview = speeches[i]["content"][:20] + (
                "..." if len(speeches[i]["content"]) > 20 else ""
            )
            print(f"   {i+1}. {send_time.strftime('%H:%M:%S')} - {speech_preview}")

        if len(speeches) > 5:
            print(f"   ... 等共 {len(speeches)} 条话术，循环发送")

        print(f"\n🔄 执行逻辑:")
        print(f"   • 执行前检查: status=0 才会触发")
        print(
            f"   • 当前状态: status={task_record[1]} ({'可执行' if task_record[1] == 0 else '待触发'})"
        )
        print(f"   • 循环模式: 话术循环使用，永久运行")

        print(f"=================== 装配信息结束 ===================\n")

    except Exception as e:
        print(f"❌ 打印弹幕任务信息失败: {str(e)}")


def checkTaskStatus(task_id):
    """
    检查任务状态是否允许执行

    Args:
        task_id: 任务ID

    Returns:
        bool: status=0时返回True，否则返回False
    """
    try:
        import sqlite3

        conn = sqlite3.connect("system.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT status FROM tasks WHERE task_id = ?
        """,
            (task_id,),
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            status = result[0]
            print(f"📋 任务 {task_id} 当前状态: status={status}")
            return status == 0  # 只有status=0才能执行
        else:
            print(f"❌ 任务 {task_id} 不存在")
            return False

    except Exception as e:
        print(f"❌ 检查任务状态失败: {str(e)}")
        return False


def getRoomNameById(room_id):
    """
    根据room_id查询直播间名称

    Args:
        room_id: 直播间ID

    Returns:
        str: 直播间名称，失败返回None
    """
    try:
        import sqlite3

        conn = sqlite3.connect("system.db")
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM rooms WHERE id = ?", (room_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            room_name = result[0]
            print(f"🔍 [DATABASE] 查询到直播间名称: ID={room_id} -> '{room_name}'")
            return room_name
        else:
            print(f"❌ [DATABASE] 直播间 {room_id} 不存在")
            return None

    except Exception as e:
        print(f"❌ [DATABASE] 查询直播间名称失败: {str(e)}")
        return None


def startLocalDanmuScheduler(
    created_tasks, room_id, room_name, chrome_view, interval_seconds
):
    """
    测试环境专用：启动本地弹幕调度器，阻塞主线程

    Args:
        created_tasks: 创建的任务ID列表
        room_id: 直播间ID
        room_name: 直播间名称
        chrome_view: 微信Chrome窗口对象
        interval_seconds: 发送间隔（秒）

    Returns:
        bool: 是否启动成功
    """
    try:
        print(
            f"\n🧪 [LOCAL_SCHEDULER] =================== 启动测试环境弹幕调度器 ==================="
        )
        print(f"📊 [LOCAL_SCHEDULER] 任务数量: {len(created_tasks)} 个")
        print(f"⏰ [LOCAL_SCHEDULER] 发送间隔: {interval_seconds} 秒")
        print(f"📺 [LOCAL_SCHEDULER] 直播间: {room_name} (ID: {room_id})")

        # 导入APScheduler
        try:
            from apscheduler.schedulers.blocking import BlockingScheduler
            from apscheduler.triggers.date import DateTrigger
            from datetime import datetime, timedelta
            import time
            import json
            import sqlite3
        except ImportError as e:
            print(f"❌ [LOCAL_SCHEDULER] APScheduler导入失败: {e}")
            return False

        # 创建本地调度器（阻塞型）
        scheduler = BlockingScheduler(timezone="Asia/Shanghai")
        print(f"✅ [LOCAL_SCHEDULER] 调度器创建成功")

        # 读取任务详情并注册到调度器
        registered_count = 0
        for task_id in created_tasks:
            try:
                # 从数据库读取任务详情
                conn = sqlite3.connect("system.db")
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT run_time, task_data FROM tasks WHERE task_id = ?",
                    (task_id,),
                )
                result = cursor.fetchone()
                conn.close()

                if not result:
                    print(f"⚠️ [LOCAL_SCHEDULER] 任务数据未找到: {task_id}")
                    continue

                run_time_str, task_data_str = result
                run_time = datetime.strptime(run_time_str, "%Y-%m-%d %H:%M:%S")
                task_data = json.loads(task_data_str)

                # 注册任务到本地调度器
                scheduler.add_job(
                    func=executeLocalDanmuTask,
                    trigger=DateTrigger(run_date=run_time),
                    id=task_id,
                    args=[task_id, task_data, chrome_view],
                    replace_existing=True,
                )

                registered_count += 1
                print(
                    f"  ✅ [LOCAL_SCHEDULER] 任务已注册: {task_id} -> {run_time.strftime('%H:%M:%S')}"
                )

            except Exception as task_e:
                print(f"  ❌ [LOCAL_SCHEDULER] 注册任务失败: {task_id} - {str(task_e)}")
                continue

        if registered_count == 0:
            print(f"❌ [LOCAL_SCHEDULER] 没有任务被成功注册")
            return False

        print(
            f"✅ [LOCAL_SCHEDULER] 成功注册 {registered_count}/{len(created_tasks)} 个任务"
        )

        # 显示即将执行的任务时间表
        jobs = scheduler.get_jobs()
        print(f"\n⏰ [LOCAL_SCHEDULER] 执行时间表:")
        for i, job in enumerate(sorted(jobs, key=lambda x: x.next_run_time), 1):
            next_run = (
                job.next_run_time.strftime("%H:%M:%S") if job.next_run_time else "未知"
            )
            print(f"   {i}. {next_run} - {job.id}")

        print(f"\n🚀 [LOCAL_SCHEDULER] 调度器即将启动（主线程将被阻塞）")
        print(f"💡 [LOCAL_SCHEDULER] 提示: 按 Ctrl+C 可停止调度器")
        print(f"=================== 调度器启动中 ===================\n")

        # 启动调度器（阻塞主线程）
        try:
            scheduler.start()
        except KeyboardInterrupt:
            print(f"\n🛑 [LOCAL_SCHEDULER] 用户手动停止调度器")
            scheduler.shutdown()
            return True
        except Exception as e:
            print(f"\n❌ [LOCAL_SCHEDULER] 调度器运行异常: {str(e)}")
            return False

        return True

    except Exception as e:
        print(f"❌ [LOCAL_SCHEDULER] 启动本地调度器失败: {str(e)}")
        return False


def executeLocalDanmuTask(task_id, task_data, chrome_view):
    """
    执行本地弹幕任务 - 测试环境专用

    Args:
        task_id: 任务ID
        task_data: 任务数据（包含弹幕内容等）
        chrome_view: 微信Chrome窗口对象
    """
    try:
        follow_print(f"💬 [LOCAL_DANMU] 执行弹幕任务: {task_id}", "info", step="执行弹幕任务")

        # 解析任务数据
        room_id = task_data.get("room_id", 0)
        room_name = task_data.get("room_name", "未知直播间")
        speech_content = task_data.get("speech_content", "默认弹幕内容")
        task_index = task_data.get("task_index", 1)
        total_tasks = task_data.get("total_tasks", 1)

        follow_print(f"📋 [LOCAL_DANMU] 任务详情:", "info", room_name=room_name)
        follow_print(f"   • 直播间: {room_name} (ID: {room_id})", "info", room_name=room_name)
        follow_print(f"   • 弹幕内容: {speech_content}", "info", room_name=room_name)
        follow_print(f"   • 任务序号: {task_index}/{total_tasks}", "info", room_name=room_name)

        # 🔥 重新查询真实的直播间名称
        real_room_name = getRoomNameById(room_id)
        if real_room_name:
            room_name = real_room_name
            follow_print(f"🔍 [LOCAL_DANMU] 使用真实直播间名称: {room_name}", "info", room_name=room_name)

        # 获取微信窗口
        wechat = getWechat()
        if not wechat:
            error_msg = "微信窗口未找到，无法发送弹幕"
            follow_print(f"❌ [LOCAL_DANMU] {error_msg}", "error", room_name=room_name)
            showToast("❌ 弹幕发送失败", f"任务{task_index}: 微信窗口未找到")
            markLocalTaskAsExecuted(task_id)
            return

        if not chrome_view:
            error_msg = "微信Chrome窗口未找到，无法发送弹幕"
            follow_print(f"❌ [LOCAL_DANMU] {error_msg}", "error", room_name=room_name)
            showToast("❌ 弹幕发送失败", f"任务{task_index}: Chrome窗口未找到")
            markLocalTaskAsExecuted(task_id)
            return

        # 🔥 重要：激活微信Chrome窗口
        try:
            follow_print(f"🖥️ [LOCAL_DANMU] 激活微信Chrome窗口...", "info", step="激活窗口", room_name=room_name)
            chrome_view.SetActive()
            time.sleep(1)
            follow_print(f"✅ [LOCAL_DANMU] 窗口激活成功", "success", room_name=room_name)
        except Exception as activate_e:
            follow_print(f"⚠️ [LOCAL_DANMU] 窗口激活失败: {str(activate_e)}", "warning", room_name=room_name)

        # 🔥 执行弹幕发送，使用更严格的检测
        follow_print(f"📤 [LOCAL_DANMU] 开始发送弹幕...", "info", step="发送弹幕", room_name=room_name)
        send_success = sendDanmuWithValidation(
            wechat=wechat,
            chrome_view=chrome_view,
            room_name=f"{room_name}的直播",
            content=speech_content,
            task_index=task_index,
        )

        if send_success:
            success_msg = f"弹幕发送成功: 第{task_index}条"
            follow_print(f"✅ [LOCAL_DANMU] {success_msg}", "success", step="弹幕发送完成", room_name=room_name)
            showToast(
                "💬 弹幕发送成功",
                f"直播间: {room_name}\n第{task_index}条弹幕已发送\n内容: {speech_content[:20]}...",
            )
        else:
            error_msg = f"弹幕发送失败: 第{task_index}条"
            follow_print(f"❌ [LOCAL_DANMU] {error_msg}", "error", room_name=room_name)
            showToast(
                "⚠️ 弹幕发送失败",
                f"直播间: {room_name}\n第{task_index}条弹幕发送失败\n请检查微信状态",
            )

        # 标记任务为已执行
        markLocalTaskAsExecuted(task_id)

        follow_print(f"✅ [LOCAL_DANMU] 弹幕任务处理完成: {task_id}", "success", step="任务完成", room_name=room_name)

    except Exception as e:
        follow_print(f"❌ [LOCAL_DANMU] 执行弹幕任务异常: {str(e)}", "error", room_name=room_name)
        showToast("❌ 弹幕任务异常", f"任务执行出错: {str(e)[:30]}...")
        markLocalTaskAsExecuted(task_id)


def sendDanmuWithValidation(wechat, chrome_view, room_name, content, task_index):
    """
    带验证的弹幕发送 - 更准确的成功/失败检测

    Args:
        wechat: 微信窗口对象
        chrome_view: 微信Chrome窗口对象
        room_name: 直播间名称（包含"的直播"后缀）
        content: 弹幕内容
        task_index: 任务序号

    Returns:
        bool: 是否成功发送
    """
    try:
        follow_log_detailed(f"切换到直播间: {room_name}", "info", room_name, "弹幕发送")

        # 步骤1: 确保微信被激活
        if getWxChromeWindowByIndex(0) is None:
            if wechat:
                follow_log_detailed("激活微信窗口", "info", room_name, "弹幕发送")
                wechat.SetActive()
                time.sleep(1)
            else:
                follow_log_detailed("微信窗口对象为空", "error", room_name, "弹幕发送")
                return False

        # 步骤2: 切换到目标直播间
        try:
            follow_log_detailed("正在切换到直播间标签页...", "info", room_name, "弹幕发送")
            switchRoom(chrome_view, room_name)
            time.sleep(2)
            follow_log_detailed("直播间切换成功", "success", room_name, "弹幕发送")
        except Exception as switch_e:
            follow_log_detailed(f"切换直播间失败: {str(switch_e)}", "error", room_name, "弹幕发送")
            return False

        # 步骤3: 检查是否在正确的直播间
        try:
            if not isRoomOpenByTabName(chrome_view, room_name):
                follow_log_detailed(f"直播间标签页不存在: {room_name}", "error", room_name, "弹幕发送")
                return False
            follow_log_detailed("确认在正确的直播间", "success", room_name, "弹幕发送")
        except Exception as check_e:
            follow_log_detailed(f"检查直播间状态失败: {str(check_e)}", "warning", room_name, "弹幕发送")
            # 继续尝试发送

        # 步骤4: 检查直播是否结束
        try:
            if liveEnd(chrome_view, room_name):
                follow_log_detailed("直播已结束，无法发送弹幕", "error", room_name, "弹幕发送")
                sync_print("📺 直播已结束，停止弹幕发送", "error", room_name, "弹幕发送")
                return False
            follow_log_detailed("直播正在进行中", "success", room_name, "弹幕发送")
        except Exception as live_e:
            follow_log_detailed(f"检查直播状态失败: {str(live_e)}", "warning", room_name, "弹幕发送")
            # 继续尝试发送

        # 步骤5: 尝试点击聊天按钮
        try:
            follow_log_detailed("点击聊天按钮...", "info", room_name, "弹幕发送")
            clickChatBtn()
            time.sleep(1)
            follow_log_detailed("聊天按钮点击成功", "success", room_name, "弹幕发送")
        except Exception as chat_e:
            follow_log_detailed(f"点击聊天按钮失败: {str(chat_e)}", "warning", room_name, "弹幕发送")
            # 继续尝试发送内容

        # 步骤6: 发送弹幕内容
        try:
            follow_log_detailed(f"正在输入弹幕内容: {content[:30]}...", "info", room_name, "弹幕发送")

            # 清空现有内容
            auto.SendKeys("{Ctrl}a{Del}")
            time.sleep(0.5)

            # 输入新内容
            auto.SendKeys(content)
            time.sleep(1)

            # 发送弹幕（根据配置选择发送方式）
            send_success = sendDanmuByConfig(room_name)
            time.sleep(1)

            if send_success:
                follow_log_detailed("弹幕内容发送完成", "success", room_name, "弹幕发送")
            else:
                follow_log_detailed("弹幕内容发送失败", "error", room_name, "弹幕发送")

            # 🔥 可选: 验证发送成功（检查输入框是否已清空）
            # 这里可以添加更精确的验证逻辑

            return True

        except Exception as send_e:
            follow_log_detailed(f"发送弹幕内容失败: {str(send_e)}", "error", room_name, "弹幕发送")
            return False

    except Exception as e:
        follow_log_detailed(f"弹幕发送过程异常: {str(e)}", "error", room_name, "弹幕发送")
        return False


def markLocalTaskAsExecuted(task_id):
    """
    标记本地任务为已执行

    Args:
        task_id: 任务ID
    """
    try:
        import sqlite3

        conn = sqlite3.connect("system.db")
        cursor = conn.cursor()

        cursor.execute("UPDATE tasks SET status = 1 WHERE task_id = ?", (task_id,))
        conn.commit()
        conn.close()

        print(f"✅ [LOCAL_TASK] 任务已标记为已执行: {task_id}")

    except Exception as e:
        print(f"❌ [LOCAL_TASK] 标记任务状态失败: {str(e)}")


def getRoomSpeeches(room_id):
    """
    获取直播间的话术列表

    Args:
        room_id: 直播间ID

    Returns:
        list: 话术列表
    """
    try:
        import sqlite3

        conn = sqlite3.connect("system.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT s.content, s.id
            FROM room_speeches rs
            JOIN speech s ON rs.speech_id = s.id
            WHERE rs.room_id = ? AND rs.status = 1 AND s.status = 1
            ORDER BY rs.create_time ASC
        """

        cursor.execute(query, (room_id,))
        results = cursor.fetchall()

        speeches = [dict(row) for row in results]
        conn.close()

        return speeches

    except Exception as e:
        print(f"❌ 获取直播间话术失败: {str(e)}")
        return []


def startScheduledDanmuTask(
    task_id,
    room_id,
    room_name,
    chrome_view,
    speeches,
    interval_minutes=5,
    matched_image=None,
):
    """
    开始定时弹幕任务 - 带状态检查

    Args:
        task_id: 任务ID
        room_id: 直播间ID
        room_name: 直播间名称
        chrome_view: 微信Chrome窗口对象
        speeches: 话术列表
        interval_minutes: 间隔时间（分钟）
        matched_image: 匹配成功的图片路径

    Returns:
        bool: 是否成功开始任务
    """
    try:
        import threading
        import time
        import random
        import sqlite3

        print(f"🔄 开始定时弹幕任务: {task_id}")
        print(f"⏰ 间隔时间: {interval_minutes} 分钟")
        print(f"💬 可用话术: {len(speeches)} 条")

        # 🔥 检查任务状态，只有status=0才会触发
        print(f"🔍 检查任务状态...")
        if not checkTaskStatus(task_id):
            print(f"⚠️ 任务 {task_id} 状态不允许执行（status!=0）")
            return False

        print(f"✅ 任务状态检查通过，开始执行弹幕任务")

        def danmu_worker():
            """弹幕任务工作线程"""
            try:
                speech_index = 0
                task_start_time = time.time()

                while True:
                    try:
                        # 检查是否还在直播中（可选功能）
                        if not isStillLive(chrome_view, room_name):
                            print(f"🛑 直播已结束，停止弹幕任务")
                            break

                        # 选择话术（循环使用）
                        if speeches:
                            current_speech = speeches[speech_index % len(speeches)]
                            speech_content = current_speech["content"]

                            print(
                                f"💬 当前话术（{speech_index + 1}）: {speech_content[:50]}{'...' if len(speech_content) > 50 else ''}"
                            )

                            # 发送弹幕
                            success = switchRoomAndSendContent(
                                wechat=getWechat(),
                                chromeView=chrome_view,
                                room_name=f"{room_name}的直播",
                                content=speech_content,
                            )

                            if success:
                                print(f"✅ 弹幕发送成功: {speech_content[:30]}")
                                # 记录成功日志
                                logDanmuSendResult(
                                    room_id,
                                    room_name,
                                    speech_content,
                                    True,
                                    matched_image,
                                )
                            else:
                                print(f"❌ 弹幕发送失败: {speech_content[:30]}")
                                # 记录失败日志
                                logDanmuSendResult(
                                    room_id,
                                    room_name,
                                    speech_content,
                                    False,
                                    matched_image,
                                )

                            speech_index += 1

                        # 等待下次发送（加入随机延迟避免被检测）
                        base_delay = interval_minutes * 60  # 转换为秒
                        random_delay = random.randint(-30, 30)  # 随机偏移±30秒
                        actual_delay = max(
                            60, base_delay + random_delay
                        )  # 最小间隔为1分钟

                        print(f"⏳ 等待 {actual_delay} 秒后发送下一条弹幕...")
                        time.sleep(actual_delay)

                    except Exception as worker_e:
                        print(f"❌ 弹幕任务工作线程异常: {str(worker_e)}")
                        intervals = getIntervalConfig()
                        time.sleep(intervals["follow_task_retry"])  # 异常时等待配置的时间再重试

            except Exception as e:
                print(f"❌ 弹幕任务线程失败: {str(e)}")

        # 在后台线程中启动弹幕任务
        danmu_thread = threading.Thread(target=danmu_worker, daemon=True)
        danmu_thread.start()

        print(f"✅ 弹幕任务已在后台开始运行")
        return True

    except Exception as e:
        print(f"❌ 开始弹幕任务失败: {str(e)}")
        return False


def isStillLive(chrome_view, room_name):
    """
    检查直播是否还在进行中

    Args:
        chrome_view: 微信Chrome窗口对象
        room_name: 直播间名称

    Returns:
        bool: 是否还在直播
    """
    try:
        # 检查是否存在"直播已结束"文字
        live_end_control = chrome_view.TextControl(Name="直播已结束")
        if live_end_control.Exists(0, 0):
            return False

        # 检查直播间标签是否还存在
        room_tab = chrome_view.TabItemControl(Name=f"{room_name}的直播")
        if not room_tab.Exists(0, 0):
            return False

        return True

    except Exception as e:
        print(f"⚠️ 检查直播状态失败: {str(e)}")
        # 异常情况下假设还在直播
        return True


def logDanmuSendResult(room_id, room_name, content, success, matched_image=None):
    """
    记录弹幕发送结果

    Args:
        room_id: 直播间ID
        room_name: 直播间名称
        content: 弹幕内容
        success: 是否成功
        matched_image: 匹配的图片路径
    """
    try:
        import sqlite3
        from datetime import datetime

        conn = sqlite3.connect("system.db")
        cursor = conn.cursor()

        # 检查是否存在danmu_log表，不存在则创建
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS danmu_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER,
                room_name TEXT,
                content TEXT,
                success INTEGER,
                matched_image TEXT,
                send_time TEXT,
                create_time TEXT
            )
        """
        )

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT INTO danmu_log (room_id, room_name, content, success, matched_image, send_time, create_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                room_id,
                room_name,
                content,
                1 if success else 0,
                matched_image,
                current_time,
                current_time,
            ),
        )

        conn.commit()
        conn.close()

        status_text = "成功" if success else "失败"
        print(f"📝 弹幕发送日志已记录: {status_text} - {content[:30]}")

    except Exception as e:
        print(f"❌ 记录弹幕日志失败: {str(e)}")


# 此函数已删除，功能已被checkTargetImageExists和checkMultipleImagesExists替代


def get_image_remark_by_path(image_path, db_path='system.db'):
    """
    根据图片路径获取图片备注信息
    
    Args:
        image_path: 图片路径
        db_path: 数据库路径
        
    Returns:
        str: 图片备注，如果没有则返回文件名
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT remark FROM images WHERE path = ?", (image_path,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return result[0]
        else:
            # 如果没有备注，返回文件名
            import os
            return f"图片文件: {os.path.basename(image_path)}"
            
    except Exception as e:
        print(f"❌ 获取图片备注失败: {str(e)}")
        import os
        return f"图片文件: {os.path.basename(image_path)}"


def checkMultipleImagesExists(image_paths, room_name=None):
    """
    改进的多图片匹配检测 - 更宽松的识别策略，详细日志同步到监听窗口
    Args:
        image_paths: 图片路径列表，可以是字符串（单图）或列表（多图）
        room_name: 直播间名称，用于日志记录
    Returns:
        dict: {
            'success': bool,  # 是否匹配成功
            'matched_image': str,  # 匹配成功的图片路径
            'matched_count': int,  # 匹配成功的图片数量
            'total_count': int,  # 总检测图片数量
            'error': str  # 错误信息（如有）
        }
    """
    try:
        # 处理单图片情况
        if isinstance(image_paths, str):
            image_paths = [image_paths]

        if not image_paths:
            if room_name:
                sync_print("❌ 图片路径列表为空", "error", room_name, "图像检测")
            return {
                "success": False,
                "matched_image": None,
                "matched_count": 0,
                "total_count": 0,
                "error": "图片路径列表为空",
            }

        # 🔥 详细的检测开始信息同步到监听窗口
        sync_print(f"🔍 开始多图匹配检测，共 {len(image_paths)} 张绑定图片", "info", room_name, "图像检测")
        
        # 🔥 修复：显示所有绑定的图片路径和备注信息
        for i, path in enumerate(image_paths, 1):
            import os
            filename = os.path.basename(path)
            # 获取图片备注信息
            image_remark = get_image_remark_by_path(path)
            if image_remark:
                sync_print(f"   图片{i}: {filename} (备注: {image_remark})", "info", room_name, "图片列表")
            else:
                sync_print(f"   图片{i}: {filename} (无备注)", "info", room_name, "图片列表")

        # 定义多个置信度级别，从高到低尝试
        confidence_levels = [0.8, 0.7, 0.6, 0.5]
        sync_print(f"🎯 置信度策略: {confidence_levels} (从高到低逐级尝试)", "info", room_name, "检测策略")

        for confidence in confidence_levels:
            sync_print(f"🎯 当前尝试置信度: {confidence}", "info", room_name, "置信度调整")

            for i, image_path in enumerate(image_paths):
                try:
                    filename = os.path.basename(image_path)
                    sync_print(f"  [{i+1}/{len(image_paths)}] 正在检测图片: {filename}", "info", room_name, "图片检测")

                    # 检查文件是否存在
                    if not os.path.exists(image_path):
                        sync_print(f"    ⚠️ 图片文件不存在: {filename}", "warning", room_name, "文件检查")
                        continue

                    # 检查文件大小
                    file_size = os.path.getsize(image_path)
                    if file_size == 0:
                        sync_print(f"    ⚠️ 图片文件为空: {filename}", "warning", room_name, "文件检查")
                        continue

                    sync_print(f"    📊 文件大小: {file_size} bytes", "info", room_name, "文件信息")

                    # 进行图像匹配
                    sync_print(f"    🔍 开始屏幕匹配 (置信度: {confidence})...", "info", room_name, "匹配执行")
                    
                    location = pyautogui.locateOnScreen(
                        image_path, confidence=confidence
                    )
                    if location is not None:
                        # 获取图片备注信息
                        image_remark = get_image_remark_by_path(image_path)
                        sync_print(f"    ✅ 匹配成功: {filename}", "success", room_name, "匹配结果")
                        sync_print(f"    📝 图片备注: {image_remark}", "success", room_name, "匹配详情")
                        sync_print(f"    📍 匹配位置: {location}", "success", room_name, "匹配详情")
                        sync_print(f"    🎯 成功置信度: {confidence}", "success", room_name, "匹配详情")

                        # 匹配到一张即可返回成功
                        return {
                            "success": True,
                            "matched_image": image_path,
                            "matched_image_remark": image_remark,
                            "matched_count": 1,
                            "total_count": len(image_paths),
                            "error": None,
                            "confidence_used": confidence,
                            "matched_location": location,
                        }
                    else:
                        sync_print(f"    ❌ 置信度 {confidence} 未匹配: {filename}", "warning", room_name, "匹配结果")

                except Exception as e:
                    # 获取图片备注信息
                    image_remark = get_image_remark_by_path(image_path)
                    sync_print(f"    ❌ 检测异常: {filename} - {str(e)}", "error", room_name, "匹配异常")
                    sync_print(f"    📝 图片备注: {image_remark}", "error", room_name, "图片信息")
                    sync_print(f"    🔍 使用置信度: {confidence}", "error", room_name, "匹配参数")
                    sync_print(f"    📁 图片路径: {image_path}", "error", room_name, "文件信息")
                    continue

        # 所有置信度级别都失败
        sync_print(f"❌ 所有图片在所有置信度级别均未匹配成功", "error", room_name, "最终结果")
        sync_print(f"🔍 尝试的置信度: {confidence_levels}", "error", room_name, "最终结果")
        
        return {
            "success": False,
            "matched_image": None,
            "matched_count": 0,
            "total_count": len(image_paths),
            "error": f"所有图片在所有置信度级别({confidence_levels})下均未匹配成功",
            "confidence_levels_tried": confidence_levels,
        }

    except Exception as e:
        error_msg = f"多图匹配检测失败: {str(e)}"
        if room_name:
            sync_print(f"❌ {error_msg}", "error", room_name, "匹配异常")
        else:
            print(f"❌ {error_msg}")
        return {
            "success": False,
            "matched_image": None,
            "matched_count": 0,
            "total_count": len(image_paths) if isinstance(image_paths, list) else 1,
            "error": error_msg,
        }


# 查询是否已经直播间是否已经结束
def liveEnd(chrome, room_name=""):
    """
    检测直播间是否已结束

    Args:
        chrome: 微信Chrome窗口对象
        room_name: 直播间名称（用于日志输出）

    Returns:
        bool: True表示直播已结束，False表示直播正在进行
    """
    try:
        # 检测"直播已结束"文字是否存在
        live_end_ctrl = chrome.TextControl(Name="直播已结束")
        is_ended = live_end_ctrl.Exists(maxSearchSeconds=2, searchIntervalSeconds=0.5)

        if is_ended:
            sync_print("📺 检测到直播已结束", "warning", room_name, "直播状态")
            return True
        else:
            sync_print("🔴 直播正在进行中", "success", room_name, "直播状态")
            return False

    except Exception as e:
        sync_print(f"❌ 检测直播状态失败: {str(e)}", "error", room_name, "直播状态")
        # 异常情况下，假设直播正在进行
        return False


# 这些方法已废弃，功能已被其他方法替代，删除以减少代码冗余


# 根据标签名称关闭
def closeTabByTitle(chrome, title):
    chrome.TabItemControl(Name=title).Click()
    auto.SendKeys("{CTRL}w")


# 跟播函数
def followLiveTask():
    with auto.UIAutomationInitializerInThread():  # ✅ 加这句初始化 COM
        initEnterRoom(getWechat(), roomName="星光漫游12")


def switchRoomAndSendContent(wechat, chromeView, room_name, content):
    """
    切换直播间并发送弹幕内容

    Args:
        wechat: 微信窗口对象
        chromeView: 微信Chrome窗口对象
        room_name: 直播间名称（包含"的直播"后缀）
        content: 要发送的内容

    Returns:
        bool: 是否成功发送
    """
    try:
        room_clean_name = room_name.replace("的直播", "")  # 提取干净的直播间名称
        sync_print(f"🔄 切换到直播间: {room_name}", "info", room_clean_name, "直播间切换")

        # 🔥 激活微信Chrome窗口确保焦点正确
        try:
            sync_print(f"🖥️ 激活微信Chrome窗口...", "info", room_clean_name, "窗口激活")
            chromeView.SetActive()
            time.sleep(1)
            sync_print(f"✅ 微信Chrome窗口激活成功", "success", room_clean_name, "窗口激活")
        except Exception as activate_e:
            sync_print(f"❌ 激活微信Chrome窗口失败: {str(activate_e)}", "error", room_clean_name, "窗口激活")
            return False

        # 选择指定直播间
        try:
            sync_print(f"🔄 切换到直播间标签页: {room_name}", "info", room_clean_name, "标签页切换")
            switchRoom(chromeView, room_name)
            time.sleep(2)
            sync_print(f"✅ 直播间标签页切换成功", "success", room_clean_name, "标签页切换")
        except Exception as switch_e:
            sync_print(f"❌ 切换直播间失败: {str(switch_e)}", "error", room_clean_name, "标签页切换")
            return False

        # 🔥 点击聊天按钮确保在输入框
        try:
            sync_print(f"🔘 点击聊天按钮...", "info", room_clean_name, "界面操作")
            clickChatBtn()
            time.sleep(1)
            sync_print(f"✅ 聊天按钮点击成功", "success", room_clean_name, "界面操作")
        except Exception as chat_e:
            sync_print(f"⚠️ 点击聊天按钮失败: {str(chat_e)}", "warning", room_clean_name, "界面操作")
            # 继续尝试发送

        # 🔥 发送前最后一次确保窗口激活
        try:
            sync_print(f"🔒 发送前最后确认窗口激活状态...", "info", room_clean_name, "窗口确认")
            # 再次激活Chrome窗口确保焦点正确
            chromeView.SetActive()
            time.sleep(0.5)

            # 确保在正确的直播间标签页
            switchRoom(chromeView, room_name)
            time.sleep(0.5)
            sync_print(f"✅ 窗口激活状态确认完成", "success", room_clean_name, "窗口确认")
        except Exception as final_activate_e:
            sync_print(f"⚠️ 最终窗口激活失败: {str(final_activate_e)}", "warning", room_clean_name, "窗口确认")
            # 继续尝试发送

        # 发送内容
        try:
            sync_print(f"📝 输入弹幕内容: {content[:30]}...", "info", room_clean_name, "弹幕输入")

            # 🔥 重要：确保输入框有焦点，先点击一下聊天区域
            try:
                clickChatBtn()
                time.sleep(0.5)
            except:
                sync_print(f"⚠️ 重新点击聊天按钮失败，继续尝试发送", "warning", room_clean_name, "界面操作")

            # 清空并输入内容
            sync_print(f"⌨️ 正在输入弹幕内容...", "info", room_clean_name, "弹幕输入")
            sendContent(f"{content}")
            time.sleep(1)

            # 🔥 重要：根据配置发送弹幕
            sync_print(f"📤 准备发送弹幕...", "info", room_clean_name, "弹幕发送")
            # 根据配置选择发送方式
            send_success = sendDanmuByConfig(room_clean_name)
            time.sleep(1)

            if send_success:
                sync_print(f"✅ 弹幕发送成功: {content[:50]}", "success", room_clean_name, "弹幕发送")
            else:
                sync_print(f"❌ 弹幕发送失败: {content[:50]}", "error", room_clean_name, "弹幕发送")
                return False

            # 🔥 新增：弹幕发送成功后截图
            try:
                sync_print(f"📸 弹幕发送成功，正在截图...", "info", room_clean_name, "截图保存")
                screenshot_path = screenshotAfterDanmu(room_name, content, chromeView)
                if screenshot_path:
                    sync_print(f"✅ 截图已保存: {os.path.basename(screenshot_path)}", "success", room_clean_name, "截图保存")
                    print(f"📷 [SCREENSHOT] 截图保存成功: {screenshot_path}")
                else:
                    sync_print(f"⚠️ 截图功能已关闭或截图失败", "warning", room_clean_name, "截图保存")
                    print(f"💡 [SCREENSHOT] 截图功能未开启或失败")
            except Exception as screenshot_e:
                sync_print(f"❌ 截图过程异常: {str(screenshot_e)}", "error", room_clean_name, "截图保存")
                print(f"❌ [SCREENSHOT] 截图异常: {str(screenshot_e)}")

            return True

        except Exception as send_e:
            sync_print(f"❌ 发送内容失败: {str(send_e)}", "error", room_clean_name, "弹幕发送")
            return False

    except Exception as e:
        sync_print(f"❌ 切换直播间并发送内容失败: {str(e)}", "error", room_clean_name, "整体流程")
        return False


def createNextRecognitionTask(room_id, room_name):
    """
    创建下次图像识别任务并返回任务信息
    
    Args:
        room_id: 直播间ID
        room_name: 直播间名称
        
    Returns:
        dict: 包含任务信息的字典，如果失败返回None
    """
    try:
        from datetime import datetime, timedelta
        import uuid
        import sqlite3
        
        # 获取重试间隔从配置文件
        intervals = getIntervalConfig()
        retry_interval = intervals["image_recognition_retry"]
        
        # 计算下次执行时间
        next_time = datetime.now() + timedelta(seconds=retry_interval)
        next_time_str = next_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 生成任务ID
        task_id = f"image_recognition_retry_{room_id}_{int(next_time.timestamp())}"
        
        # 创建任务数据
        task_data = {
            "room_id": room_id,
            "room_name": room_name,
            "retry_count": 1,
            "reason": "image_recognition_failed"
        }
        
        # 保存到数据库（如果需要的话）
        try:
            conn = sqlite3.connect("system.db")
            cursor = conn.cursor()
            
            # 这里可以插入到任务表，但现在先简单返回信息
            # cursor.execute(...)
            
            conn.close()
        except Exception as db_e:
            print(f"⚠️ 保存识别重试任务到数据库失败: {db_e}")
        
        return {
            "task_id": task_id,
            "next_time": next_time_str,
            "interval": retry_interval,
            "room_id": room_id,
            "room_name": room_name
        }
        
    except Exception as e:
        print(f"❌ 创建下次识别任务失败: {str(e)}")
        return None


def performImageMatchingAndCreateDanmuTask(room_id, room_name, chrome_view):
    """
    执行图像匹配并在成功时创建弹幕任务 - 增强日志版本

    Args:
        room_id: 直播间ID
        room_name: 直播间名称
        chrome_view: 微信Chrome窗口对象

    Returns:
        bool: 是否执行成功
    """
    try:
        follow_log_detailed("开始图像匹配流程", "info", room_name, "图像识别")
        follow_log_detailed(f"执行参数 - 直播间ID: {room_id}, Chrome窗口: {'存在' if chrome_view else '空'}",
                          "info", room_name, "图像识别")

        # 🔥 新增：输出当前图像识别配置到监听窗口
        try:
            image_interval = getImageRecognitionRetryInterval()

            # 从配置文件读取功能开关
            config = loadConfig()
            system_config = config.get("system_config", {})
            features = system_config.get("features", {})
            image_enabled = features.get("enable_image_recognition", True)

            sync_print(f"🔍 图像识别重试间隔: {image_interval}秒", "info", room_name, "任务配置")
            sync_print(f"🔍 图像识别功能: {'✅ 已开启' if image_enabled else '❌ 已关闭'}", "info", room_name, "任务配置")

        except Exception as config_e:
            sync_print(f"⚠️ 读取图像识别配置失败: {str(config_e)}", "warning", room_name, "任务配置")

        # # 🔥 显示开始图像识别的Toast通知 - 已注释
        # showToast(
        #     "🔍 开始图像识别",
        #     f"直播间: {room_name}\n正在检测屏幕中的商品图片\n请保持直播间页面在前台",
        # )

        # 🔥 重要：激活微信Chrome窗口，确保图像识别在正确的窗口中进行
        follow_log_detailed("步骤1: 激活微信Chrome窗口", "info", room_name, "窗口管理")
        if chrome_view:
            try:
                follow_log_detailed("尝试激活现有窗口对象...", "info", room_name, "窗口管理")
                chrome_view.SetActive()
                follow_log_detailed("微信Chrome窗口激活成功", "success", room_name, "窗口管理")

                # 等待窗口激活完成
                import time

                time.sleep(1)
                follow_log_detailed("窗口激活等待完成（1秒）", "info", room_name, "窗口管理")

            except Exception as activate_error:
                follow_log_detailed(f"激活现有窗口失败: {str(activate_error)}", "warning", room_name, "窗口管理")
                follow_log_detailed("尝试重新获取窗口...", "info", room_name, "窗口管理")

                # 尝试重新获取窗口
                chrome_view = getWxChromeWindowByIndex(0)
                if chrome_view:
                    chrome_view.SetActive()
                    time.sleep(1)
                    follow_log_detailed("重新获取并激活窗口成功", "success", room_name, "窗口管理")
                else:
                    follow_log_detailed("无法获取微信Chrome窗口，图像识别将失败", "error", room_name, "窗口管理")
                    return False
        else:
            follow_log_detailed("窗口对象为空，尝试重新获取...", "warning", room_name, "窗口管理")
            chrome_view = getWxChromeWindowByIndex(0)
            if chrome_view:
                chrome_view.SetActive()
                time.sleep(1)
                follow_log_detailed("重新获取并激活窗口成功", "success", room_name, "窗口管理")
            else:
                follow_log_detailed("无法获取微信Chrome窗口，跳过图像匹配", "error", room_name, "窗口管理")
                return False

        # 获取直播间绑定的商品图片
        follow_log_detailed("步骤2: 获取绑定的商品图片", "info", room_name, "数据查询")
        image_paths = getRoomProductImages(room_id)

        if not image_paths:
            follow_log_detailed("该直播间没有绑定商品图片", "warning", room_name, "数据查询")
            follow_log_detailed("无图片可匹配，跳过图像识别", "warning", room_name, "数据查询")
            
            # # 🔥 显示无绑定图片的Toast通知 - 已注释
            # showToast(
            #     "⚠️ 图像识别跳过",
            #     f"直播间: {room_name}\n该直播间没有绑定商品图片\n请先在后台绑定商品和图片",
            # )
            return False

        follow_log_detailed(f"找到 {len(image_paths)} 张绑定图片", "success", room_name, "数据查询")
        for i, path in enumerate(image_paths, 1):
            follow_log_detailed(f"图片 {i}: {path}", "info", room_name, "数据查询")

        # 🔥 显示正在识别中的Toast通知
        showToast(
            "🎯 图像识别中...",
            f"直播间: {room_name}\n找到 {len(image_paths)} 张商品图片\n正在屏幕中搜索匹配...",
        )

        # 执行多图匹配
        follow_log_detailed("步骤3: 执行图像识别匹配", "info", room_name, "图像匹配")
        follow_log_detailed("开始在屏幕中搜索商品图片...", "info", room_name, "图像匹配")

        match_result = checkMultipleImagesExists(image_paths, room_name)

        follow_log_detailed("匹配结果统计:", "info", room_name, "图像匹配")
        follow_log_detailed(f"匹配成功: {match_result.get('success', False)}", "info", room_name, "图像匹配")
        follow_log_detailed(f"匹配图片: {match_result.get('matched_image', 'None')}", "info", room_name, "图像匹配")
        if match_result.get('matched_image_remark'):
            follow_log_detailed(f"图片备注: {match_result.get('matched_image_remark')}", "info", room_name, "图像匹配")
        follow_log_detailed(f"成功数量: {match_result.get('matched_count', 0)}", "info", room_name, "图像匹配")
        follow_log_detailed(f"总计图片: {match_result.get('total_count', 0)}", "info", room_name, "图像匹配")
        if match_result.get("error"):
            follow_log_detailed(f"错误信息: {match_result.get('error')}", "warning", room_name, "图像匹配")
        if match_result.get("confidence_used"):
            follow_log_detailed(f"使用置信度: {match_result.get('confidence_used')}", "info", room_name, "图像匹配")

        if match_result["success"]:
            # 🔥 详细的成功匹配信息
            import os
            matched_filename = os.path.basename(match_result['matched_image'])
            follow_log_detailed("🎉 图像匹配成功！", "success", room_name, "匹配结果")
            follow_log_detailed(f"✅ 成功匹配图片: {matched_filename}", "success", room_name, "匹配详情")
            if match_result.get('matched_image_remark'):
                follow_log_detailed(f"📝 图片备注: {match_result.get('matched_image_remark')}", "success", room_name, "匹配详情")
            follow_log_detailed(f"📊 匹配统计: {match_result['matched_count']}/{match_result['total_count']} 张图片", "success", room_name, "匹配统计")
            follow_log_detailed(f"🎯 使用置信度: {match_result.get('confidence_used', '未知')}", "success", room_name, "匹配参数")
            
            # 显示匹配位置信息
            if match_result.get('matched_location'):
                location = match_result['matched_location']
                follow_log_detailed(f"📍 匹配位置: x={location.left}, y={location.top}, w={location.width}, h={location.height}", "success", room_name, "匹配位置")
            
            follow_log_detailed(f"📁 完整路径: {match_result['matched_image']}", "info", room_name, "文件信息")
            
            # 🔥 新增：获取并显示图片备注信息
            matched_image_path = match_result['matched_image']
            image_remark = get_image_remark_by_path(matched_image_path)
            if image_remark:
                sync_print(f"📝 图片备注: {image_remark}", "success", room_name, "图片信息")
                print(f"📝 [IMAGE_MATCH] 图片备注: {image_remark}")
            else:
                sync_print(f"📝 图片备注: 无备注信息", "info", room_name, "图片信息")
                print(f"📝 [IMAGE_MATCH] 图片备注: 无备注信息")

            # 🔥 显示图像识别成功的Toast通知
            import os
            matched_image_name = os.path.basename(match_result['matched_image'])
            confidence_used = match_result.get('confidence_used', '未知')
            
            showToast(
                "🎉 图像识别成功！",
                f"直播间: {room_name}\n✅ 检测到商品图片: {matched_image_name}\n🎯 使用置信度: {confidence_used}\n⏰ 即将创建弹幕任务...",
            )

            # 🔥 更新进度：图像识别成功
            try:
                from apis import add_follow_progress_log, update_follow_progress_status
                add_follow_progress_log(f"🎯 图像识别成功，检测到商品图片", "success", 75, "识别成功")
                update_follow_progress_status(progress=75, step="图像识别成功")
            except:
                pass
            
            # 创建弹幕任务
            follow_log_detailed("步骤4: 创建弹幕发送任务", "info", room_name, "弹幕任务")
            follow_log_detailed("匹配成功，开始创建定时弹幕任务...", "info", room_name, "弹幕任务")

            task_created = createDanmuTaskAfterImageMatch(
                room_id=room_id,
                room_name=room_name,
                matched_image_path=match_result["matched_image"],
                chrome_view=chrome_view,
            )

            if task_created:
                # 获取实际的弹幕发送间隔
                interval_seconds = getBulletScreenInterval()
                interval_minutes = interval_seconds // 60
                interval_display = f"{interval_minutes}分钟" if interval_minutes > 0 else f"{interval_seconds}秒"
                follow_log_detailed(f"弹幕任务创建成功，将开始每{interval_display}发送一次弹幕", "success", room_name, "弹幕任务")
                
                # 🔥 更新进度：弹幕任务创建成功
                try:
                    from apis import add_follow_progress_log, update_follow_progress_status
                    add_follow_progress_log(f"✅ 弹幕任务创建成功，开始定时发送", "success", 85, "任务已创建")
                    update_follow_progress_status(progress=85, step="弹幕任务运行中")
                except:
                    pass
                
                follow_log_detailed("图像识别流程完成", "success", room_name, "完成")
                return True
            else:
                follow_log_detailed("弹幕任务创建失败", "error", room_name, "弹幕任务")
                follow_log_detailed("图像匹配成功但弹幕任务创建失败", "warning", room_name, "完成")
                
                # # 🔥 显示弹幕任务创建失败的Toast通知 - 已注释
                # showToast(
                #     "⚠️ 弹幕任务创建失败",
                #     f"直播间: {room_name}\n图像识别成功但弹幕任务创建失败\n请检查话术配置和系统状态",
                # )
                return False
        else:
            # 🔥 更新进度：图像识别失败，等待重试
            try:
                from apis import add_follow_progress_log, update_follow_progress_status
                add_follow_progress_log(f"🔍 图像识别失败，等待下次重试", "warning", 70, "等待重试")
                update_follow_progress_status(progress=70, step="等待图像识别重试")
            except:
                pass
            
            # 🔥 详细的图像识别失败分析
            follow_log_detailed("❌ 图像识别失败", "error", room_name, "识别结果")
            follow_log_detailed(f"🔍 匹配统计: {match_result['matched_count']}/{match_result['total_count']} 张图片", "error", room_name, "识别统计")
            
            # 显示技术细节
            if match_result.get("error"):
                follow_log_detailed(f"⚙️ 技术错误: {match_result['error']}", "error", room_name, "技术信息")
            
            # 显示尝试过的置信度级别
            if match_result.get("confidence_levels_tried"):
                levels = match_result["confidence_levels_tried"]
                follow_log_detailed(f"🎯 尝试的置信度级别: {levels}", "error", room_name, "技术信息")
            
            if match_result.get("confidence_used"):
                follow_log_detailed(f"🎯 最后使用置信度: {match_result['confidence_used']}", "error", room_name, "技术信息")
            
            if match_result.get("search_area"):
                follow_log_detailed(f"📐 搜索区域: {match_result['search_area']}", "error", room_name, "技术信息")
            
            # 显示检测的图片文件信息
            follow_log_detailed(f"📷 检测的图片数量: {match_result.get('total_count', 0)} 张", "error", room_name, "检测详情")

            # 🔥 业务层面的失败原因分析
            follow_log_detailed("📋 识别失败原因分析:", "error", room_name, "失败分析")
            follow_log_detailed("1️⃣ 当前直播间可能未在带货绑定的产品", "error", room_name, "失败分析")
            follow_log_detailed("2️⃣ 商品图片不在当前屏幕上显示", "error", room_name, "失败分析")
            follow_log_detailed("3️⃣ 直播间没有切换到正确的标签页", "error", room_name, "失败分析")
            follow_log_detailed("4️⃣ 图片被其他界面元素遮挡", "error", room_name, "失败分析")
            follow_log_detailed("5️⃣ 商品图片大小或角度发生变化", "error", room_name, "失败分析")
            follow_log_detailed("6️⃣ 图像识别置信度设置过高", "error", room_name, "失败分析")

            # 🔥 创建下次识别任务并显示时间 - 优化版本
            follow_log_detailed("⏰ 正在创建下次识别任务", "info", room_name, "任务创建")
            next_task_info = createNextRecognitionTask(room_id, room_name)

            if next_task_info:
                # 🔥 新增：同步到监听窗口的重试信息
                next_time_display = next_task_info['next_time'].split(' ')[1]  # 只显示时间部分
                sync_print(f"🔄 已创建重试任务，将在 {next_time_display} 重试", "warning", room_name, "重试安排")
                sync_print(f"⏱️ 重试间隔: {next_task_info['interval']}秒", "info", room_name, "重试配置")

                follow_log_detailed(f"✅ 下次识别时间: {next_task_info['next_time']}", "success", room_name, "任务创建")
                follow_log_detailed(f"🔄 重试间隔: {next_task_info['interval']}秒后自动执行", "info", room_name, "任务创建")
                follow_log_detailed(f"📝 任务ID: {next_task_info['task_id']}", "info", room_name, "任务创建")

                # 显示倒计时信息
                from datetime import datetime
                try:
                    next_datetime = datetime.strptime(next_task_info['next_time'], "%Y-%m-%d %H:%M:%S")
                    now = datetime.now()
                    time_diff = next_datetime - now
                    if time_diff.total_seconds() > 0:
                        minutes = int(time_diff.total_seconds() // 60)
                        seconds = int(time_diff.total_seconds() % 60)
                        follow_log_detailed(f"⏳ 距离下次重试还有: {minutes}分{seconds}秒", "info", room_name, "倒计时")
                        # 🔥 新增：同步倒计时到监听窗口
                        sync_print(f"⏳ 距离下次重试: {minutes}分{seconds}秒", "info", room_name, "倒计时")

                        # 🔥 新增：显示重试任务创建成功的Toast通知
                        showToast(
                            "🔄 重试任务已创建",
                            f"直播间: {room_name}\n⏰ 将在 {next_time_display} 重试图像识别\n⏳ 距离重试: {minutes}分{seconds}秒\n💡 请确保商品在直播画面中显示",
                            duration=5
                        )
                except:
                    pass

                # 🔥 重要：重试任务创建成功时，延迟关闭监听窗口（给用户时间看到重试信息）
                import threading
                import time

                def delayed_close_window():
                    time.sleep(3)  # 延迟3秒让用户看到重试信息
                    try:
                        from apis import API
                        api = API()
                        close_result = api.close_follow_progress_window(room_name)
                        if close_result["success"]:
                            sync_print(f"🔄 监听窗口已自动关闭", "warning", room_name, "窗口管理")
                        else:
                            sync_print(f"⚠️ 监听窗口关闭失败: {close_result['message']}", "warning", room_name, "窗口管理")
                    except Exception as close_e:
                        sync_print(f"⚠️ 关闭监听窗口异常: {str(close_e)}", "warning", room_name, "窗口管理")

                # 在后台线程中延迟关闭窗口
                threading.Thread(target=delayed_close_window, daemon=True).start()
            else:
                # 🔥 新增：重试任务创建失败的提示
                sync_print(f"❌ 重试任务创建失败，请手动重新启动跟播", "error", room_name, "重试失败")
                follow_log_detailed("❌ 下次识别任务创建失败", "error", room_name, "任务创建")

                # 🔥 显示重试任务创建失败的Toast通知
                showToast(
                    "❌ 重试任务创建失败",
                    f"直播间: {room_name}\n无法创建重试识别任务\n请手动重新启动跟播\n检查任务管理器状态",
                    duration=5
                )

                # 🔥 新增：跟播失败且无法创建重试任务时立即关闭监听窗口
                try:
                    from apis import API
                    api = API()
                    close_result = api.close_follow_progress_window(room_name)
                    if close_result["success"]:
                        sync_print(f"🔄 监听窗口已自动关闭", "warning", room_name, "窗口管理")
                    else:
                        sync_print(f"⚠️ 监听窗口关闭失败: {close_result['message']}", "warning", room_name, "窗口管理")
                except Exception as close_e:
                    sync_print(f"⚠️ 关闭监听窗口异常: {str(close_e)}", "warning", room_name, "窗口管理")

                # 🔥 新增：关闭搜索标签
                try:
                    # 获取微信Chrome窗口
                    wechatChrome = getWxChromeWindowByIndex(0)
                    if wechatChrome:
                        # 关闭搜索标签
                        closeTabByTitle(wechatChrome, f"{room_name} - 搜一搜")
                        sync_print(f"🔄 搜索标签已自动关闭", "warning", room_name, "标签管理")
                    else:
                        sync_print(f"⚠️ 无法获取微信Chrome窗口，跳过关闭搜索标签", "warning", room_name, "标签管理")
                except Exception as tab_e:
                    sync_print(f"⚠️ 关闭搜索标签异常: {str(tab_e)}", "warning", room_name, "标签管理")

            # # 🔥 显示图像识别失败的Toast通知 - 已注释
            # showToast(
            #     "❌ 图像识别失败",
            #     f"直播间: {room_name}\n🚫 当前直播间可能未在带货绑定的产品\n🔄 已安排30秒后重试识别",
            # )

            return False

    except Exception as e:
        follow_log_detailed("执行异常", "error", room_name, "异常处理")
        follow_log_detailed(f"图像匹配和弹幕任务创建失败: {str(e)}", "error", room_name, "异常处理")
        import traceback
        follow_log_detailed("错误详情:", "error", room_name, "异常处理")
        follow_log_detailed(traceback.format_exc(), "error", room_name, "异常处理")
        return False


def getRoomProductImages(room_id):
    """
    获取直播间绑定的商品图片路径列表 - 增强调试版本

    Args:
        room_id: 直播间ID

    Returns:
        list: 图片路径列表
    """
    try:
        import sqlite3
        import os

        sync_print(f"🔍 查询直播间 {room_id} 的商品图片...", "info", operation="数据查询")

        conn = sqlite3.connect("system.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 首先检查直播间是否存在
        sync_print(f"检查直播间 {room_id} 是否存在...", "info", operation="数据验证")
        cursor.execute(
            "SELECT id, name, product_id FROM rooms WHERE id = ?", (room_id,)
        )
        room = cursor.fetchone()

        if not room:
            sync_print(f"❌ 直播间 {room_id} 不存在", "error", operation="数据验证")
            conn.close()
            return []

        sync_print(
            f"直播间信息: ID={room['id']}, 名称='{room['name']}', 商品ID={room['product_id']}", 
            "info", room['name'], "数据验证"
        )

        if not room["product_id"]:
            sync_print(f"⚠️ 直播间 '{room['name']}' 未绑定商品", "warning", room['name'], "数据验证")
            conn.close()
            return []

        # 检查商品是否存在
        sync_print(f"检查商品 {room['product_id']} 是否存在...", "info", room['name'], "商品验证")
        cursor.execute(
            "SELECT id, name FROM products WHERE id = ?", (room["product_id"],)
        )
        product = cursor.fetchone()

        if not product:
            sync_print(f"❌ 商品 {room['product_id']} 不存在", "error", room['name'], "商品验证")
            conn.close()
            return []

        sync_print(f"商品信息: ID={product['id']}, 名称='{product['name']}'", "info", room['name'], "商品验证")

        # 查询直播间绑定的商品图片
        sync_print(f"查询商品 {room['product_id']} 的图片...", "info", room['name'], "图片查询")
        query = """
            SELECT i.path, i.id, i.create_time, i.remark
            FROM rooms r
            JOIN products p ON r.product_id = p.id
            JOIN images i ON p.id = i.product_id
            WHERE r.id = ? AND r.product_id IS NOT NULL
            ORDER BY i.id ASC
        """

        cursor.execute(query, (room_id,))
        results = cursor.fetchall()
        conn.close()

        if not results:
            sync_print(f"⚠️ 商品 '{product['name']}' 没有绑定图片", "warning", room['name'], "图片查询")
            return []

        sync_print(f"查询到 {len(results)} 张图片记录", "success", room['name'], "图片查询")

        valid_image_data = []
        for i, row in enumerate(results, 1):
            image_path = row["path"]
            image_remark = row["remark"] or "无备注"
            image_id = row["id"]
            
            # 显示图片信息（包含备注）
            sync_print(f"检查第 {i} 张图片: {os.path.basename(image_path)}", "info", room['name'], "图片验证")
            sync_print(f"    📝 图片备注: {image_remark}", "info", room['name'], "图片信息")

            # 检查文件是否存在
            if os.path.exists(image_path):
                file_size = os.path.getsize(image_path)
                sync_print(f"    ✅ 文件存在，大小: {file_size} bytes", "success", room['name'], "图片验证")
                valid_image_data.append({
                    'path': image_path,
                    'remark': image_remark,
                    'id': image_id,
                    'filename': os.path.basename(image_path)
                })
            else:
                sync_print(f"    ❌ 文件不存在: {image_path}", "error", room['name'], "图片验证")

        sync_print(f"📷 最终有效图片: {len(valid_image_data)}/{len(results)} 张", "success", room['name'], "图片统计")
        if valid_image_data:
            for i, img_data in enumerate(valid_image_data, 1):
                sync_print(f"   {i}. {img_data['filename']} - {img_data['remark']}", "info", room['name'], "图片列表")

        # 为了兼容现有代码，返回路径列表，但同时存储完整信息
        return [img_data['path'] for img_data in valid_image_data]

    except Exception as e:
        sync_print(f"❌ 获取直播间商品图片失败: {str(e)}", "error", operation="图片查询")
        import traceback
        sync_print(f"错误详情: {traceback.format_exc()}", "error", operation="异常处理")
        return []


def createImageRecognitionTask(
    room_id=70, room_name=None, interval_seconds=None, test_mode=None
):
    """
    创建图像识别定时任务 - 支持直接测试

    Args:
        room_id: 直播间ID (默认70，用于测试)
        room_name: 直播间名称 (从数据库查询)
        interval_seconds: 间隔时间（秒），从配置文件读取
        test_mode: 是否为测试模式，从配置文件读取

    Returns:
        bool: 是否成功创建任务
    """
    try:
        # 🔥 如果没有提供room_name，从数据库查询真实名称
        if room_name is None:
            room_name = getRoomNameById(room_id)
            if not room_name:
                print(f"❌ [IMAGE_TASK] 直播间 {room_id} 不存在")
                return False

        # 🔥 如果没有提供间隔时间，从配置文件读取图像识别重试间隔
        if interval_seconds is None:
            interval_seconds = getImageRecognitionRetryInterval()

        # 🔥 如果没有提供测试模式，设为False（不再从配置文件读取）
        if test_mode is None:
            test_mode = False

        print(f"\n🚀 [IMAGE_TASK] 开始创建图像识别任务")
        print(f"📊 [IMAGE_TASK] 参数信息:")
        print(f"   - 直播间ID: {room_id}")
        print(f"   - 直播间名称: {room_name} (从数据库查询)")
        print(f"   - 检测间隔: {interval_seconds}秒")
        print(f"   - 测试模式: {test_mode}")

        from datetime import datetime, timedelta

        # 创建图像识别任务ID
        timestamp = int(datetime.now().timestamp())
        task_id = f"image_recognition_{room_id}_{timestamp}"
        print(f"🆔 [IMAGE_TASK] 生成任务ID: {task_id}")

        # 🔥 修复：不再立即执行图像识别，而是按配置文件设置延迟
        print(f"\n📅 [IMAGE_TASK] 按配置文件创建定时图像识别任务...")
        sync_print(f"📋 开始创建图像识别任务...", "info", room_name, "任务创建")
        
        # 从配置文件读取首次执行延迟时间
        config = loadConfig()
        system_config = config.get("system_config", {})
        intervals = system_config.get("intervals", {})
        start_delay = intervals.get('image_recognition_retry', interval_seconds)  # 使用图像识别间隔作为首次延迟
        first_run_time = datetime.now() + timedelta(seconds=start_delay)  # 配置的延迟后开始首次检测
        
        # 🔥 增强：向监听窗口输出更详细的配置信息
        sync_print(f"⚙️ 读取到系统配置信息:", "success", room_name, "配置读取")
        
        # 显示所有关键配置项
        bullet_interval = intervals.get('bullet_screen_send', 500)
        bullet_retry_interval = intervals.get('bullet_screen_retry', 10)
        follow_retry_interval = intervals.get('follow_task_retry', 60)
        
        sync_print(f"   📨 弹幕发送间隔: {bullet_interval}秒", "info", room_name, "配置详情")
        sync_print(f"   🔄 弹幕重试间隔: {bullet_retry_interval}秒", "info", room_name, "配置详情")
        sync_print(f"   🖼️ 图像识别间隔: {start_delay}秒", "info", room_name, "配置详情")
        sync_print(f"   🎯 跟播重试间隔: {follow_retry_interval}秒", "info", room_name, "配置详情")

        # 显示弹幕发送模式
        real_danmu_enabled = isRealDanmuSendEnabled()
        danmu_mode = "🎯 真实发送(OCR点击)" if real_danmu_enabled else "🧪 测试模式(回车键)"
        sync_print(f"   📤 弹幕发送模式: {danmu_mode}", "info", room_name, "配置详情")
        
        # 显示任务创建计划
        sync_print(f"📋 图像识别任务创建计划:", "info", room_name, "任务计划")
        sync_print(f"   ⏰ 首次执行时间: {first_run_time.strftime('%Y-%m-%d %H:%M:%S')}", "info", room_name, "执行时间")
        sync_print(f"   🔁 后续执行间隔: 每{start_delay}秒执行一次", "info", room_name, "执行间隔")
        
        # 显示任务模式
        mode_text = "🧪 测试模式" if test_mode else "🚀 生产模式"
        sync_print(f"   {mode_text}: 当前运行环境", "info", room_name, "运行模式")
        
        print(f"⏰ [IMAGE_TASK] 首次执行时间: {first_run_time.strftime('%H:%M:%S')}")

        # 使用任务管理器创建任务
        from task_manager import get_task_manager

        task_manager = get_task_manager()

        if not task_manager or not task_manager.is_running:
            print(f"❌ [IMAGE_TASK] 任务管理器未运行，无法创建图像识别任务")
            return False

        print(f"✅ [IMAGE_TASK] 任务管理器运行正常")
        
        # 🔥 增强：输出更详细的任务创建信息
        print(f"📊 [IMAGE_TASK] ===== 图像识别任务详细信息 =====")
        print(f"🏠 [IMAGE_TASK] 直播间: {room_name} (ID: {room_id})")
        print(f"🆔 [IMAGE_TASK] 任务ID: {task_id}")
        print(f"⚙️ [IMAGE_TASK] 运行模式: {'🧪 测试模式' if test_mode else '🚀 生产模式'}")
        print(f"⏱️ [IMAGE_TASK] 检测间隔: {interval_seconds}秒")
        print(f"🕐 [IMAGE_TASK] 当前时间: {datetime.now().strftime('%H:%M:%S')}")
        print(f"⏰ [IMAGE_TASK] 首次执行: {first_run_time.strftime('%H:%M:%S')}")
        print(f"⏳ [IMAGE_TASK] 延迟启动: {int((first_run_time - datetime.now()).total_seconds())}秒后开始")
        print(f"📊 [IMAGE_TASK] ========================================")

        # 创建图像识别任务备注
        mode_text = "开发测试" if test_mode else "生产环境"
        interval_text = (
            f"{interval_seconds}秒"
            if interval_seconds < 60
            else f"{interval_seconds//60}分钟"
        )

        remark = f"图像识别任务 - {mode_text}\n"
        remark += f"直播间: {room_name} (ID: {room_id})\n"
        remark += f"检测间隔: 每{interval_text}一次\n"
        remark += f"任务说明: 定时检测直播间内是否出现绑定的商品图片，匹配成功后自动创建弹幕发送任务"

        print(f"📝 [IMAGE_TASK] 任务备注创建完成")

        # 使用任务管理器的方法创建图像识别任务
        print(f"🔧 [IMAGE_TASK] 调用任务管理器创建定时任务...")
        current_time = datetime.now()
        time_diff = (first_run_time - current_time).total_seconds()
        
        print(f"🕐 [IMAGE_TASK] 当前时间: {current_time.strftime('%H:%M:%S')}")
        print(f"⏰ [IMAGE_TASK] 首次执行时间: {first_run_time.strftime('%H:%M:%S')}")
        print(f"⏳ [IMAGE_TASK] 延迟时间: {time_diff}秒")
        
        # 🔥 新增：向监听窗口输出任务创建详情
        sync_print(f"🕐 当前时间: {current_time.strftime('%H:%M:%S')}", "info", room_name, "时间信息")
        sync_print(f"⏰ 计划执行时间: {first_run_time.strftime('%H:%M:%S')}", "info", room_name, "时间信息")
        sync_print(f"⏳ 将在 {int(time_diff)} 秒后开始首次识别", "info", room_name, "时间信息")
        
        success = task_manager.add_image_recognition_task(
            task_id=task_id,
            room_id=room_id,
            room_name=room_name,
            run_time=first_run_time,
            interval_seconds=interval_seconds,
            remark=remark,
            test_mode=test_mode,
        )

        if success:
            print(f"✅ [IMAGE_TASK] 图像识别任务创建成功: {task_id}")
            print(f"🖼️ [IMAGE_TASK] 首次执行时间: {first_run_time.strftime('%H:%M:%S')}")
            print(f"⏰ [IMAGE_TASK] 检测间隔: 每{interval_text}一次")
            
            # 🔥 新增：同步到监听窗口的友好提示
            sync_print(f"✅ 图像识别任务创建成功", "success", room_name, "任务创建")
            sync_print(f"🖼️ 首次执行时间: {first_run_time.strftime('%Y-%m-%d %H:%M:%S')}", "info", room_name, "执行计划")
            sync_print(f"⏰ 检测间隔: 每{interval_text}执行一次", "info", room_name, "执行计划")
            sync_print(f"📋 任务ID: {task_id}", "info", room_name, "任务信息")
            
            return True
        else:
            print(f"❌ [IMAGE_TASK] 图像识别任务创建失败")
            return False

    except Exception as e:
        print(f"❌ [IMAGE_TASK] 创建图像识别任务失败: {str(e)}")
        import traceback

        print(f"🔍 [IMAGE_TASK] 错误详情: {traceback.format_exc()}")
        return False


def executeImageRecognitionTask(
    task_id, room_id, room_name, interval_seconds, test_mode, db_path
):
    """
    执行图像识别任务的全局函数

    Args:
        task_id: 任务ID
        room_id: 直播间ID
        room_name: 直播间名称
        interval_seconds: 间隔时间（秒）
        test_mode: 是否为测试模式
        db_path: 数据库路径
    """
    try:
        from datetime import datetime, timedelta

        # 🔥 详细的日志输出 - 任务启动
        follow_log_detailed(f"执行图像识别任务: {task_id}", "info", room_name, "任务启动")
        follow_log_detailed(f"直播间: {room_name} (ID: {room_id})", "info", room_name, "任务启动")
        follow_log_detailed(f"间隔时间: {interval_seconds}秒, 测试模式: {test_mode}", "info", room_name, "任务启动")

        # 检查任务状态
        from task_manager import check_task_status, mark_task_as_executed, add_task_log

        follow_log_detailed("检查任务状态...", "info", room_name, "状态检查")
        if not check_task_status(task_id, db_path):
            follow_log_detailed(f"任务 {task_id} 状态已失效或已执行，跳过执行", "warning", room_name, "状态检查")
            add_task_log(
                task_id,
                2,
                f"图像识别任务状态已失效，跳过执行 - 直播间: {room_name}",
                room_id,
                room_name,
                db_path,
            )
            return

        # 标记任务为已执行
        follow_log_detailed("标记任务为已执行", "info", room_name, "状态更新")
        mark_task_as_executed(task_id, db_path)

        # 获取并激活直播间的Chrome窗口
        follow_log_detailed("获取微信Chrome窗口...", "info", room_name, "窗口获取")
        chrome_view = getWxChromeWindowByIndex(0)
        if not chrome_view:
            error_msg = "微信Chrome窗口未找到，无法执行图像识别"
            follow_log_detailed(error_msg, "error", room_name, "窗口获取")
            add_task_log(task_id, 2, error_msg, room_id, room_name, db_path)
            return

        # 🔥 重要：激活微信Chrome窗口
        try:
            follow_log_detailed("激活微信Chrome窗口进行图像识别...", "info", room_name, "窗口激活")
            chrome_view.SetActive()
            follow_log_detailed("微信Chrome窗口已激活", "success", room_name, "窗口激活")

            # 等待窗口激活完成
            import time
            time.sleep(1)
            follow_log_detailed("窗口激活等待完成", "info", room_name, "窗口激活")

        except Exception as activate_error:
            error_msg = f"激活微信Chrome窗口失败: {str(activate_error)}"
            follow_log_detailed(error_msg, "warning", room_name, "窗口激活")
            # 窗口激活失败不应该中断识别，继续尝试

        # 执行图像匹配
        follow_log_detailed("开始执行图像匹配...", "info", room_name, "图像匹配")
        match_success = performImageMatchingAndCreateDanmuTask(
            room_id=room_id, room_name=room_name, chrome_view=chrome_view
        )

        if match_success:
            # 匹配成功，停止继续创建识别任务
            success_msg = f"图像识别成功，已创建弹幕任务，停止继续识别"
            follow_log_detailed(success_msg, "success", room_name, "识别成功")
            add_task_log(task_id, 1, success_msg, room_id, room_name, db_path)
        else:
            # 匹配失败，创建下一次识别任务
            failure_msg = f"图像识别未找到匹配图片，将在{interval_seconds}秒后重试"
            follow_log_detailed(failure_msg, "warning", room_name, "识别失败")
            add_task_log(task_id, 2, failure_msg, room_id, room_name, db_path)

            # 创建下一次识别任务
            follow_log_detailed(f"创建下次识别任务，{interval_seconds}秒后执行", "info", room_name, "任务创建")
            next_run_time = datetime.now() + timedelta(seconds=interval_seconds)
            next_task_id = (
                f"image_recognition_{room_id}_{int(next_run_time.timestamp())}"
            )

            from task_manager import get_task_manager

            task_manager = get_task_manager()

            if task_manager and task_manager.is_running:
                # 创建下一次识别任务的备注
                mode_text = "开发测试" if test_mode else "生产环境"
                interval_text = (
                    f"{interval_seconds}秒"
                    if interval_seconds < 60
                    else f"{interval_seconds//60}分钟"
                )

                next_remark = f"图像识别重试任务 - {mode_text}\n"
                next_remark += f"直播间: {room_name} (ID: {room_id})\n"
                next_remark += f"检测间隔: 每{interval_text}一次\n"
                next_remark += f"上次结果: 未找到匹配图片\n"
                next_remark += f"任务说明: 继续检测直播间内是否出现绑定的商品图片"

                success = task_manager.add_image_recognition_task(
                    task_id=next_task_id,
                    room_id=room_id,
                    room_name=room_name,
                    run_time=next_run_time,
                    interval_seconds=interval_seconds,
                    remark=next_remark,
                    test_mode=test_mode,
                )

                if success:
                    print(f"✅ 已创建下一次识别任务: {next_task_id}")
                    print(f"⏰ 执行时间: {next_run_time.strftime('%H:%M:%S')}")
                    
                    # 🔥 显示重试任务创建成功的Toast通知
                    from follwRoom import showToast
                    showToast(
                        "🔄 创建重试任务",
                        f"直播间: {room_name}\n⏰ 将在 {interval_text} 后重试图像识别\n📅 下次执行: {next_run_time.strftime('%H:%M:%S')}\n💡 请确保商品在直播画面中显示",
                    )
                else:
                    print(f"❌ 创建下一次识别任务失败")
                    
                    # 🔥 显示重试任务创建失败的Toast通知
                    from follwRoom import showToast
                    showToast(
                        "❌ 重试任务创建失败",
                        f"直播间: {room_name}\n无法创建重试识别任务\n请检查任务管理器状态",
                    )
            else:
                print(f"❌ 任务管理器不可用，无法创建下一次识别任务")
                
                # 🔥 显示任务管理器不可用的Toast通知
                from follwRoom import showToast
                showToast(
                    "⚠️ 任务管理器不可用",
                    f"直播间: {room_name}\n任务管理器未运行或不可用\n无法创建重试识别任务",
                )

        print(f"✅ 图像识别任务执行完成: {task_id}")

    except Exception as e:
        error_msg = f"图像识别任务执行异常: {str(e)}"
        print(f"❌ {error_msg}")
        from task_manager import add_task_log

        add_task_log(task_id, 2, error_msg, room_id, room_name, db_path)


if __name__ == "__main__":
    print("🧪 开始测试环境 - follwRoom.py 直接启动")

    # 🔥 重要：测试环境下启动TaskManager
    print("\n🚀 启动TaskManager（测试环境）...")
    try:
        from task_manager import get_task_manager, init_task_manager

        # 初始化TaskManager
        if init_task_manager():
            print("✅ TaskManager 初始化成功")

            # 获取并启动TaskManager
            task_manager = get_task_manager()
            if task_manager and not task_manager.is_running:
                task_manager.start()
                print("✅ TaskManager 已启动")
            else:
                print("✅ TaskManager 已在运行")

            print(
                f"📊 TaskManager 状态: {task_manager.is_running if task_manager else False}"
            )
        else:
            print("❌ TaskManager 初始化失败")
    except Exception as e:
        print(f"❌ TaskManager 启动失败: {str(e)}")

    # 测试图像识别功能
    print("\n🧪 开始测试图像识别功能...")

    # 方式1: 直接测试图像识别任务创建
    print("\n📋 方式1: 直接测试图像识别")
    createImageRecognitionTask()

    # 🔥 阻塞主线程，确保所有弹幕任务都能执行完成
    print("\n⏰ 等待弹幕任务执行完成...")
    print("💡 提示: 按 Ctrl+C 可提前结束程序")

    try:
        import time
        import sqlite3

        # 持续检查是否还有待执行的弹幕任务
        while True:
            try:
                # 查询待执行的弹幕任务数量
                conn = sqlite3.connect("system.db")
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM tasks WHERE task_type = 'danmu_task' AND status = 0"
                )
                pending_count = cursor.fetchone()[0]
                conn.close()

                if pending_count > 0:
                    print(f"🔄 还有 {pending_count} 个弹幕任务待执行，继续等待...")
                    intervals = getIntervalConfig()
                    time.sleep(intervals["live_room_check"] // 30)  # 使用配置的检查间隔（除以30使其更快）
                else:
                    print("✅ 所有弹幕任务已执行完成")
                    break

            except KeyboardInterrupt:
                print("\n🛑 用户手动停止程序")
                break
            except Exception as e:
                print(f"⚠️ 检查任务状态异常: {str(e)}")
                time.sleep(5)

    except KeyboardInterrupt:
        print("\n🛑 程序被用户停止")

    print("\n🎉 测试环境结束")

    # 方式2: 完整流程测试（需要手动打开直播间）
    # print("\n📋 方式2: 完整流程测试")
    # initEnterRoom(getWechat(), roomName="参半牙膏工厂店", room_id=70)
