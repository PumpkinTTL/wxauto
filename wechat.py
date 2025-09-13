#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

微信自动化工具
功能：自动加好友、自动回复、日志记录
基于wxauto库实现
"""

import os
import sys
import time
import json
import random
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import threading

try:
    import wxauto
    from wxauto import WeChat
except ImportError as e:
    print(f"❌ wxauto库导入失败: {e}")
    print("请安装: pip install wxauto")
    sys.exit(1)


class WeChatLogger:
    """微信日志记录器"""

    def __init__(self, log_dir: str = "wxauto_logs"):
        """初始化日志记录器"""
        self.log_dir = log_dir
        self.setup_logger()

    def setup_logger(self):
        """设置日志记录器"""
        # 创建日志目录
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # 创建日志文件名（按日期）
        today = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(self.log_dir, f"app_{today}.log")

        # 配置日志格式
        log_format = "%(asctime)s [%(name)s] [%(levelname)s] [%(filename)s:%(lineno)d]  %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"

        # 配置日志记录器
        logging.basicConfig(
            level=logging.DEBUG,
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info("微信自动化工具日志系统初始化完成")


class WeChatAutoFriend:
    """微信自动加好友功能"""

    def __init__(self, logger: logging.Logger):
        """初始化微信自动加好友"""
        self.logger = logger
        self.wx = None
        self.friends_data_file = "friends_data.json"
        self.default_friends_data = [
               {
                "search_key": "BitleSuper",
                "verify_msg": "看到您在XX群的专业分享，希望能向您请教",
                "remark": "专业人士003",
                "tags": ["专业", "学习"]
            },
            {
                "search_key": "user001",
                "verify_msg": "您好！我是XX公司的客服，方便通过好友申请交流下项目吗？",
                "remark": "客户001",
                "tags": ["客户", "潜在合作"]
            },
            {
                "search_key": "user002",
                "verify_msg": "朋友介绍认识，想和您沟通下行业动态，麻烦通过下~",
                "remark": "行业联系人002",
                "tags": ["行业", "交流"]
            },
         
        ]

    def init_wechat(self) -> bool:
        """初始化微信客户端"""
        try:
            self.wx = WeChat()
            self.logger.info("微信客户端初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"微信客户端初始化失败: {e}")
            return False

    def check_wechat_status(self) -> bool:
        """检查微信状态"""
        try:
            if not self.wx:
                self.logger.error("微信客户端未初始化")
                return False

            self.logger.info("微信窗口检测成功")

            # 尝试获取用户信息
            try:
                if hasattr(self.wx, 'nickname'):
                    username = self.wx.nickname
                    self.logger.info(f"当前微信账号: {username}")
                elif hasattr(self.wx, 'CurrentUserName'):
                    username = self.wx.CurrentUserName()
                    self.logger.info(f"当前微信账号: {username}")
                else:
                    self.logger.info("微信客户端已连接")
            except Exception as e:
                self.logger.warning(f"获取用户信息失败: {e}")

            # 尝试获取会话信息
            try:
                if hasattr(self.wx, 'GetSessionList'):
                    sessions = self.wx.GetSessionList()
                    self.logger.info(f"微信状态正常，当前有 {len(sessions)} 个会话")
                else:
                    self.logger.info("微信状态正常（基础模式）")
            except Exception as e:
                self.logger.warning(f"获取会话信息失败: {e}")
                self.logger.info("微信状态正常（基础模式）")

            return True

        except Exception as e:
            self.logger.error(f"检查微信状态失败: {e}")
            return False

    def load_friends_data(self) -> List[Dict]:
        """加载好友数据"""
        try:
            if os.path.exists(self.friends_data_file):
                with open(self.friends_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.logger.info(f"成功加载 {len(data)} 个好友数据")
                    return data
            else:
                self.logger.warning(f"文件 {self.friends_data_file} 不存在，使用默认数据")
                return self.default_friends_data
        except Exception as e:
            self.logger.error(f"加载好友数据失败: {e}")
            return self.default_friends_data

    def save_friends_data(self, data: List[Dict]):
        """保存好友数据"""
        try:
            with open(self.friends_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"成功保存 {len(data)} 个好友数据")
        except Exception as e:
            self.logger.error(f"保存好友数据失败: {e}")

    def add_single_friend(self, friend_info: Dict) -> bool:
        """添加单个好友"""
        try:
            search_key = friend_info.get("search_key", "")
            verify_msg = friend_info.get("verify_msg", "")
            remark = friend_info.get("remark", "")
            tags = friend_info.get("tags", [])

            self.logger.info(f"开始添加好友: {search_key}")

            # 检查是否支持Plus版本的高级功能
            if hasattr(self.wx, 'AddNewFriend'):
                self.logger.info("使用Plus版本的AddNewFriend方法")
                try:
                    # 使用Plus版本的高级API添加好友
                    result = self.wx.AddNewFriend(
                        keywords=search_key,
                        addmsg=verify_msg,
                        remark=remark,
                        tags=tags,
                        permission="朋友圈",
                        timeout=10
                    )

                    # 检查返回结果
                    if hasattr(result, 'success') and result.success:
                        self.logger.info(f"✅ 成功添加好友: {search_key}")
                        return True
                    else:
                        self.logger.warning(f"⚠️ 添加好友失败: {search_key} - {result}")
                        return False

                except Exception as e:
                    self.logger.error(f"Plus版本AddNewFriend调用失败: {e}")
                    return False
            else:
                # 开源版本的处理方式
                self.logger.warning("当前使用开源版本wxauto，不支持自动添加好友功能")
                self.logger.info("💡 建议升级到Plus版本(wxautox)以获得完整的自动添加好友功能")
                self.logger.info("   安装命令: pip install wxautox")
                self.logger.info("")
                self.logger.info("📋 需要添加的好友信息:")
                self.logger.info(f"   🔍 搜索关键词: {search_key}")
                self.logger.info(f"   💬 验证消息: {verify_msg}")
                if remark:
                    self.logger.info(f"   🏷️ 建议备注: {remark}")
                if tags:
                    self.logger.info(f"   🔖 建议标签: {', '.join(tags)}")

                self.logger.info("")
                self.logger.info("🔧 当前版本处理方式:")

                # 尝试切换到该用户的聊天窗口（检查是否已经是好友）
                try:
                    self.wx.ChatWith(search_key)
                    self.logger.info(f"✅ {search_key} 已经是好友，可以直接聊天")
                    return True
                except Exception as e:
                    self.logger.info(f"⚠️ {search_key} 不是好友或无法找到")
                    self.logger.info("   请手动在微信中搜索并添加该好友")
                    return False

        except Exception as e:
            self.logger.error(f"添加好友异常: {e}")
            return False

    def batch_add_friends(self, mode: str = "auto") -> Dict:
        """批量添加好友

        Args:
            mode: 添加模式 ("auto": 自动检测, "manual": 手动指导, "ui": UI自动化)
        """
        friends_data = self.load_friends_data()
        total_count = len(friends_data)
        success_count = 0
        failed_count = 0
        skipped_count = 0

        self.logger.info(f"开始批量处理 {total_count} 个好友...")

        if mode == "manual":
            self.logger.info("使用手动指导模式")
        elif mode == "ui":
            self.logger.info("使用UI自动化模式")
        else:
            self.logger.info("使用自动检测模式")

        for i, friend_info in enumerate(friends_data, 1):
            self.logger.info(f"\n[{i}/{total_count}] 处理: {friend_info.get('search_key', 'Unknown')}")

            if mode == "manual":
                # 手动指导模式：只显示信息，等待用户手动操作
                input(f"请手动添加好友: {friend_info.get('search_key')} (按回车继续下一个)")
                success_count += 1
            else:
                # 自动模式
                result = self.add_single_friend(friend_info)
                if result:
                    success_count += 1
                else:
                    failed_count += 1

                # 安全等待，避免操作过快
                wait_time = random.uniform(5, 20)
                self.logger.info(f"⏱️ 等待 {wait_time:.1f} 秒...")
                time.sleep(wait_time)

        # 返回统计结果
        return {
            "total": total_count,
            "success": success_count,
            "failed": failed_count,
            "skipped": skipped_count
        }


class WeChatAutoReply:
    """微信自动回复功能"""

    def __init__(self, logger: logging.Logger):
        """初始化微信自动回复"""
        self.logger = logger
        self.wx = None
        self.reply_rules_file = "reply_rules.json"
        self.is_running = False
        self.monitor_thread = None
        self.default_reply_rules = {
            "keywords": {
                "你好": ["您好！很高兴为您服务", "您好，请问有什么可以帮助您的吗？"],
                "价格": ["关于价格问题，我们有多种套餐可选，请问您具体需要了解哪方面？"],
                "产品": ["我们的产品功能丰富，请问您想了解哪个具体功能？"],
                "服务": ["我们提供7*24小时专业服务，有任何问题随时联系我们"],
                "谢谢": ["不客气，很高兴能帮到您！", "您太客气了，这是我们应该做的"]
            },
            "default_replies": [
                "感谢您的消息，我会尽快回复您",
                "收到您的消息了，稍后详细回复",
                "您好，我正在处理其他事务，稍后回复您"
            ],
            "auto_reply_enabled": True,
            "reply_delay_min": 3,
            "reply_delay_max": 10,
            "exclude_groups": True,  # 是否排除群聊
            "exclude_keywords": ["不用回复", "别回复", "自动回复"]  # 包含这些关键词的消息不自动回复
        }

    def init_wechat(self, wx_instance=None) -> bool:
        """初始化微信客户端"""
        try:
            if wx_instance:
                self.wx = wx_instance
            else:
                self.wx = WeChat()
            self.logger.info("自动回复模块微信客户端初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"自动回复模块微信客户端初始化失败: {e}")
            return False

    def load_reply_rules(self) -> Dict:
        """加载回复规则"""
        try:
            if os.path.exists(self.reply_rules_file):
                with open(self.reply_rules_file, 'r', encoding='utf-8') as f:
                    rules = json.load(f)
                    self.logger.info("成功加载自定义回复规则")
                    return rules
            else:
                self.logger.info("使用默认回复规则")
                self.save_reply_rules(self.default_reply_rules)
                return self.default_reply_rules
        except Exception as e:
            self.logger.error(f"加载回复规则失败: {e}")
            return self.default_reply_rules

    def save_reply_rules(self, rules: Dict):
        """保存回复规则"""
        try:
            with open(self.reply_rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)
            self.logger.info("回复规则保存成功")
        except Exception as e:
            self.logger.error(f"保存回复规则失败: {e}")

    def get_reply_message(self, received_msg: str, rules: Dict) -> Optional[str]:
        """根据接收到的消息获取回复内容"""
        try:
            # 检查是否包含排除关键词
            exclude_keywords = rules.get("exclude_keywords", [])
            for keyword in exclude_keywords:
                if keyword in received_msg:
                    self.logger.info(f"消息包含排除关键词 '{keyword}'，不自动回复")
                    return None

            # 检查关键词匹配
            keywords = rules.get("keywords", {})
            for keyword, replies in keywords.items():
                if keyword in received_msg:
                    reply = random.choice(replies)
                    self.logger.info(f"匹配关键词 '{keyword}'，回复: {reply}")
                    return reply

            # 使用默认回复
            default_replies = rules.get("default_replies", [])
            if default_replies:
                reply = random.choice(default_replies)
                self.logger.info(f"使用默认回复: {reply}")
                return reply

            return None

        except Exception as e:
            self.logger.error(f"获取回复消息失败: {e}")
            return None

    def send_reply(self, contact_name: str, reply_msg: str, rules: Dict) -> bool:
        """发送回复消息"""
        try:
            if not self.wx:
                self.logger.error("微信客户端未初始化")
                return False

            # 添加延迟，模拟人工回复
            delay_min = rules.get("reply_delay_min", 3)
            delay_max = rules.get("reply_delay_max", 10)
            delay = random.uniform(delay_min, delay_max)

            self.logger.info(f"等待 {delay:.1f} 秒后回复...")
            time.sleep(delay)

            # 发送消息
            self.wx.ChatWith(contact_name)
            self.wx.SendMsg(reply_msg)

            self.logger.info(f"✅ 已向 {contact_name} 发送回复: {reply_msg}")
            return True

        except Exception as e:
            self.logger.error(f"发送回复失败: {e}")
            return False

    def monitor_messages(self):
        """监控新消息"""
        rules = self.load_reply_rules()

        if not rules.get("auto_reply_enabled", True):
            self.logger.info("自动回复功能已禁用")
            return

        self.logger.info("开始监控新消息...")
        self.logger.info("注意：当前版本使用简化的消息监控模式")
        last_messages = {}

        while self.is_running:
            try:
                if not self.wx:
                    break

                # 使用GetNewMessage方法获取新消息
                try:
                    new_messages = self.wx.GetNewMessage()
                    if new_messages:
                        for msg in new_messages:
                            try:
                                msg_content = msg.get('content', '') if isinstance(msg, dict) else str(msg)
                                msg_type = msg.get('type', 'text') if isinstance(msg, dict) else 'text'
                                sender = msg.get('sender', 'Unknown') if isinstance(msg, dict) else 'Unknown'

                                # 只处理文本消息
                                if msg_type == 'text' and msg_content and msg_content.strip():
                                    # 跳过群聊（如果设置了排除群聊）
                                    if rules.get("exclude_groups", True) and self.is_group_chat(sender):
                                        continue

                                    # 检查是否是新消息
                                    msg_key = f"{sender}_{msg_content}_{msg.get('time', time.time())}"
                                    if msg_key not in last_messages:
                                        last_messages[msg_key] = True

                                        self.logger.info(f"收到来自 {sender} 的新消息: {msg_content}")

                                        # 获取回复内容
                                        reply_msg = self.get_reply_message(msg_content, rules)
                                        if reply_msg:
                                            # 发送回复
                                            self.send_reply(sender, reply_msg, rules)

                            except Exception as e:
                                self.logger.error(f"处理单条消息时出错: {e}")
                                continue

                except AttributeError:
                    # 如果GetNewMessage也不支持，使用更基础的方法
                    self.logger.warning("当前wxauto版本不支持GetNewMessage，使用基础监控模式")
                    # 可以在这里添加其他监控逻辑，比如定期检查特定联系人
                    pass
                except Exception as e:
                    self.logger.error(f"获取新消息失败: {e}")

                # 短暂休息
                time.sleep(3)

            except Exception as e:
                self.logger.error(f"监控消息时出错: {e}")
                time.sleep(5)

        self.logger.info("消息监控已停止")

    def is_group_chat(self, contact_name: str) -> bool:
        """判断是否为群聊"""
        # 简单的群聊判断逻辑，可以根据实际情况调整
        group_indicators = ['群', 'Group', '讨论组', '工作群', '家庭群']
        return any(indicator in contact_name for indicator in group_indicators)

    def start_auto_reply(self):
        """启动自动回复"""
        if self.is_running:
            self.logger.warning("自动回复已在运行中")
            return

        self.is_running = True
        self.monitor_thread = threading.Thread(target=self.monitor_messages, daemon=True)
        self.monitor_thread.start()
        self.logger.info("自动回复功能已启动")
        self.logger.info("注意：当前版本的自动回复功能有限，建议使用手动回复模式")

    def stop_auto_reply(self):
        """停止自动回复"""
        self.is_running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        self.logger.info("自动回复功能已停止")

    def manual_reply_mode(self):
        """手动回复模式 - 针对当前wxauto版本的替代方案"""
        rules = self.load_reply_rules()
        self.logger.info("="*50)
        self.logger.info("手动回复模式启动")
        self.logger.info("="*50)
        self.logger.info("使用说明:")
        self.logger.info("1. 输入联系人名称")
        self.logger.info("2. 输入收到的消息内容")
        self.logger.info("3. 系统会推荐回复内容")
        self.logger.info("4. 输入 'quit' 退出")
        self.logger.info("="*50)

        while True:
            try:
                contact_name = input("\n请输入联系人名称 (或输入 'quit' 退出): ").strip()
                if contact_name.lower() == 'quit':
                    break

                if not contact_name:
                    print("联系人名称不能为空")
                    continue

                received_msg = input("请输入收到的消息内容: ").strip()
                if not received_msg:
                    print("消息内容不能为空")
                    continue

                # 获取推荐回复
                reply_msg = self.get_reply_message(received_msg, rules)

                if reply_msg:
                    print(f"\n推荐回复: {reply_msg}")

                    send_choice = input("是否发送此回复? (y/n): ").strip().lower()
                    if send_choice == 'y':
                        try:
                            self.wx.ChatWith(contact_name)
                            time.sleep(1)  # 等待窗口切换
                            self.wx.SendMsg(reply_msg)
                            self.logger.info(f"✅ 已向 {contact_name} 发送: {reply_msg}")
                        except Exception as e:
                            self.logger.error(f"发送消息失败: {e}")
                    else:
                        custom_reply = input("请输入自定义回复 (留空跳过): ").strip()
                        if custom_reply:
                            try:
                                self.wx.ChatWith(contact_name)
                                time.sleep(1)
                                self.wx.SendMsg(custom_reply)
                                self.logger.info(f"✅ 已向 {contact_name} 发送: {custom_reply}")
                            except Exception as e:
                                self.logger.error(f"发送消息失败: {e}")
                else:
                    print("未找到匹配的回复规则")
                    custom_reply = input("请输入自定义回复 (留空跳过): ").strip()
                    if custom_reply:
                        try:
                            self.wx.ChatWith(contact_name)
                            time.sleep(1)
                            self.wx.SendMsg(custom_reply)
                            self.logger.info(f"✅ 已向 {contact_name} 发送: {custom_reply}")
                        except Exception as e:
                            self.logger.error(f"发送消息失败: {e}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"手动回复模式出错: {e}")

        self.logger.info("手动回复模式已退出")


class WeChatAutomation:
    """微信自动化主控制类"""

    def __init__(self):
        """初始化微信自动化工具"""
        # 初始化日志
        self.logger_manager = WeChatLogger()
        self.logger = self.logger_manager.logger

        # 初始化各功能模块
        self.auto_friend = WeChatAutoFriend(self.logger)
        self.auto_reply = WeChatAutoReply(self.logger)

        # 微信客户端实例
        self.wx = None

        # 检测wxauto版本
        self.wxauto_version = self.detect_wxauto_version()

    def detect_wxauto_version(self) -> str:
        """检测wxauto版本"""
        try:
            import wxauto

            # 检查是否是Plus版本
            try:
                # 尝试导入Plus版本特有的模块或检查特有方法
                wx_temp = wxauto.WeChat()
                if hasattr(wx_temp, 'AddNewFriend'):
                    return "Plus版本 (wxautox)"
                else:
                    return "开源版本 (wxauto)"
            except:
                return "开源版本 (wxauto)"

        except ImportError:
            return "未安装"

    def init_wechat(self) -> bool:
        """初始化微信客户端"""
        try:
            # 初始化主微信客户端
            if not self.auto_friend.init_wechat():
                return False

            self.wx = self.auto_friend.wx

            # 共享微信客户端实例给自动回复模块
            self.auto_reply.init_wechat(self.wx)

            # 检查微信状态
            return self.auto_friend.check_wechat_status()

        except Exception as e:
            self.logger.error(f"初始化微信客户端失败: {e}")
            return False

    def batch_add_friends(self, mode: str = "auto") -> Dict:
        """批量添加好友"""
        return self.auto_friend.batch_add_friends(mode)

    def start_auto_reply(self):
        """启动自动回复"""
        self.auto_reply.start_auto_reply()

    def stop_auto_reply(self):
        """停止自动回复"""
        self.auto_reply.stop_auto_reply()

    def get_session_info(self) -> Dict:
        """获取会话信息"""
        try:
            if not self.wx:
                return {"error": "微信客户端未初始化"}

            self.logger.info("正在获取微信状态信息...")

            # 尝试获取当前用户信息
            try:
                if hasattr(self.wx, 'nickname'):
                    nickname = self.wx.nickname
                    self.logger.info(f"当前微信账号: {nickname}")
                else:
                    self.logger.info("当前微信客户端已连接")
            except Exception as e:
                self.logger.warning(f"获取用户信息失败: {e}")

            # 尝试获取会话信息（如果支持）
            sessions = []
            session_count = 0

            try:
                if hasattr(self.wx, 'GetSessionList'):
                    sessions = self.wx.GetSessionList()
                    session_count = len(sessions)
                    self.logger.info(f"当前会话总数: {session_count}")

                    # 显示前5个会话的详细信息
                    for i, session in enumerate(sessions[:5], 1):
                        self.logger.info(f"  会话{i}: {session}")

                    if session_count > 5:
                        self.logger.info(f"  ... 还有 {session_count - 5} 个会话")
                else:
                    self.logger.warning("当前wxauto版本不支持GetSessionList方法")
                    self.logger.info("微信客户端状态: 已连接，但无法获取详细会话信息")

            except Exception as e:
                self.logger.error(f"获取会话列表失败: {e}")

            return {
                "total_sessions": session_count,
                "sessions": sessions,
                "status": "connected"
            }

        except Exception as e:
            self.logger.error(f"获取会话信息失败: {e}")
            return {"error": str(e)}

    def run_interactive_mode(self):
        """运行交互模式"""
        self.logger.info("="*50)
        self.logger.info("微信自动化工具启动")
        self.logger.info(f"当前版本: {self.wxauto_version}")
        self.logger.info("="*50)

        # 检查微信状态
        self.logger.info("⚠️ 请确保:")
        self.logger.info("1. 微信PC版已登录且窗口打开")
        self.logger.info("2. 网络连接正常")
        self.logger.info("3. 不要操作鼠标/键盘直到脚本完成")

        if not self.init_wechat():
            self.logger.error("微信状态检查失败，程序退出")
            return

        while True:
            try:
                print("\n" + "="*50)
                print("微信自动化工具菜单")
                print(f"当前版本: {self.wxauto_version}")
                print("="*50)

                if "Plus" in self.wxauto_version:
                    print("1. 批量添加好友 (自动模式) ✨")
                    print("2. 批量添加好友 (手动指导模式)")
                else:
                    print("1. 批量添加好友 (基础模式)")
                    print("2. 批量添加好友 (手动指导模式)")

                print("3. 获取会话信息")
                print("4. 启动自动回复 (实验性)")
                print("5. 停止自动回复")
                print("6. 手动回复模式 (推荐)")
                print("7. 升级到Plus版本")
                print("8. 退出程序")

                if "开源版本" in self.wxauto_version:
                    print("\n💡 提示: 升级到Plus版本可获得完整的自动添加好友功能")

                print("="*50)

                choice = input("请选择功能 (1-8): ").strip()

                if choice == "1":
                    if "Plus" in self.wxauto_version:
                        self.logger.info("准备批量添加好友 (Plus版自动模式)...")
                    else:
                        self.logger.info("准备批量添加好友 (基础模式)...")
                    result = self.batch_add_friends("auto")
                    self.print_batch_result(result)

                elif choice == "2":
                    self.logger.info("准备批量添加好友 (手动指导模式)...")
                    result = self.batch_add_friends("manual")
                    self.print_batch_result(result)

                elif choice == "3":
                    self.get_session_info()

                elif choice == "4":
                    self.start_auto_reply()

                elif choice == "5":
                    self.stop_auto_reply()

                elif choice == "6":
                    self.auto_reply.manual_reply_mode()

                elif choice == "7":
                    self.show_upgrade_info()

                elif choice == "8":
                    self.logger.info("程序退出")
                    self.stop_auto_reply()
                    break

                else:
                    print("无效选择，请重新输入")

            except KeyboardInterrupt:
                self.logger.info("用户中断程序")
                self.stop_auto_reply()
                break
            except Exception as e:
                self.logger.error(f"程序运行异常: {e}")

        self.print_safety_tips()
        self.logger.info("程序执行完成！")

    def print_batch_result(self, result: Dict):
        """打印批量处理结果"""
        self.logger.info("\n" + "="*30)
        self.logger.info("批量处理好友完成！")
        self.logger.info(f"✅ 成功: {result['success']} 人")
        self.logger.info(f"❌ 失败: {result['failed']} 人")
        self.logger.info(f"⏭️ 跳过: {result['skipped']} 人")
        self.logger.info("="*30)

    def show_upgrade_info(self):
        """显示升级信息"""
        print("\n" + "="*60)
        print("🚀 升级到wxauto Plus版本")
        print("="*60)
        print("Plus版本新增功能:")
        print("✅ AddNewFriend - 完全自动化添加好友")
        print("✅ GetNewFriends - 获取好友申请列表")
        print("✅ 自动接受好友申请")
        print("✅ 后台模式 - 不抢占鼠标")
        print("✅ 更多高级功能")
        print("")
        print("安装方法:")
        print("1. 卸载当前版本: pip uninstall wxauto")
        print("2. 安装Plus版本: pip install wxautox")
        print("3. 获取激活码: 联系作者微信")
        print("4. 激活: wxautox -a [激活码]")
        print("")
        print("💰 价格: 订阅制，1年期")
        print("📞 联系方式: 扫描作者微信二维码")
        print("🌐 官方文档: https://docs.wxauto.org/plus/")
        print("="*60)

        choice = input("\n是否现在升级? (y/n): ").strip().lower()
        if choice == 'y':
            print("正在为您打开官方文档...")
            try:
                import webbrowser
                webbrowser.open("https://docs.wxauto.org/plus/")
            except:
                print("请手动访问: https://docs.wxauto.org/plus/")

    def print_safety_tips(self):
        """打印安全提示"""
        self.logger.info("\n⚠️ 重要提示:")
        self.logger.info("1. 微信对频繁添加好友有严格限制")
        self.logger.info("2. 建议每日添加好友不超过10次")
        self.logger.info("3. 如遇到限制，请24小时后再试")
        self.logger.info("4. 请遵守微信使用规范，避免账号风险")


def main():
    """主函数"""
    try:
        # 创建微信自动化实例
        wechat_auto = WeChatAutomation()

        # 运行交互模式
        wechat_auto.run_interactive_mode()

    except Exception as e:
        print(f"程序运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()