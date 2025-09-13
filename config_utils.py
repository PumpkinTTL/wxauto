"""
配置工具模块
提供统一的配置读取接口，避免硬编码
"""

import json
import os
from typing import Any, Dict, Optional

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self._config_cache = None
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config_cache = json.load(f)
            else:
                self._config_cache = self._get_default_config()
                print(f"⚠️ 配置文件不存在，使用默认配置: {self.config_path}")
        except Exception as e:
            print(f"❌ 加载配置失败: {e}")
            self._config_cache = self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "system_config": {
                "intervals": {
                    "bullet_screen_send": 500,
                    "bullet_screen_retry": 30,
                    "follow_task_retry": 60,
                    "image_recognition_retry": 60,
                    "live_room_check": 300,
                    "page_load_wait": 2,
                    "window_switch_wait": 1,
                    "operation_wait": 1,
                    "network_timeout": 30,
                    "tab_switch_wait": 1,
                    "element_wait": 0.5,
                    "chrome_load_wait": 3,
                    "wechat_operation_wait": 2,
                    "screenshot_wait": 1,
                    "element_click_wait": 0.5
                },
                "retry_config": {
                    "max_bullet_retry": 5,
                    "max_image_retry": 5,
                    "max_follow_retry": 10,
                    "enable_auto_retry": True,
                    "max_network_retry": 3,
                    "max_element_retry": 3
                },
                "features": {
                    "enable_screenshot": True,
                    "enable_notifications": False,
                    "enable_detailed_logs": True,
                    "enable_auto_scroll": True,
                    "enable_error_recovery": True,
                    "enable_performance_monitoring": False,
                    "enable_real_danmu_send": False
                },
                "quality": {
                    "screenshot_quality": 80,
                    "image_match_confidence": 0.8,
                    "log_level": "info",
                    "max_log_file_size": 10,
                    "max_log_files": 5
                },
                "timeouts": {
                    "element_timeout": 10,
                    "page_timeout": 30,
                    "network_timeout": 60,
                    "task_timeout": 300,
                    "screenshot_timeout": 5
                }
            },
            "ui_config": {
                "theme": "default",
                "auto_scroll": True,
                "show_notifications": True,
                "animation_enabled": True,
                "refresh_interval": 5,
                "max_display_logs": 1000
            },
            "wechat_config": {
                "chrome_profile_path": "chrome_profile_tmall",
                "window_title_pattern": "微信",
                "max_retry_attempts": 3,
                "element_detection_timeout": 5,
                "scroll_speed": 3,
                "click_delay": 0.5
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        try:
            keys = key.split('.')
            value = self._config_cache
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
        except Exception:
            return default
    
    def get_interval(self, interval_name: str) -> int:
        """获取时间间隔配置"""
        return self.get(f"system_config.intervals.{interval_name}", 30)
    
    def get_feature(self, feature_name: str) -> bool:
        """获取功能开关配置"""
        return self.get(f"system_config.features.{feature_name}", True)
    
    def get_retry_config(self, retry_name: str) -> Any:
        """获取重试配置"""
        return self.get(f"system_config.retry_config.{retry_name}")
    
    def get_timeout(self, timeout_name: str) -> int:
        """获取超时配置"""
        return self.get(f"system_config.timeouts.{timeout_name}", 30)
    
    def reload(self):
        """重新加载配置"""
        self._load_config()

# 全局配置管理器实例
config_manager = ConfigManager()

# 便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return config_manager.get(key, default)

def get_interval(interval_name: str) -> int:
    """获取时间间隔配置（秒）"""
    return config_manager.get_interval(interval_name)

def get_feature(feature_name: str) -> bool:
    """获取功能开关配置"""
    return config_manager.get_feature(feature_name)

def get_retry_config(retry_name: str) -> Any:
    """获取重试配置"""
    return config_manager.get_retry_config(retry_name)

def get_timeout(timeout_name: str) -> int:
    """获取超时配置（秒）"""
    return config_manager.get_timeout(timeout_name)

def reload_config():
    """重新加载配置"""
    config_manager.reload()

# 常用配置的快捷访问函数
def get_bullet_interval() -> int:
    """获取弹幕发送间隔"""
    return get_interval('bullet_screen_send')

def get_page_load_wait() -> int:
    """获取页面加载等待时间"""
    return get_interval('page_load_wait')

def get_window_switch_wait() -> int:
    """获取窗口切换等待时间"""
    return get_interval('window_switch_wait')

def get_operation_wait() -> int:
    """获取操作等待时间"""
    return get_interval('operation_wait')

def get_element_wait() -> float:
    """获取元素等待时间"""
    return get_interval('element_wait')

def is_screenshot_enabled() -> bool:
    """是否启用截图"""
    return get_feature('enable_screenshot')

def is_notifications_enabled() -> bool:
    """是否启用通知"""
    return get_feature('enable_notifications')

def is_detailed_logs_enabled() -> bool:
    """是否启用详细日志"""
    return get_feature('enable_detailed_logs')

def is_real_danmu_send_enabled() -> bool:
    """是否启用真实发送弹幕（OCR点击发送按钮）"""
    return get_feature('enable_real_danmu_send')

if __name__ == "__main__":
    # 测试配置读取
    print("=== 配置测试 ===")
    print(f"弹幕间隔: {get_bullet_interval()}秒")
    print(f"页面加载等待: {get_page_load_wait()}秒")
    print(f"截图功能: {'启用' if is_screenshot_enabled() else '禁用'}")
    print(f"详细日志: {'启用' if is_detailed_logs_enabled() else '禁用'}")