# -*- coding: utf-8 -*-
"""
定时任务管理器
基于APScheduler实现的定时任务管理系统
用于管理微信自动化跟播的定时任务
"""

import os
import sys
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sqlite3

def loadTaskManagerConfig():
    """
    加载任务管理器配置
    
    Returns:
        dict: 配置字典
    """
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        
        if not os.path.exists(config_path):
            return getDefaultTaskManagerConfig()
            
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            
        return config
    except Exception as e:
        print(f"❌ [TASK_MANAGER] 配置加载失败: {str(e)}")
        return getDefaultTaskManagerConfig()

def getDefaultTaskManagerConfig():
    """
    获取默认任务管理器配置
    
    Returns:
        dict: 默认配置
    """
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
                "enable_detailed_logs": True
            }
        }
    }

def getTaskRetryConfig():
    """
    获取任务重试配置
    
    Returns:
        dict: 重试配置
    """
    try:
        config = loadTaskManagerConfig()
        system_config = config.get("system_config", {})
        retry_config = system_config.get("retry_config", {})
        intervals = system_config.get("intervals", {})
        
        return {
            "max_follow_retry": retry_config.get("max_follow_retry", 10),
            "max_bullet_retry": retry_config.get("max_bullet_retry", 3),
            "follow_task_retry_interval": intervals.get("follow_task_retry", 60),
            "bullet_screen_retry_interval": intervals.get("bullet_screen_retry", 10),
            "enable_auto_retry": retry_config.get("enable_auto_retry", True)
        }
    except Exception as e:
        print(f"❌ [TASK_MANAGER] 获取重试配置失败: {str(e)}")
        return {
            "max_follow_retry": 10,
            "max_bullet_retry": 3,
            "follow_task_retry_interval": 60,
            "bullet_screen_retry_interval": 10,
            "enable_auto_retry": True
        }

# 第三方库导入
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
    from apscheduler.executors.pool import ThreadPoolExecutor
except ImportError as e:
    print(f"❌ APScheduler库导入失败: {e}")
    print("请安装: pip install APScheduler")
    sys.exit(1)

# 本地模块导入
try:
    from sqlite3_util import query_table, create_table, table_exists
except ImportError as e:
    print(f"❌ 数据库模块导入失败: {e}")
    sys.exit(1)


# 全局函数，用于避免序列化问题
def execute_live_reminder_task(room_id: int, remark: str, db_path: str, task_id: str = None):
    """执行直播安排任务的全局函数 - 直接跟播"""
    try:
        print(f"🎯 执行直播安排任务: 直播间ID={room_id}, 备注={remark}")
        
        # 如果没有提供task_id，则生成一个用于日志记录
        if not task_id:
            from datetime import datetime
            task_id = f"live_reminder_{room_id}_{int(datetime.now().timestamp())}"
        
        # 🔥 修复：检查并标记任务状态，如果任务不存在则直接返回
        if check_task_status(task_id, db_path):
            mark_task_as_executed(task_id, db_path)
        else:
            print(f"⚠️ 任务 {task_id} 状态已失效、已执行或不存在，停止执行")
            # 如果任务不存在或已失效，直接返回，不再继续执行
            return
        
        # 1. 标记直播状态为已开播
        mark_live_as_started(room_id, db_path)
        
        # 2. 获取直播间信息
        from sqlite3_util import query_table
        rooms = query_table(
            db_path=db_path,
            table_name='rooms',
            where='id = ?',
            params=(room_id,)
        )
        
        if not rooms:
            print(f"❌ 未找到直播间: ID={room_id}")
            return
            
        room = rooms[0]
        room_name = room['name']
        
        # 3. 显示开始跟播通知
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(
                title="🚀 开始跟播",
                msg=f"直播间 {room_name} 开播时间到！\n即将开始自动跟播\n{remark}",
                duration=8,
                threaded=True
            )
            print(f"🔔 已显示跟播开始通知: {room_name}")
        except Exception as e:
            print(f"⚠️ 显示通知失败: {str(e)}")
        
        # 4. 等待2秒让用户看到通知
        import time
        time.sleep(2)
        
        # 5. 执行跟播
        print(f"🎮 开始跟播: {room_name} (ID: {room_id})")
        success = execute_single_room_follow(room_id, room_name)
        
        if success:
            print(f"✅ 跟播成功: {room_name}")
            add_task_log(task_id, 1, f"直播安排跟播成功: {room_name}", room_id, room_name, db_path)
        else:
            print(f"❌ 跟播失败: {room_name}")
            failure_reason = "跟播失败：可能是微信状态、网络连接错误或直播间名称有误/未在直播"
            add_task_log(task_id, 2, f"直播安排跟播失败: {room_name} - {failure_reason}", room_id, room_name, db_path)
            
            # 创建重试任务
            try:
                from task_manager import get_task_manager
                from datetime import datetime, timedelta
                
                task_manager = get_task_manager()
                if task_manager and task_manager.is_running:
                    retry_config = getTaskRetryConfig()
                    retry_time = datetime.now() + timedelta(seconds=retry_config["follow_task_retry_interval"])
                    retry_task_id = f"follow_task_{room_id}_{int(retry_time.timestamp())}_retry"
                    
                    retry_remark = f"直播安排重试任务 - 第1次重试\n原因：{failure_reason}\n失败直播间：{room_name}\n说明：尝试重新跟播失败的直播间"
                    
                    success = task_manager.add_follow_task(
                        task_id=retry_task_id,
                        room_ids=[room_id],
                        room_names=[room_name],
                        run_time=retry_time,
                        remark=retry_remark,
                        retry_count=1
                    )
                    
                    if success:
                        retry_interval = retry_config["follow_task_retry_interval"]
                        print(f"✅ 已创建重试任务: {retry_task_id}，将在{retry_interval}秒后重试")
                    else:
                        print(f"❌ 创建重试任务失败")
                        
            except Exception as retry_e:
                print(f"❌ 创建重试任务失败: {str(retry_e)}")
        
        print(f"✅ 直播安排任务完成: 直播间ID={room_id}")

    except Exception as e:
        print(f"❌ 执行直播安排任务失败: {str(e)}")


def send_live_notification(room_id: int, remark: str, db_path: str):
    """发送直播通知的全局函数"""
    try:
        # 获取直播间信息
        from sqlite3_util import query_table
        rooms = query_table(
            db_path=db_path,
            table_name='rooms',
            where='id = ?',
            params=(room_id,)
        )
        
        if not rooms:
            print(f"❌ 未找到直播间: ID={room_id}")
            return
            
        room = rooms[0]
        room_name = room['name']
        
        # 发送Windows通知
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(
                title="直播提醒",
                msg=f"直播间 {room_name} 即将开播！\n{remark}",
                duration=10,
                threaded=True
            )
            print(f"✅ 已发送通知: {room_name}")
        except ImportError:
            print("⚠️ win10toast未安装，无法发送系统通知")
        except Exception as e:
            print(f"❌ 发送通知失败: {str(e)}")
            
    except Exception as e:
        print(f"❌ 发送通知失败: {str(e)}")


def execute_follow_task(task_id: str, room_ids: List[int], room_names: List[str], db_path: str, retry_count: int = 0):
    """执行跟播任务的全局函数"""
    try:
        # 🔥 使用sync_print同步到进度窗口
        try:
            from apis import sync_print
            sync_print(f"🎯 开始执行跟播任务: {task_id}")
            sync_print(f"📋 涉及直播间: {len(room_ids)} 个")
        except:
            print(f"🎯 开始执行跟播任务: {task_id}")
            print(f"📋 涉及直播间: {len(room_ids)} 个")

        # 检查任务状态，只有状态为0的任务才执行
        if not check_task_status(task_id, db_path):
            room_names_str = '、'.join(room_names)
            add_task_log(task_id, 2, f"任务状态已失效或已执行，跳过执行 - 涉及直播间: {room_names_str}", db_path=db_path)
            return

        # 标记任务为已执行
        mark_task_as_executed(task_id, db_path)

        # 更新任务状态为执行中
        update_task_execution_status(task_id, 'executing', db_path)

        # 🔥 新增：初始化跟播进度状态并创建进度监控窗口
        try:
            from apis import (
                reset_follow_progress_logs,
                update_follow_progress_status,
                add_follow_progress_log,
                sync_print,
                API
            )

            # 重置进度日志
            reset_follow_progress_logs()

            # 初始化跟播状态
            update_follow_progress_status(
                is_following=True,
                room_count=len(room_ids),
                completed_count=0,
                progress=0,
                step="倒计时跟播开始"
            )

            # 添加初始日志
            room_names_str = ", ".join(room_names[:2])
            if len(room_names) > 2:
                room_names_str += f" 等{len(room_names)}个直播间"

            add_follow_progress_log(f"🚀 倒计时跟播任务开始", "info", 5, "任务初始化")
            add_follow_progress_log(f"📺 将跟播 {len(room_ids)} 个直播间: {room_names_str}", "info", 10, "任务准备")

            # 🔥 创建进度监控窗口
            api = API()
            progress_result = api.create_follow_progress_window(room_names_str)

            if progress_result["success"]:
                add_follow_progress_log("✅ 跟播进度监控窗口已创建", "success", 15, "窗口创建完成")
                print("🪟 跟播进度监控窗口创建成功")
            else:
                add_follow_progress_log(f"⚠️ 进度窗口创建失败: {progress_result['message']}", "warning")
                print(f"⚠️ 进度窗口创建失败: {progress_result['message']}")

        except Exception as progress_error:
            print(f"⚠️ 初始化跟播进度功能失败: {str(progress_error)}")
            # 不影响跟播任务继续执行
        
        # 在开始跟播前显示弹窗提醒
        room_names_str = '、'.join(room_names[:3])
        if len(room_names) > 3:
            room_names_str += f'等{len(room_names)}个'
        
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(
                title="🚀 开始跟播",
                msg=f"即将开始跟播 {len(room_names)} 个直播间\n直播间: {room_names_str}\n\n请确保微信正常运行且网络通畅",
                duration=8,
                threaded=True
            )
            print(f"🔔 已显示跟播提醒")
        except ImportError:
            print("⚠️ win10toast未安装，无法显示系统通知")
        except Exception as e:
            print(f"⚠️ 显示提醒失败: {str(e)}")
        
        # 等待1秒让用户看到提醒
        import time
        time.sleep(1)
        
        success_count = 0
        failed_rooms = []
        
        # 执行每个直播间的跟播
        for i, (room_id, room_name) in enumerate(zip(room_ids, room_names)):
            try:
                # 🔥 使用sync_print同步到进度窗口
                try:
                    sync_print(f"🎮 [{i+1}/{len(room_ids)}] 开始跟播: {room_name} (ID: {room_id})")
                except:
                    print(f"🎮 [{i+1}/{len(room_ids)}] 开始跟播: {room_name} (ID: {room_id})")

                # 🔥 更新跟播进度
                try:
                    from apis import add_follow_progress_log, update_follow_progress_status

                    current_progress = 20 + (i / len(room_ids)) * 70  # 20-90% 的进度范围
                    add_follow_progress_log(f"🎮 [{i+1}/{len(room_ids)}] 开始跟播: {room_name}", "info",
                                          current_progress, f"跟播第{i+1}个直播间", room_name)

                    update_follow_progress_status(
                        current_room=room_name,
                        progress=current_progress,
                        step=f"跟播第{i+1}个直播间",
                        completed_count=i
                    )
                except:
                    pass  # 不影响跟播任务执行

                # 调用跟播自动化逻辑
                success = execute_single_room_follow(room_id, room_name)

                if success:
                    success_count += 1
                    # 🔥 使用sync_print同步到进度窗口
                    try:
                        sync_print(f"✅ 跟播成功: {room_name}")
                    except:
                        print(f"✅ 跟播成功: {room_name}")
                    add_task_log(task_id, 1, f"跟播成功: {room_name}", room_id, room_name, db_path)

                    # 🔥 更新成功状态
                    try:
                        from apis import add_follow_progress_log, update_follow_progress_status

                        completed_progress = 20 + ((i + 1) / len(room_ids)) * 70
                        add_follow_progress_log(f"✅ 跟播成功: {room_name}", "success",
                                              completed_progress, f"第{i+1}个直播间完成", room_name)

                        update_follow_progress_status(
                            current_room=room_name,
                            progress=completed_progress,
                            step=f"第{i+1}个直播间完成",
                            completed_count=i+1
                        )
                    except:
                        pass

                else:
                    failed_rooms.append({'id': room_id, 'name': room_name})
                    failure_reason = "跟播失败：可能是微信状态、网络连接错误或直播间名称有误/未在直播"
                    # 🔥 使用sync_print同步到进度窗口
                    try:
                        sync_print(f"❌ {failure_reason}: {room_name}")
                    except:
                        print(f"❌ {failure_reason}: {room_name}")
                    add_task_log(task_id, 2, f"{failure_reason}: {room_name}", room_id, room_name, db_path)

                    # 🔥 更新失败状态
                    try:
                        from apis import add_follow_progress_log
                        add_follow_progress_log(f"❌ 跟播失败: {room_name}", "error",
                                              None, f"第{i+1}个直播间失败", room_name)
                    except:
                        pass
                    
            except Exception as e:
                failed_rooms.append({'id': room_id, 'name': room_name})
                error_msg = f"跟播异常: {room_name} - {str(e)}"
                print(f"❌ {error_msg}")
                add_task_log(task_id, 2, error_msg, room_id, room_name, db_path)
        
        # 任务完成状态处理
        if len(failed_rooms) == 0:
            # 全部成功
            update_task_execution_status(task_id, 'completed', db_path)
            success_msg = f"成功跟播 {success_count} 个直播间\n全部任务执行成功！"
            send_follow_notification(
                f"🎉 跟播完成",
                success_msg
            )
            add_task_log(task_id, 1, f"所有跟播任务完成，成功 {success_count} 个", db_path=db_path)

            # 🔥 修复：根据实际情况设置进度
            try:
                from apis import add_follow_progress_log, update_follow_progress_status
                
                # 如果是单个直播间，设置为60%（已进入直播间，但图像识别任务还在运行）
                # 如果是多个直播间，才设置为100%
                if len(room_ids) == 1:
                    add_follow_progress_log(f"✅ 直播间进入完成: {room_names[0]}", "success", 60, "直播间已进入")
                    add_follow_progress_log(f"🖼️ 图像识别任务已启动，正在监控商品图片", "info", 65, "监控进行中")
                    update_follow_progress_status(
                        is_following=True,  # 仍在跟播中
                        progress=65,
                        step="图像识别监控中",
                        completed_count=len(room_ids)
                    )
                else:
                    add_follow_progress_log(f"🎉 跟播任务全部完成: {success_count} 个直播间", "success", 100, "任务全部完成")
                    update_follow_progress_status(
                        is_following=False,
                        progress=100,
                        step="任务全部完成",
                        completed_count=len(room_ids)
                    )
            except:
                pass
        elif len(failed_rooms) < len(room_ids):
            # 部分成功
            update_task_execution_status(task_id, 'partial', db_path)
            failed_names = [room['name'] for room in failed_rooms[:3]]
            failed_text = '、'.join(failed_names)
            if len(failed_rooms) > 3:
                failed_text += f"等{len(failed_rooms)}个"

            partial_msg = f"成功: {success_count} 个\n失败: {len(failed_rooms)} 个\n失败直播间: {failed_text}\n\n失败原因可能是:\n• 微信状态异常\n• 网络连接错误\n• 直播间名称有误或未在直播"
            send_follow_notification(
                f"⚠️ 跟播部分完成",
                partial_msg
            )
            add_task_log(task_id, 2, f"部分成功：成功 {success_count} 个，失败 {len(failed_rooms)} 个", db_path=db_path)

            # 🔥 更新部分成功状态
            try:
                from apis import add_follow_progress_log, update_follow_progress_status
                add_follow_progress_log(f"⚠️ 跟播任务部分完成: 成功 {success_count} 个，失败 {len(failed_rooms)} 个", "warning", 95, "任务部分完成")
                update_follow_progress_status(
                    is_following=False,
                    progress=95,
                    step="任务部分完成",
                    completed_count=success_count
                )
            except:
                pass
        else:
            # 全部失败
            update_task_execution_status(task_id, 'failed', db_path)
            fail_msg = f"所有 {len(room_ids)} 个直播间跟播都失败了\n\n可能原因:\n• 微信未正常启动或状态异常\n• 网络连接问题\n• 直播间名称有误或未在直播\n• 系统环境异常"
            send_follow_notification(
                f"❌ 跟播失败",
                fail_msg
            )
            # 注释掉重复的总结日志，因为每个房间失败已经单独记录了
            # add_task_log(task_id, 2, f"所有跟播任务失败，失败 {len(room_ids)} 个", db_path=db_path)

            # 🔥 更新失败状态
            try:
                from apis import add_follow_progress_log, update_follow_progress_status
                add_follow_progress_log(f"❌ 跟播任务全部失败: {len(room_ids)} 个直播间", "error", 0, "任务全部失败")
                update_follow_progress_status(
                    is_following=False,
                    progress=0,
                    step="任务全部失败",
                    completed_count=0
                )
            except:
                pass
            
            # 全部失败时创建重试任务
            if retry_count < 3:  # 最多重试3次
                try:
                    from task_manager import get_task_manager
                    task_manager = get_task_manager()
                    if task_manager and task_manager.is_running:
                        # 获取失败直播间信息
                        failed_names = [room['name'] for room in failed_rooms]
                        failed_names_str = '、'.join(failed_names[:3])
                        if len(failed_rooms) > 3:
                            failed_names_str += f'等{len(failed_rooms)}个'
                        
                        failure_reason = "跟播失败：可能是微信状态、网络连接错误或直播间名称有误/未在直播"
                        
                        success = task_manager.add_retry_task(
                            original_task_id=task_id,
                            room_ids=room_ids,
                            room_names=room_names,
                            retry_count=retry_count + 1,
                            failure_reason=failure_reason,
                            failed_rooms_str=failed_names_str
                        )
                        if success:
                            retry_config = getTaskRetryConfig()
                            retry_interval = retry_config["follow_task_retry_interval"]
                            print(f"✅ 已创建重试任务，将在{retry_interval}秒后重试")
                except Exception as retry_e:
                    print(f"❌ 创建重试任务失败: {str(retry_e)}")
        
        print(f"🎯 跟播任务执行完成: {task_id}")
        print(f"📊 结果统计: 成功 {success_count}/{len(room_ids)} 个")
        
    except Exception as e:
        print(f"❌ 执行跟播任务失败: {str(e)}")
        update_task_execution_status(task_id, 'error', db_path)
        add_task_log(task_id, 2, f"任务执行异常: {str(e)}", db_path=db_path)
        send_follow_notification("❌ 跟播任务异常", f"任务执行出现错误: {str(e)}")


def execute_danmu_task(task_id: str, db_path: str):
    """执行弹幕任务的全局函数"""
    try:
        import json
        # 使用sync_print同步到进度窗口
        try:
            from apis import add_follow_progress_log
            add_follow_progress_log(f"🚀 执行弹幕任务: {task_id}", "info", None, "弹幕执行", None)
        except:
            pass
        print(f"🚀 执行弹幕任务: {task_id}")
        
        # 读取任务数据
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT status, task_data FROM tasks 
            WHERE task_id = ? AND task_type = 'danmu_task'
        """, (task_id,))
        
        result = cursor.fetchone()
        if not result:
            try:
                add_follow_progress_log(f"❌ 弹幕任务 {task_id} 不存在", "error", None, "任务验证", None)
            except:
                pass
            print(f"❌ 弹幕任务 {task_id} 不存在")
            return
        
        status, task_data_str = result
        if status != 0:
            try:
                add_follow_progress_log(f"⚠️ 弹幕任务 {task_id} 状态为 {status}，跳过执行", "warning", None, "任务验证", None)
            except:
                pass
            print(f"⚠️ 弹幕任务 {task_id} 状态为 {status}，跳过执行")
            return
        
        # 解析任务数据 - 直接从task_data读取所有信息
        task_data = json.loads(task_data_str)
        room_id = task_data.get('room_id', 0)
        room_name = task_data.get('room_name', '未知直播间')
        speech_content = task_data.get('speech_content', '默认弹幕内容')
        task_index = task_data.get('task_index', 1)
        total_tasks = task_data.get('total_tasks', 1)
        
        # 🔥 如果task_data中的room_name不可靠，从数据库重新查询
        if room_name == '测试直播间' or room_name == '未知直播间':
            try:
                conn_room = sqlite3.connect(db_path)
                cursor_room = conn_room.cursor()
                cursor_room.execute("SELECT name FROM rooms WHERE id = ?", (room_id,))
                result_room = cursor_room.fetchone()
                conn_room.close()
                
                if result_room:
                    room_name = result_room[0]
                    try:
                        add_follow_progress_log(f"🔍 重新查询到真实直播间名称: {room_name}", "info", None, "数据查询", room_name)
                    except:
                        pass
                    print(f"🔍 [DATABASE] 重新查询到真实直播间名称: {room_name}")
            except Exception as e:
                try:
                    add_follow_progress_log(f"⚠️ 重新查询直播间名称失败: {str(e)}", "warning", None, "数据查询", None)
                except:
                    pass
                print(f"⚠️ [DATABASE] 重新查询直播间名称失败: {str(e)}")
        
        # 同步任务详情到进度窗口
        try:
            add_follow_progress_log(f"📋 弹幕任务详情:", "info", None, "任务信息", room_name)
            add_follow_progress_log(f"   • 直播间: {room_name} (ID: {room_id})", "info", None, "任务信息", room_name)
            add_follow_progress_log(f"   • 弹幕内容: {speech_content}", "info", None, "任务信息", room_name)
            add_follow_progress_log(f"   • 任务序号: {task_index}/{total_tasks}", "info", None, "任务信息", room_name)
        except:
            pass
        print(f"📋 弹幕任务详情 (从task_data读取):")
        print(f"   • 直播间: {room_name} (ID: {room_id})")
        print(f"   • 弹幕内容: {speech_content}")
        print(f"   • 任务序号: {task_index}/{total_tasks}")
        print(f"   • 完整task_data: {task_data}")
        
        # 导入弹幕发送函数
        try:
            from follwRoom import getWechat, getWxChromeWindowByIndex, switchRoomAndSendContent
            
            # 获取微信窗口
            wechat = getWechat()
            chrome_view = getWxChromeWindowByIndex(0)
            
            if not chrome_view:
                error_msg = "微信Chrome窗口未找到，无法发送弹幕"
                try:
                    add_follow_progress_log(f"❌ {error_msg}", "error", None, "窗口检查", room_name)
                except:
                    pass
                print(f"❌ {error_msg}")
                # 🔥 更新任务执行状态为失败
                update_task_execution_status(task_id, 'failed', db_path)
                mark_task_as_executed(task_id, db_path)
                return
            
            # 🔥 直接调用你封装好的发送函数
            try:
                add_follow_progress_log(f"🚀 开始发送弹幕: {speech_content[:30]}{'...' if len(speech_content) > 30 else ''}", "info", None, "弹幕发送", room_name)
                # 🔥 新增：发送前的详细信息
                add_follow_progress_log(f"📋 发送详情:", "info", None, "发送准备", room_name)
                add_follow_progress_log(f"   • 序号: 第{task_index}条/共{total_tasks}条", "info", None, "发送详情", room_name)
                add_follow_progress_log(f"   • 内容长度: {len(speech_content)}字符", "info", None, "发送详情", room_name)
                add_follow_progress_log(f"   • 发送时间: {datetime.now().strftime('%H:%M:%S')}", "info", None, "发送详情", room_name)
            except:
                pass

            # 🔥 记录发送开始时间
            send_start_time = datetime.now()

            success = switchRoomAndSendContent(
                wechat=wechat,
                chromeView=chrome_view,
                room_name=f"{room_name}的直播",
                content=speech_content
            )

            # 🔥 计算发送耗时
            send_duration = (datetime.now() - send_start_time).total_seconds()
            
            if success:
                success_msg = f"弹幕发送成功: 任务 {task_index}/{total_tasks}"
                try:
                    add_follow_progress_log(f"✅ {success_msg}", "success", None, "弹幕发送", room_name)
                    # 🔥 新增：发送成功的详细统计信息
                    add_follow_progress_log(f"📊 发送成功统计:", "success", None, "发送统计", room_name)
                    add_follow_progress_log(f"   • 发送耗时: {send_duration:.2f}秒", "success", None, "性能统计", room_name)
                    add_follow_progress_log(f"   • 完成时间: {datetime.now().strftime('%H:%M:%S')}", "success", None, "时间统计", room_name)
                    add_follow_progress_log(f"   • 剩余任务: {total_tasks - task_index}条", "success", None, "进度统计", room_name)

                    # 🔥 更新进度：弹幕发送成功 - 从85%到95%动态变化
                    progress_value = 85 + (task_index * 10 // total_tasks)  # 85-95%之间动态变化
                    add_follow_progress_log(f"💬 第{task_index}条弹幕发送成功", "success", progress_value, "弹幕发送中")
                    update_follow_progress_status(progress=progress_value, step=f"弹幕发送中 ({task_index}/{total_tasks})")

                    print(f"📊 [PROGRESS] 弹幕发送进度更新: {progress_value}% ({task_index}/{total_tasks})")
                except:
                    pass
                print(f"✅ {success_msg}")
                
                # 🔥 添加下一条发送时间提示
                try:
                    if task_index < total_tasks:  # 还有未发送的弹幕
                        from follwRoom import getBulletScreenInterval
                        interval_seconds = getBulletScreenInterval()
                        next_time = datetime.now() + timedelta(seconds=interval_seconds)
                        next_time_str = next_time.strftime('%H:%M:%S')
                        
                        next_msg = f"📅 下一条弹幕发送时间: {next_time_str}"
                        print(f"📅 [DANMU_SCHEDULE] {next_msg}")
                        add_follow_progress_log(next_msg, "info", None, "发送计划", room_name)
                    else:
                        # 这是最后一条弹幕
                        final_msg = f"🎉 这是最后一条弹幕，{room_name} 所有话术发送完毕"
                        print(f"🎉 [DANMU_COMPLETE] {final_msg}")
                        add_follow_progress_log(final_msg, "success", None, "发送完成", room_name)
                except Exception as e:
                    print(f"⚠️ 计算下次发送时间失败: {e}")
                
                # 🔥 更新任务执行状态为成功
                update_task_execution_status(task_id, 'completed', db_path)
                
                # 🔥 检查是否所有弹幕任务都已完成
                try:
                    print(f"🔍 [COMPLETION_CHECK] 正在检查直播间 {room_id} 的任务完成情况...")
                    is_all_completed, completion_stats = self._check_all_danmu_tasks_completed_with_stats(room_id, db_path)
                    print(f"🔍 [COMPLETION_CHECK] 检查结果: {'全部完成' if is_all_completed else '尚未完成'}")
                    
                    if is_all_completed:
                        # 🔥 详细的完成统计
                        completion_msg = f"🎉 {room_name} 所有话术发送完毕，跟播任务完成"
                        print(f"🎉 [COMPLETION] {completion_msg}")
                        
                        # 🔥 输出弹幕发送统计到监听窗口 - 增强版本
                        try:
                            add_follow_progress_log(f"📊 弹幕发送最终统计:", "success", 98, "发送统计")
                            add_follow_progress_log(f"✅ 成功发送: {completion_stats['completed']}条弹幕", "success", 99, "统计详情")
                            add_follow_progress_log(f"❌ 发送失败: {completion_stats['total'] - completion_stats['completed']}条弹幕", "info", 99, "统计详情")
                            add_follow_progress_log(f"📺 直播间: {room_name}", "success", 99, "统计详情")
                            add_follow_progress_log(f"⏱️ 发送完成时间: {datetime.now().strftime('%H:%M:%S')}", "success", 99, "统计详情")

                            # 🔥 新增：计算成功率
                            success_rate = (completion_stats['completed'] / completion_stats['total'] * 100) if completion_stats['total'] > 0 else 0
                            add_follow_progress_log(f"📈 发送成功率: {success_rate:.1f}%", "success", 99, "统计详情")

                            add_follow_progress_log(completion_msg, "success", 100, "跟播完成")
                            add_follow_progress_log(f"✨ 跟播结束，感谢使用！", "success", 100, "任务结束")
                            
                            print(f"✅ [COMPLETION] 统计信息已输出到监听窗口")
                        except Exception as log_e:
                            print(f"❌ [COMPLETION] 输出统计到监听窗口失败: {log_e}")
                            # 备用输出方式
                            try:
                                from apis import sync_print
                                sync_print(f"📊 弹幕发送统计: 成功发送{completion_stats['completed']}条弹幕", "success", room_name, "发送统计")
                                sync_print(f"🎉 {room_name} 所有话术发送完毕，跟播任务完成", "success", room_name, "跟播完成")
                                sync_print(f"✨ 跟播结束，感谢使用！", "success", room_name, "任务结束")
                            except Exception as sync_e:
                                print(f"❌ [COMPLETION] 备用输出也失败: {sync_e}")
                        
                        update_follow_progress_status(
                            is_following=False,
                            progress=100,
                            step="跟播任务完成",
                            completed_count=1
                        )
                        
                        # 🔥 发送完成通知
                        try:
                            from follwRoom import showToast
                            showToast("🎉 跟播完成", f"{room_name}\n✅ 成功发送 {completion_stats['completed']} 条弹幕\n跟播任务已结束")
                        except:
                            pass
                            
                    else:
                        print(f"📊 [COMPLETION_CHECK] 还有未完成的弹幕任务，继续等待...")
                        
                except Exception as e:
                    print(f"❌ [COMPLETION_CHECK] 检查任务完成状态失败: {e}")
                    import traceback
                    traceback.print_exc()
                    pass
                
                # 🔥 弹幕发送成功通知
                try:
                    from follwRoom import showToast
                    showToast("💬 弹幕发送成功", f"直播间: {room_name}\n第{task_index}条弹幕已发送\n内容: {speech_content[:20]}{'...' if len(speech_content) > 20 else ''}")
                except:
                    pass
                    
            else:
                error_msg = f"弹幕发送失败: 任务 {task_index}/{total_tasks}"
                try:
                    add_follow_progress_log(f"❌ {error_msg}", "error", None, "弹幕发送", room_name)
                    # 🔥 新增：发送失败的详细信息
                    add_follow_progress_log(f"📊 发送失败详情:", "error", None, "失败分析", room_name)
                    add_follow_progress_log(f"   • 失败耗时: {send_duration:.2f}秒", "error", None, "性能统计", room_name)
                    add_follow_progress_log(f"   • 失败时间: {datetime.now().strftime('%H:%M:%S')}", "error", None, "时间统计", room_name)
                    add_follow_progress_log(f"   • 弹幕内容: {speech_content[:50]}{'...' if len(speech_content) > 50 else ''}", "error", None, "内容信息", room_name)
                    add_follow_progress_log(f"   • 剩余任务: {total_tasks - task_index}条", "error", None, "进度统计", room_name)
                except:
                    pass
                print(f"❌ {error_msg}")

                # 🔥 更新任务执行状态为失败
                update_task_execution_status(task_id, 'failed', db_path)
                
                # try:
                #     from follwRoom import showToast
                #     showToast("⚠️ 弹幕发送失败", f"直播间: {room_name}\n第{task_index}条弹幕发送失败")
                # except:
                #     pass
            
            # 标记任务已执行（状态字段）
            mark_task_as_executed(task_id, db_path)
            
        except ImportError as import_e:
            print(f"❌ 导入弹幕发送模块失败: {str(import_e)}")
            # 🔥 更新任务执行状态为错误
            update_task_execution_status(task_id, 'error', db_path)
            mark_task_as_executed(task_id, db_path)
            
        conn.close()
        
    except Exception as e:
        print(f"❌ 执行弹幕任务异常: {str(e)}")
        print(f"📊 异常详情: 任务ID={task_id}")
        
        # 记录异常日志但不中断其他任务
        try:
            import traceback
            print(f"🔍 错误堆栈: {traceback.format_exc()}")
            
            # 🔥 更新任务执行状态为错误
            update_task_execution_status(task_id, 'error', db_path)
            # 确保任务被标记为已执行，避免重复执行
            mark_task_as_executed(task_id, db_path)
        except Exception as mark_e:
            print(f"⚠️ 标记任务执行状态失败: {str(mark_e)}")
        
        # 🔥 重要：异常不应该中断其他任务的执行
        print(f"📋 任务 {task_id} 已处理完毕，其他任务将继续执行")


def execute_test_follow_task(task_id: str, room_ids: List[int], room_names: List[str], db_path: str):
    """
    执行测试跟播任务的全局函数 - 只测试话术输入，不实际发送
    
    Args:
        task_id: 任务ID
        room_ids: 直播间ID列表
        room_names: 直播间名称列表
        db_path: 数据库路径
    """
    try:
        print(f"🧪 开始执行测试跟播任务: {task_id}")
        print(f"📋 涉及直播间: {len(room_ids)} 个（仅测试模式）")
        
        # 检查任务状态，只有状态为0的任务才执行
        if not check_task_status(task_id, db_path):
            room_names_str = '、'.join(room_names)
            add_task_log(task_id, 2, f"测试任务状态已失效或已执行，跳过执行 - 涉及直播间: {room_names_str}", db_path=db_path)
            return
        
        # 标记任务为已执行
        mark_task_as_executed(task_id, db_path)
        
        # 更新任务状态为执行中
        update_task_execution_status(task_id, 'executing', db_path)
        
        success_count = 0
        failed_rooms = []
        
        # 执行每个直播间的测试跟播
        for i, (room_id, room_name) in enumerate(zip(room_ids, room_names)):
            try:
                print(f"🧪 [{i+1}/{len(room_ids)}] 开始测试跟播: {room_name} (ID: {room_id})")
                
                # 调用测试模式的跟播自动化逻辑
                success = execute_single_room_follow(room_id, room_name, test_mode=True)
                
                if success:
                    success_count += 1
                    print(f"✅ 测试跟播成功: {room_name}")
                    add_task_log(task_id, 1, f"测试跟播成功: {room_name}（话术测试完成，未实际发送）", room_id, room_name, db_path)
                else:
                    failed_rooms.append({'id': room_id, 'name': room_name})
                    failure_reason = "测试跟播失败：可能是微信状态、网络连接错误或直播间名称有误/未在直播"
                    print(f"❌ {failure_reason}: {room_name}")
                    add_task_log(task_id, 2, f"{failure_reason}: {room_name}", room_id, room_name, db_path)
                    
            except Exception as e:
                failed_rooms.append({'id': room_id, 'name': room_name})
                error_msg = f"测试跟播异常: {room_name} - {str(e)}"
                print(f"❌ {error_msg}")
                add_task_log(task_id, 2, error_msg, room_id, room_name, db_path)
        
        # 任务完成状态处理
        if len(failed_rooms) == 0:
            # 全部成功
            update_task_execution_status(task_id, 'completed', db_path)
            success_msg = f"成功测试 {success_count} 个直播间\n所有话术测试完成！\n注意：仅测试输入，未实际发送"
            send_follow_notification(
                f"🧪 测试跟播完成", 
                success_msg
            )
            add_task_log(task_id, 1, f"所有测试跟播任务完成，成功 {success_count} 个", db_path=db_path)
        elif len(failed_rooms) < len(room_ids):
            # 部分成功
            update_task_execution_status(task_id, 'partial', db_path)
            failed_names = [room['name'] for room in failed_rooms[:3]]
            failed_text = '、'.join(failed_names)
            if len(failed_rooms) > 3:
                failed_text += f"等{len(failed_rooms)}个"
                
            partial_msg = f"成功测试: {success_count} 个\n失败: {len(failed_rooms)} 个\n失败直播间: {failed_text}\n注意：仅测试模式"
            send_follow_notification(
                f"🧪 测试跟播部分完成", 
                partial_msg
            )
            add_task_log(task_id, 2, f"部分成功：成功 {success_count} 个，失败 {len(failed_rooms)} 个", db_path=db_path)
        else:
            # 全部失败
            update_task_execution_status(task_id, 'failed', db_path)
            fail_msg = f"所有 {len(room_ids)} 个直播间测试都失败了\n请检查微信和直播间状态"
            send_follow_notification(
                f"❌ 测试跟播失败", 
                fail_msg
            )
            add_task_log(task_id, 2, f"所有测试跟播任务失败，失败 {len(room_ids)} 个", db_path=db_path)
        
        print(f"🧪 测试跟播任务执行完成: {task_id}")
        print(f"📊 结果统计: 成功 {success_count}/{len(room_ids)} 个")
        
    except Exception as e:
        print(f"❌ 执行测试跟播任务失败: {str(e)}")
        update_task_execution_status(task_id, 'error', db_path)
        add_task_log(task_id, 2, f"测试任务执行异常: {str(e)}", db_path=db_path)


def execute_single_room_follow(room_id: int, room_name: str, test_mode: bool = False) -> bool:
    """执行单个直播间的跟播（支持测试模式）"""
    try:
        # 导入跟播模块
        import sys
        import os
        import time
        import random
        
        # 🔥 同步打印到进度窗口
        try:
            from apis import add_follow_progress_log
            add_follow_progress_log(f"开始执行直播间跟播: {room_name}", "info", 
                                  None, "跟播初始化", room_name)
        except:
            pass
        
        # 确保可以导入 follwRoom 模块
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.append(current_dir)
            
        from follwRoom import initEnterRoomWithTest, getWechat
        import uiautomation as auto
        
        # 🔥 记录模块导入成功
        try:
            from apis import add_follow_progress_log
            add_follow_progress_log("跟播模块导入成功", "success", None, "模块加载", room_name)
        except:
            pass
        
        # 在新线程中初始化COM (重要!)
        with auto.UIAutomationInitializerInThread():
            # 🔥 记录COM初始化
            try:
                from apis import add_follow_progress_log
                add_follow_progress_log("COM环境初始化成功", "success", None, "环境准备", room_name)
            except:
                pass
            
            # 获取微信窗口
            try:
                from apis import add_follow_progress_log
                add_follow_progress_log("正在获取微信窗口...", "info", None, "窗口获取", room_name)
            except:
                pass
                
            wechat = getWechat()
            if not wechat:
                try:
                    from apis import add_follow_progress_log
                    add_follow_progress_log("无法找到微信窗口", "error", None, "窗口获取", room_name)
                except:
                    pass
                print(f"❌ 无法找到微信窗口")
                return False
            else:
                try:
                    from apis import add_follow_progress_log
                    add_follow_progress_log("微信窗口获取成功", "success", None, "窗口获取", room_name)
                except:
                    pass
            
            # 执行改进的跟播逻辑
            if test_mode:
                # 🔥 记录测试模式开始
                try:
                    from apis import add_follow_progress_log
                    add_follow_progress_log("启动测试模式: 进入直播间并测试所有话术", "info",
                                          None, "测试模式", room_name)
                    add_follow_progress_log("测试模式将模拟发送所有绑定话术", "info",
                                          None, "测试模式", room_name)
                except:
                    print(f"🧪 测试模式: 进入直播间并测试所有话术")

                try:
                    from apis import add_follow_progress_log
                    add_follow_progress_log("正在调用跟播核心功能...", "info",
                                          None, "跟播执行", room_name)
                except:
                    pass

                result = initEnterRoomWithTest(
                    wechat=wechat,
                    roomName=room_name,
                    room_id=room_id,
                    test_mode=True,
                    interval_seconds=getTaskRetryConfig()["bullet_screen_retry_interval"]
                )
            else:
                # 🔥 记录正常模式开始
                try:
                    from apis import add_follow_progress_log
                    add_follow_progress_log("启动正常模式: 进入直播间并启动图像识别", "info",
                                          None, "正常模式", room_name)
                    add_follow_progress_log("将自动识别商品图片并发送话术", "info",
                                          None, "正常模式", room_name)
                except:
                    print(f"🎯 正常模式: 进入直播间并发送话术")

                try:
                    from apis import add_follow_progress_log
                    add_follow_progress_log("正在调用跟播核心功能...", "info",
                                          None, "跟播执行", room_name)
                except:
                    pass

                result = initEnterRoomWithTest(
                    wechat=wechat,
                    roomName=room_name,
                    room_id=room_id,
                    test_mode=False
                )

            if result:
                # 🔥 记录跟播任务成功完成
                try:
                    from apis import add_follow_progress_log
                    add_follow_progress_log(f"跟播任务执行完成: {room_name}", "success",
                                          None, "任务完成", room_name)
                    if test_mode:
                        add_follow_progress_log("测试模式执行成功，话术发送完毕", "success",
                                              None, "测试完成", room_name)
                    else:
                        add_follow_progress_log("正常模式执行成功，图像识别任务已启动", "success",
                                              None, "跟播完成", room_name)
                except:
                    print(f"✅ 跟播任务完成: {room_name}")

                # 🔥 更新成功状态
                try:
                    from apis import add_follow_progress_log
                    add_follow_progress_log(f"✅ 跟播任务完成: {room_name}", "success",
                                          None, "单个直播间完成", room_name)
                except:
                    pass

                return True
            else:
                # 🔥 记录跟播任务失败
                try:
                    from apis import add_follow_progress_log
                    add_follow_progress_log(f"跟播任务执行失败: {room_name}", "error",
                                          None, "任务失败", room_name)
                    add_follow_progress_log("可能原因: 直播间未找到或微信连接异常", "error",
                                          None, "失败分析", room_name)
                except:
                    print(f"❌ 跟播任务失败: {room_name}")

                return False
            
    except Exception as e:
        # 🔥 记录跟播异常详情
        try:
            from apis import add_follow_progress_log
            add_follow_progress_log(f"直播间跟播出现异常: {room_name}", "error",
                                  None, "异常处理", room_name)
            add_follow_progress_log(f"异常详情: {str(e)}", "error",
                                  None, "异常详情", room_name)
        except:
            print(f"❌ 单个直播间跟播失败: {room_name} - {str(e)}")

        # 🔥 更新异常状态
        try:
            from apis import add_follow_progress_log
            add_follow_progress_log(f"❌ 单个直播间跟播异常: {room_name} - {str(e)}", "error",
                                  None, "跟播异常", room_name)
        except:
            pass

        return False


def get_room_speeches_for_follow(room_id: int) -> List[Dict]:
    """获取直播间的话术用于跟播"""
    try:
        import sqlite3
        
        # 直接使用SQL查询获取直播间绑定的话术
        conn = sqlite3.connect('system.db')
        conn.row_factory = sqlite3.Row  # 使结果可以通过字段名访问
        cursor = conn.cursor()
        
        query = """
            SELECT s.content, s.id
            FROM room_speeches rs
            JOIN speech s ON rs.speech_id = s.id
            WHERE rs.room_id = ? AND rs.status = 1 AND s.status = 1
            ORDER BY rs.create_time ASC
            LIMIT 10
        """
        
        cursor.execute(query, (room_id,))
        results = cursor.fetchall()
        
        # 转换为字典列表
        speeches = [dict(row) for row in results]
        
        conn.close()
        
        if speeches:
            print(f"📋 获取到 {len(speeches)} 条话术")
            return speeches
        else:
            print(f"⚠️ 直播间 {room_id} 没有绑定的话术")
            return []
            
    except Exception as e:
        print(f"❌ 获取直播间话术失败: {str(e)}")
        return []


def schedule_retry_if_needed(task_id: str, failed_rooms: List[Dict], retry_count: int, db_path: str, max_retries: int = None):
    """安排重试任务（简化版）"""
    try:
        # 从配置获取最大重试次数
        if max_retries is None:
            retry_config = getTaskRetryConfig()
            max_retries = retry_config["max_follow_retry"]
            
        if retry_count >= max_retries:
            print(f"⚠️ 任务 {task_id} 已达到最大重试次数 ({max_retries})，不再重试")
            return
            
        if not failed_rooms:
            return
            
        # 从配置获取重试延迟时间
        retry_config = getTaskRetryConfig()
        retry_delay_seconds = retry_config["follow_task_retry_interval"]
        retry_time = datetime.now() + timedelta(seconds=retry_delay_seconds)
        
        # 创建重试任务
        from task_manager import get_task_manager
        task_manager = get_task_manager()
        
        # 获取失败直播间信息
        failed_names = [room['name'] for room in failed_rooms]
        failed_names_str = '、'.join(failed_names[:3])
        if len(failed_rooms) > 3:
            failed_names_str += f'等{len(failed_rooms)}个'
        
        failure_reason = "跟播失败：可能是微信状态、网络连接错误或直播间名称有误/未在直播"
        
        # 创建跟播重试任务
        retry_task_id = f"{task_id}_retry_{retry_count + 1}"
        room_ids = [room['id'] for room in failed_rooms]
        room_names = [room['name'] for room in failed_rooms]
        
        follow_remark = f"跟播重试任务 - 第{retry_count + 1}次重试\n原因：{failure_reason}\n失败直播间：{failed_names_str}\n说明：尝试重新跟播失败的直播间"
        
        success = task_manager.add_follow_task(
            task_id=retry_task_id,
            room_ids=room_ids,
            room_names=room_names, 
            run_time=retry_time,
            remark=follow_remark,
            retry_count=retry_count + 1
        )
        
        if success:
            print(f"📅 已安排跟播重试任务: {retry_task_id}，将在 {retry_delay_seconds} 秒后执行")
        else:
            print(f"❌ 安排跟播重试任务失败: {retry_task_id}")
            
    except Exception as e:
        print(f"❌ 安排重试失败: {str(e)}")


def update_task_execution_status(task_id: str, status: str, db_path: str):
    """更新任务执行状态"""
    try:
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            UPDATE tasks SET execution_status = ?, last_execution_time = ? WHERE task_id = ?
        """, (status, update_time, task_id))
        
        conn.commit()
        conn.close()
        
        print(f"📝 任务状态已更新: {task_id} -> {status}")
        
    except Exception as e:
        print(f"❌ 更新任务状态失败: {str(e)}")


def send_follow_notification(title: str, message: str):
    """发送跟播通知"""
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(
            title=title,
            msg=message,
            duration=12,
            threaded=True
        )
        print(f"🔔 已发送通知: {title}")
    except ImportError:
        print("⚠️ win10toast未安装，无法发送系统通知")
    except Exception as e:
        print(f"❌ 发送通知失败: {str(e)}")


def mark_live_as_started(room_id: int, db_path: str):
    """标记直播为已开播状态的全局函数"""
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 更新直播时间表中的状态
        cursor.execute("""
            UPDATE time_of_live 
            SET status = 1 
            WHERE room_id = ? AND status = 0
        """, (room_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 已标记直播间 {room_id} 为已开播")
        
    except Exception as e:
        print(f"❌ 标记直播状态失败: {str(e)}")


def add_task_log(task_id: str, status: int, message: str, room_id: int = None, room_name: str = None, db_path: str = 'system.db'):
    """
    添加任务日志记录
    
    Args:
        task_id: 任务ID
        status: 状态 1=成功，2=失败
        message: 状态详情
        room_id: 直播间ID
        room_name: 直播间名称
        db_path: 数据库路径
    """
    try:
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        execution_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            INSERT INTO task_log (task_id, status, message, room_id, room_name, execution_time) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (task_id, status, message, room_id, room_name, execution_time))
        
        conn.commit()
        conn.close()
        
        status_text = "成功" if status == 1 else "失败"
        print(f"📝 任务日志已记录: {task_id} - {status_text}: {message}")
        
    except Exception as e:
        print(f"❌ 记录任务日志失败: {str(e)}")


def check_task_status(task_id: str, db_path: str) -> bool:
    """
    检查任务状态，只有状态为0（等待触发）的任务才会执行
    
    Args:
        task_id: 任务ID
        db_path: 数据库路径
        
    Returns:
        bool: True表示可以执行（状态为0），False表示不可执行
    """
    try:
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT status FROM tasks WHERE task_id = ?
        """, (task_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result is None:
            print(f"⚠️ 任务 {task_id} 不存在")
            return False
            
        task_status = result['status']
        
        if task_status == 0:
            print(f"✅ 任务 {task_id} 状态为等待触发，可以执行")
            return True
        elif task_status == 1:
            print(f"⚠️ 任务 {task_id} 已被触发，跳过执行")
            return False
        else:
            print(f"⚠️ 任务 {task_id} 状态异常: {task_status}")
            return False
            
    except Exception as e:
        print(f"❌ 检查任务状态失败: {str(e)}")
        return False


def mark_task_as_executed(task_id: str, db_path: str):
    """
    标记任务为已执行（状态为1）
    
    Args:
        task_id: 任务ID
        db_path: 数据库路径
    """
    try:
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE tasks SET status = 1 WHERE task_id = ?
        """, (task_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 任务 {task_id} 已标记为已执行")
        
    except Exception as e:
        print(f"❌ 标记任务状态失败: {str(e)}")


def mark_live_as_started(room_id: int, db_path: str):
    """标记直播状态为已开播"""
    try:
        from sqlite3_util import query_table
        import sqlite3

        # 查找该直播间的待开播时间记录
        live_times = query_table(
            db_path=db_path,
            table_name='time_of_live',
            where='room_id = ? AND status = 0',  # 0=等待开播
            params=(room_id,),
            order_by='live_time ASC',
            limit=1
        )

        if live_times:
            live_time_record = live_times[0]
            live_time_id = live_time_record['id']

            # 更新状态为已开播
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE time_of_live SET status = 1 WHERE id = ?
            """, (live_time_id,))

            conn.commit()
            conn.close()

            print(f"✅ 已标记直播间 {room_id} 为已开播状态")
        else:
            print(f"⚠️ 未找到直播间 {room_id} 的待开播记录")

    except Exception as e:
        print(f"❌ 标记直播状态失败: {str(e)}")


class TaskManager:
    """
    定时任务管理器
    负责管理所有的定时任务，包括微信跟播提醒等
    """
    
    def __init__(self, db_path: str = 'system.db'):
        """
        初始化任务管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.scheduler = None
        self.is_running = False
        
        # 配置日志
        self._setup_logging()
        
        # 初始化数据库表
        self._init_task_table()
        
        # 初始化调度器
        self._init_scheduler()
        
    def _setup_logging(self):
        """配置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('task_manager.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _init_task_table(self):
        """初始化任务表"""
        try:
            if not table_exists(self.db_path, 'tasks'):
                task_table_sql = """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE NOT NULL,           -- APScheduler任务ID
                    task_type TEXT NOT NULL,                -- 任务类型：live_reminder、follow_task等
                    room_id INTEGER,                        -- 关联的直播间ID
                    room_ids TEXT,                          -- 多个直播间ID（JSON格式）
                    room_names TEXT,                        -- 多个直播间名称（JSON格式）
                    run_time TEXT NOT NULL,                 -- 执行时间
                    create_time TEXT NOT NULL,              -- 创建时间
                    status INTEGER DEFAULT 0,               -- 状态：0=等待触发，1=已失效
                    execution_status TEXT DEFAULT 'pending', -- 执行状态：pending/executing/completed/failed/error/partial_success
                    last_execution_time TEXT,               -- 最后执行时间
                    retry_count INTEGER DEFAULT 0,         -- 重试次数
                    remark TEXT,                            -- 备注信息
                    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
                )
                """
                
                result = create_table(db_path=self.db_path, sql_statement=task_table_sql)
                if result:
                    self.logger.info("✅ tasks 表创建成功")
                else:
                    self.logger.error("❌ tasks 表创建失败")
                    raise Exception("任务表创建失败")
            else:
                self.logger.info("ℹ️  tasks 表已存在，检查字段更新")
                
                # 检查是否需要添加新字段
                self._check_and_add_task_columns()
                
        except Exception as e:
            self.logger.error(f"❌ 初始化任务表失败: {str(e)}")
            raise e
            
    def _check_and_add_task_columns(self):
        """检查并添加新的tasks表字段"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取当前表结构
            cursor.execute("PRAGMA table_info(tasks)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # 需要添加的新字段
            new_columns = [
                ('room_ids', 'TEXT'),
                ('room_names', 'TEXT'), 
                ('execution_status', 'TEXT DEFAULT "pending"'),
                ('last_execution_time', 'TEXT'),
                ('retry_count', 'INTEGER DEFAULT 0')
            ]
            
            # 添加缺失的字段
            for column_name, column_type in new_columns:
                if column_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE tasks ADD COLUMN {column_name} {column_type}")
                        self.logger.info(f"✅ 添加字段: {column_name}")
                    except sqlite3.Error as e:
                        self.logger.warning(f"⚠️ 添加字段 {column_name} 失败: {str(e)}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ 检查表字段失败: {str(e)}")
            
    def _init_scheduler(self):
        """初始化APScheduler调度器"""
        try:
            # 配置作业存储
            jobstores = {
                'default': SQLAlchemyJobStore(url=f'sqlite:///{self.db_path}')
            }
            
            # 配置执行器
            executors = {
                'default': ThreadPoolExecutor(20),
            }
            
            # 作业默认设置
            job_defaults = {
                'coalesce': False,
                'max_instances': 3
            }
            
            # 创建调度器
            self.scheduler = BackgroundScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone='Asia/Shanghai'
            )
            
            # 添加事件监听器
            self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)
            
            self.logger.info("✅ APScheduler调度器初始化成功")
            
        except Exception as e:
            self.logger.error(f"❌ 调度器初始化失败: {str(e)}")
            raise e
            
    def _job_listener(self, event):
        """任务执行事件监听器"""
        if event.exception:
            self.logger.error(f"❌ 任务执行失败: {event.job_id}, 异常: {event.exception}")
        else:
            self.logger.info(f"✅ 任务执行成功: {event.job_id}")
            
    def start(self):
        """启动任务管理器"""
        try:
            if not self.is_running:
                self.scheduler.start()
                self.is_running = True
                self.logger.info("🚀 任务管理器启动成功")
                
                # 🔥 新增：启动时清理过期任务
                self.logger.info("🧹 启动时清理过期任务...")
                cleanup_count = self.cleanup_expired_tasks()
                if cleanup_count > 0:
                    self.logger.info(f"✅ 启动时清理了 {cleanup_count} 个过期任务")
                else:
                    self.logger.info("✅ 启动时无过期任务需要清理")
                
                # 🔥 修复：清理APScheduler中的残留job
                self._cleanup_orphaned_jobs()
                
                # 🔥 修复：强制清理特定的问题任务
                self._force_remove_problematic_job('live_reminder_74_1757142120')
                
                # 加载数据库中的现有任务
                self._load_existing_tasks()
            else:
                self.logger.warning("⚠️ 任务管理器已经在运行")
                
        except Exception as e:
            self.logger.error(f"❌ 任务管理器启动失败: {str(e)}")
            raise e
            
    def stop(self):
        """停止任务管理器"""
        try:
            if self.is_running:
                self.scheduler.shutdown()
                self.is_running = False
                self.logger.info("🛑 任务管理器已停止")
            else:
                self.logger.warning("⚠️ 任务管理器未在运行")
                
        except Exception as e:
            self.logger.error(f"❌ 任务管理器停止失败: {str(e)}")
            
    def _load_existing_tasks(self):
        """从数据库加载现有的有效任务"""
        try:
            # 查询所有有效任务（status=0表示等待触发）
            # 🔥 修复：同时检查时间，避免重复处理过期任务
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            tasks = query_table(
                db_path=self.db_path,
                table_name='tasks',
                where='status = ? AND run_time >= ?',
                params=(0, current_time),  # 只加载未过期的有效任务
                order_by='create_time DESC'
            )
            
            loaded_count = 0
            for task in tasks:
                try:
                    # 🔥 修复：移除过期检查，因为SQL查询已经过滤了过期任务
                    run_time = datetime.fromisoformat(task['run_time'])
                        
                    # 检查调度器中是否已存在该任务
                    if self.scheduler.get_job(task['task_id']):
                        self.logger.info(f"ℹ️ 任务已存在于调度器中: {task['task_id']}")
                        continue
                        
                    # 重新添加任务到调度器
                    if task['task_type'] == 'live_reminder':
                        self._add_live_reminder_job(
                            task_id=task['task_id'],
                            room_id=task['room_id'],
                            run_time=run_time,
                            remark=task.get('remark', '')
                        )
                        loaded_count += 1
                    elif task['task_type'] == 'follow_task':
                        # 加载跟播任务
                        import json
                        
                        room_ids = json.loads(task.get('room_ids', '[]'))
                        room_names = json.loads(task.get('room_names', '[]'))
                        retry_count = task.get('retry_count', 0)
                        
                        self._add_follow_task_job(
                            task_id=task['task_id'],
                            room_ids=room_ids,
                            room_names=room_names,
                            run_time=run_time,
                            remark=task.get('remark', ''),
                            retry_count=retry_count
                        )
                        loaded_count += 1
                    elif task['task_type'] == 'test_follow_task':
                        # 加载测试跟播任务
                        import json
                        
                        room_ids = json.loads(task.get('room_ids', '[]'))
                        room_names = json.loads(task.get('room_names', '[]'))
                        
                        self._add_test_follow_task_job(
                            task_id=task['task_id'],
                            room_ids=room_ids,
                            room_names=room_names,
                            run_time=run_time,
                            remark=task.get('remark', '')
                        )
                        loaded_count += 1
                        
                except Exception as e:
                    self.logger.error(f"❌ 加载任务失败: {task['task_id']}, 错误: {str(e)}")
                    
            self.logger.info(f"📋 从数据库加载了 {loaded_count} 个有效任务")
            
        except Exception as e:
            self.logger.error(f"❌ 加载现有任务失败: {str(e)}")
            
    def add_live_reminder(self, room_id: int, run_time: datetime, remark: str = '') -> bool:
        """
        添加直播提醒任务
        
        Args:
            room_id: 直播间ID
            run_time: 执行时间
            remark: 备注信息
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 生成唯一的任务ID
            task_id = f"live_reminder_{room_id}_{int(run_time.timestamp())}"
            
            # 检查是否已存在相同的任务
            existing_task = self._get_task_by_id(task_id)
            if existing_task:
                self.logger.warning(f"⚠️ 任务已存在: {task_id}")
                return False
                
            # 添加任务到调度器
            self._add_live_reminder_job(task_id, room_id, run_time, remark)
            
            # 保存任务到数据库
            self._save_task_to_db(
                task_id=task_id,
                task_type='live_reminder',
                room_id=room_id,
                run_time=run_time,
                remark=remark
            )
            
            self.logger.info(f"✅ 成功添加直播提醒任务: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 添加直播提醒任务失败: {str(e)}")
            return False
    
    def add_follow_task(self, task_id: str = None, room_ids: List[int] = None, room_names: List[str] = None, 
                       run_time: datetime = None, remark: str = '', retry_count: int = 0) -> bool:
        """
        添加跟播任务
        
        Args:
            task_id: 任务ID（可选，如不提供则自动生成）
            room_ids: 直播间ID列表
            room_names: 直播间名称列表
            run_time: 执行时间（可选，如不提供则立即执行）
            remark: 备注信息
            retry_count: 重试次数
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 参数验证
            if not room_ids or not room_names:
                self.logger.error("❌ 直播间ID和名称列表不能为空")
                return False
                
            if len(room_ids) != len(room_names):
                self.logger.error("❌ 直播间ID和名称列表长度不匹配")
                return False
            
            # 生成任务ID
            if not task_id:
                timestamp = int(datetime.now().timestamp())
                room_ids_str = '_'.join(map(str, room_ids))
                task_id = f"follow_task_{room_ids_str}_{timestamp}"
            
            # 检查是否已存在相同的任务
            existing_task = self._get_task_by_id(task_id)
            if existing_task:
                self.logger.warning(f"⚠️ 任务已存在: {task_id}")
                return False
            
            # 确定执行时间
            if run_time is None:
                # 🔥 修复：从配置文件读取跟播任务延迟时间，不再立即执行
                config = loadTaskManagerConfig()
                delay_seconds = config.get('system_config', {}).get('intervals', {}).get('follow_task_retry', 60)
                run_time = datetime.now() + timedelta(seconds=delay_seconds)
                self.logger.info(f"⏰ 跟播任务将在{delay_seconds}秒后执行: {run_time.strftime('%H:%M:%S')}")
                
            # 添加任务到调度器
            self._add_follow_task_job(task_id, room_ids, room_names, run_time, remark, retry_count)
            
            # 保存任务到数据库
            self._save_follow_task_to_db(
                task_id=task_id,
                room_ids=room_ids,
                room_names=room_names,
                run_time=run_time,
                remark=remark,
                retry_count=retry_count
            )
            
            self.logger.info(f"✅ 成功添加跟播任务: {task_id} ({len(room_ids)}个直播间)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 添加跟播任务失败: {str(e)}")
            return False
    
    def add_retry_task(self, original_task_id: str, room_ids: List[int], room_names: List[str], 
                      retry_count: int, failure_reason: str = '', failed_rooms_str: str = '') -> bool:
        """
        添加重试任务（只创建一个跟播重试任务）
        
        Args:
            original_task_id: 原始任务ID
            room_ids: 直播间ID列表
            room_names: 直播间名称列表
            retry_count: 重试次数
            failure_reason: 失败原因
            failed_rooms_str: 失败直播间名称字符串
            
        Returns:
            bool: 是否添加成功
        """
        try:
            if not room_ids or not room_names:
                self.logger.error("❌ 直播间ID和名称列表不能为空")
                return False
                
            if len(room_ids) != len(room_names):
                self.logger.error("❌ 直播间ID和名称列表长度不匹配")
                return False
            
            # 计算重试时间
            retry_config = getTaskRetryConfig()
            retry_time = datetime.now() + timedelta(seconds=retry_config["follow_task_retry_interval"])
            
            # 构建失败原因说明
            if not failure_reason:
                failure_reason = "跟播失败：可能是微信状态、网络连接错误或直播间名称有误/未在直播"
            
            if not failed_rooms_str:
                failed_rooms_str = '、'.join(room_names[:3])
                if len(room_names) > 3:
                    failed_rooms_str += f'等{len(room_names)}个'
            
            # 创建重试跟播任务
            retry_task_id = f"{original_task_id}_retry_{retry_count}"
            follow_remark = f"跟播重试任务 - 第{retry_count}次重试\n原因：{failure_reason}\n失败直播间：{failed_rooms_str}\n说明：尝试重新跟播失败的直播间"
            
            follow_success = self.add_follow_task(
                task_id=retry_task_id,
                room_ids=room_ids,
                room_names=room_names,
                run_time=retry_time,
                remark=follow_remark,
                retry_count=retry_count
            )
            
            if follow_success:
                retry_interval = retry_config["follow_task_retry_interval"]
                self.logger.info(f"✅ 已创建跟播重试任务: {retry_task_id}，将在{retry_interval}秒后执行")
                return True
            else:
                self.logger.error("❌ 创建跟播重试任务失败")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 添加重试任务失败: {str(e)}")
            return False

    def add_immediate_follow_task(self, room_ids: List[int], room_names: List[str], remark: str = '') -> bool:
        """
        添加立即执行的跟播任务
        
        Args:
            room_ids: 直播间ID列表
            room_names: 直播间名称列表
            remark: 备注信息
            
        Returns:
            bool: 是否添加成功
        """
        return self.add_follow_task(
            room_ids=room_ids,
            room_names=room_names,
            run_time=None,  # 立即执行
            remark=remark
        )
    
    def add_test_follow_task(self, room_ids: List[int], room_names: List[str], remark: str = '') -> bool:
        """
        添加测试跟播任务（不实际发送，只测试话术输入）
        
        Args:
            room_ids: 直播间ID列表
            room_names: 直播间名称列表
            remark: 备注信息
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 参数验证
            if not room_ids or not room_names:
                self.logger.error("❌ 直播间ID和名称列表不能为空")
                return False
                
            if len(room_ids) != len(room_names):
                self.logger.error("❌ 直播间ID和名称列表长度不匹配")
                return False
            
            # 生成测试任务ID
            timestamp = int(datetime.now().timestamp())
            room_ids_str = '_'.join(map(str, room_ids))
            task_id = f"test_follow_task_{room_ids_str}_{timestamp}"
            
            # 检查是否已存在相同的任务
            existing_task = self._get_task_by_id(task_id)
            if existing_task:
                self.logger.warning(f"⚠️ 任务已存在: {task_id}")
                return False
            
            # 🔥 修复：从配置文件读取测试跟播任务延迟时间
            config = loadTaskManagerConfig()
            delay_seconds = config.get('system_config', {}).get('intervals', {}).get('follow_task_retry', 60)
            run_time = datetime.now() + timedelta(seconds=delay_seconds)
            self.logger.info(f"⏰ 测试跟播任务将在{delay_seconds}秒后执行: {run_time.strftime('%H:%M:%S')}")
                
            # 添加测试任务到调度器
            self._add_test_follow_task_job(task_id, room_ids, room_names, run_time, remark)
            
            # 保存任务到数据库
            self._save_test_follow_task_to_db(
                task_id=task_id,
                room_ids=room_ids,
                room_names=room_names,
                run_time=run_time,
                remark=remark
            )
            
            self.logger.info(f"✅ 成功添加测试跟播任务: {task_id} ({len(room_ids)}个直播间)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 添加测试跟播任务失败: {str(e)}")
            return False
    
    def register_danmu_task(self, task_id: str, run_time: datetime):
        """注册弹幕任务到调度器"""
        try:
            retry_config = getTaskRetryConfig()
            self.scheduler.add_job(
                func=execute_danmu_task,
                trigger=DateTrigger(run_date=run_time),
                id=task_id,
                args=[task_id, self.db_path],
                replace_existing=True,
                misfire_grace_time=retry_config["follow_task_retry_interval"] // 2  # 使用配置的一半作为容错时间
            )
            self.logger.info(f"✅ 弹幕任务已注册到调度器: {task_id} -> {run_time}")
            return True
        except Exception as e:
            self.logger.error(f"❌ 注册弹幕任务失败: {task_id}, 错误: {str(e)}")
            return False

    def _add_test_follow_task_job(self, task_id: str, room_ids: List[int], room_names: List[str], 
                                 run_time: datetime, remark: str):
        """添加测试跟播任务作业到调度器"""
        self.scheduler.add_job(
            func=execute_test_follow_task,  # 使用测试执行函数
            trigger=DateTrigger(run_date=run_time),
            id=task_id,
            args=[task_id, room_ids, room_names, self.db_path],
            replace_existing=True
        )
        
    def _save_test_follow_task_to_db(self, task_id: str, room_ids: List[int], room_names: List[str], 
                                    run_time: datetime, remark: str = ''):
        """保存测试跟播任务到数据库"""
        try:
            import json
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            run_time_str = run_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # 将ID和名称列表转换为JSON
            room_ids_json = json.dumps(room_ids)
            room_names_json = json.dumps(room_names, ensure_ascii=False)

            cursor.execute("""
                INSERT INTO tasks (task_id, task_type, room_ids, room_names, run_time, create_time, status, remark, retry_count)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?, 0)
            """, (task_id, 'test_follow_task', room_ids_json, room_names_json, run_time_str, create_time, remark))

            conn.commit()
            conn.close()

            self.logger.info(f"✅ 测试跟播任务已保存到数据库: {task_id}")

        except Exception as e:
            self.logger.error(f"❌ 保存测试跟播任务到数据库失败: {str(e)}")
            raise e
    
    def _add_follow_task_job(self, task_id: str, room_ids: List[int], room_names: List[str], 
                            run_time: datetime, remark: str, retry_count: int):
        """添加跟播任务作业到调度器"""
        self.scheduler.add_job(
            func=execute_follow_task,  # 使用全局函数
            trigger=DateTrigger(run_date=run_time),
            id=task_id,
            args=[task_id, room_ids, room_names, self.db_path, retry_count],
            replace_existing=True
        )
        
    def _save_follow_task_to_db(self, task_id: str, room_ids: List[int], room_names: List[str], 
                               run_time: datetime, remark: str = '', retry_count: int = 0):
        """保存跟播任务到数据库"""
        try:
            import json
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            run_time_str = run_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # 将ID和名称列表转换为JSON
            room_ids_json = json.dumps(room_ids)
            room_names_json = json.dumps(room_names, ensure_ascii=False)

            cursor.execute("""
                INSERT INTO tasks (task_id, task_type, room_ids, room_names, run_time, create_time, status, remark, retry_count)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
            """, (task_id, 'follow_task', room_ids_json, room_names_json, run_time_str, create_time, remark, retry_count))

            conn.commit()
            conn.close()

            self.logger.info(f"✅ 跟播任务已保存到数据库: {task_id}")

        except Exception as e:
            self.logger.error(f"❌ 保存跟播任务到数据库失败: {str(e)}")
            raise e
            
    def _add_live_reminder_job(self, task_id: str, room_id: int, run_time: datetime, remark: str):
        """添加直播提醒作业到调度器"""
        self.scheduler.add_job(
            func=execute_live_reminder_task,  # 使用全局函数而不是实例方法
            trigger=DateTrigger(run_date=run_time),
            id=task_id,
            args=[room_id, remark, self.db_path, task_id],  # 传递数据库路径和任务ID
            replace_existing=True
        )

    def _save_task_to_db(self, task_id: str, task_type: str, room_id: int, run_time: datetime, remark: str = ''):
        """保存任务到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            run_time_str = run_time.strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute("""
                INSERT INTO tasks (task_id, task_type, room_id, run_time, create_time, status, remark)
                VALUES (?, ?, ?, ?, ?, 0, ?)
            """, (task_id, task_type, room_id, run_time_str, create_time, remark))

            conn.commit()
            conn.close()

            self.logger.info(f"✅ 任务已保存到数据库: {task_id}")

        except Exception as e:
            self.logger.error(f"❌ 保存任务到数据库失败: {str(e)}")
            raise e

    def _get_task_by_id(self, task_id: str) -> Optional[Dict]:
        """根据任务ID获取任务信息"""
        try:
            tasks = query_table(
                db_path=self.db_path,
                table_name='tasks',
                where='task_id = ?',
                params=(task_id,)
            )

            return tasks[0] if tasks else None

        except Exception as e:
            self.logger.error(f"❌ 获取任务信息失败: {str(e)}")
            return None

    def _update_task_status(self, task_id: str, status: int):
        """更新任务状态"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 🔥 修复：先检查任务是否存在
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE task_id = ?", (task_id,))
            task_exists = cursor.fetchone()[0] > 0
            
            if not task_exists:
                conn.close()
                self.logger.warning(f"⚠️ 尝试更新不存在的任务: {task_id}")
                return

            cursor.execute("""
                UPDATE tasks SET status = ? WHERE task_id = ?
            """, (status, task_id))

            conn.commit()
            conn.close()

            self.logger.info(f"✅ 任务状态已更新: {task_id} -> {status}")

        except Exception as e:
            self.logger.error(f"❌ 更新任务状态失败: {str(e)}")

    def remove_task(self, task_id: str) -> bool:
        """
        移除任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否移除成功
        """
        try:
            # 🔥 修复：先检查任务是否存在
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE task_id = ?", (task_id,))
            task_exists = cursor.fetchone()[0] > 0
            conn.close()
            
            if not task_exists:
                self.logger.warning(f"⚠️ 尝试移除不存在的任务: {task_id}")
                # 仍然尝试从调度器中移除（可能存在孤儿job）
                if self.scheduler.get_job(task_id):
                    self.scheduler.remove_job(task_id)
                    self.logger.info(f"✅ 已从调度器移除孤儿job: {task_id}")
                return True  # 不存在的任务视为移除成功
            
            # 从调度器中移除任务
            if self.scheduler.get_job(task_id):
                self.scheduler.remove_job(task_id)
                self.logger.info(f"✅ 已从调度器移除任务: {task_id}")

            # 从数据库中标记为失效
            self._update_task_status(task_id, 1)  # 1=已失效

            return True

        except Exception as e:
            self.logger.error(f"❌ 移除任务失败: {str(e)}")
            return False

    def get_active_tasks(self) -> List[Dict]:
        """获取所有活跃任务"""
        try:
            tasks = query_table(
                db_path=self.db_path,
                table_name='tasks',
                where='status = ?',
                params=(0,),  # 0=等待触发
                order_by='create_time DESC'
            )

            # 添加调度器状态信息
            for task in tasks:
                scheduler_job = self.scheduler.get_job(task['task_id'])
                task['scheduler_status'] = 'active' if scheduler_job else 'missing'
                if scheduler_job:
                    task['next_run_time'] = scheduler_job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if scheduler_job.next_run_time else None

            return tasks

        except Exception as e:
            self.logger.error(f"❌ 获取活跃任务失败: {str(e)}")
            return []

    def sync_tasks_with_live_times(self):
        """
        同步任务与直播时间表
        检查time_of_live表中的待开播时间，自动创建对应的提醒任务
        """
        try:
            # 查询所有待开播的直播时间
            live_times = query_table(
                db_path=self.db_path,
                table_name='time_of_live',
                where='status = 0',  # 0=等待开播
                order_by='live_time ASC'
            )

            sync_count = 0
            for live_time in live_times:
                try:
                    room_id = live_time['room_id']
                    live_time_str = live_time['live_time']
                    remark = live_time.get('remark', '')

                    # 解析时间
                    run_time = datetime.fromisoformat(live_time_str)

                    # 检查时间是否已过期
                    if run_time <= datetime.now():
                        self.logger.info(f"⏰ 直播时间已过期，跳过: {live_time_str}")
                        continue

                    # 生成任务ID
                    task_id = f"live_reminder_{room_id}_{int(run_time.timestamp())}"

                    # 检查任务是否已存在（status=0表示等待触发）
                    existing_task = self._get_task_by_id(task_id)
                    if existing_task and existing_task['status'] == 0:  # 0=等待触发
                        continue

                    # 创建提醒任务
                    success = self.add_live_reminder(room_id, run_time, remark)
                    if success:
                        sync_count += 1

                except Exception as e:
                    self.logger.error(f"❌ 同步单个直播时间失败: {str(e)}")

            self.logger.info(f"📋 同步完成，创建了 {sync_count} 个新任务")
            return sync_count

        except Exception as e:
            self.logger.error(f"❌ 同步任务失败: {str(e)}")
            return 0

    def cleanup_expired_tasks(self):
        """清理过期任务"""
        try:
            # 查询所有过期的活跃任务
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            expired_tasks = query_table(
                db_path=self.db_path,
                table_name='tasks',
                where='status = 1 AND run_time < ?',
                params=(current_time,)
            )

            cleanup_count = 0
            for task in expired_tasks:
                try:
                    # 🔥 修复：彻底清理过期任务，包括调度器job和数据库记录
                    task_id = task['task_id']
                    
                    # 1. 从APScheduler中移除job（如果存在）
                    if self.scheduler.get_job(task_id):
                        self.scheduler.remove_job(task_id)
                        self.logger.info(f"🗑️ 已从调度器移除job: {task_id}")
                    
                    # 2. 从数据库中删除任务记录
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
                    conn.commit()
                    conn.close()
                    self.logger.info(f"🗑️ 已删除过期任务记录: {task_id}")
                    cleanup_count += 1

                except Exception as e:
                    self.logger.error(f"❌ 清理单个过期任务失败: {task['task_id']}, 错误: {str(e)}")

            self.logger.info(f"🧹 清理完成，处理了 {cleanup_count} 个过期任务")
            return cleanup_count

        except Exception as e:
            self.logger.error(f"❌ 清理过期任务失败: {str(e)}")
            return 0
    
    def _cleanup_orphaned_jobs(self):
        """清理APScheduler中没有对应数据库记录的孤儿job"""
        try:
            self.logger.info("🧹 清理APScheduler中的孤儿job...")
            
            # 获取所有APScheduler中的job
            scheduler_jobs = self.scheduler.get_jobs()
            
            # 获取数据库中所有有效任务的ID
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            valid_task_ids = set()
            
            try:
                results = cursor.execute("SELECT task_id FROM tasks WHERE status = 0").fetchall()
                valid_task_ids = {row[0] for row in results}
            except:
                pass
            
            conn.close()
            
            orphaned_count = 0
            for job in scheduler_jobs:
                if job.id not in valid_task_ids:
                    self.scheduler.remove_job(job.id)
                    self.logger.info(f"🗑️ 删除孤儿job: {job.id}")
                    orphaned_count += 1
            
            if orphaned_count > 0:
                self.logger.info(f"✅ 清理了 {orphaned_count} 个孤儿job")
            else:
                self.logger.info("✅ 无孤儿job需要清理")
                
        except Exception as e:
            self.logger.error(f"❌ 清理孤儿job失败: {str(e)}")
    
    def _force_remove_problematic_job(self, task_id: str):
        """强制移除问题任务"""
        try:
            # 从APScheduler中移除
            if self.scheduler.get_job(task_id):
                self.scheduler.remove_job(task_id)
                self.logger.info(f"🔥 强制删除问题job: {task_id}")
            
            # 从数据库中删除（如果存在）
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            cursor.execute("DELETE FROM apscheduler_jobs WHERE id = ?", (task_id,))
            conn.commit()
            conn.close()
            
            self.logger.info(f"🔥 强制清理问题任务完成: {task_id}")
            
        except Exception as e:
            self.logger.error(f"❌ 强制清理问题任务失败: {str(e)}")
    
    def get_retry_tasks(self) -> List[Dict]:
        """获取所有重试任务"""
        try:
            tasks = query_table(
                db_path=self.db_path,
                table_name='tasks',
                where='status = 1 AND retry_count > 0',
                order_by='create_time DESC'
            )
            
            return tasks
            
        except Exception as e:
            self.logger.error(f"❌ 获取重试任务失败: {str(e)}")
            return []
    
    def cancel_retry_tasks(self, original_task_id: str) -> bool:
        """取消指定任务的所有重试任务"""
        try:
            # 查找所有相关的重试任务
            retry_tasks = query_table(
                db_path=self.db_path,
                table_name='tasks',
                where='task_id LIKE ? AND status = 1',
                params=(f"{original_task_id}_retry_%",)
            )
            
            cancel_count = 0
            for task in retry_tasks:
                task_id = task['task_id']
                
                # 从调度器中移除
                if self.scheduler.get_job(task_id):
                    self.scheduler.remove_job(task_id)
                
                # 标记为失效
                self._update_task_status(task_id, 1)  # 1=已失效
                cancel_count += 1
            
            self.logger.info(f"✅ 已取消 {cancel_count} 个重试任务")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 取消重试任务失败: {str(e)}")
            return False
    
    def get_task_execution_stats(self) -> Dict:
        """获取任务执行统计信息"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # 总任务数
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE task_type = 'follow_task'")
            stats['total_follow_tasks'] = cursor.fetchone()[0]
            
            # 各状态任务数
            cursor.execute("""
                SELECT execution_status, COUNT(*) 
                FROM tasks 
                WHERE task_type = 'follow_task' 
                GROUP BY execution_status
            """)
            
            status_counts = {}
            for row in cursor.fetchall():
                status_counts[row[0] or 'pending'] = row[1]
            
            stats['status_counts'] = status_counts
            
            # 重试任务数
            cursor.execute("""
                SELECT COUNT(*) FROM tasks 
                WHERE task_type = 'follow_task' AND retry_count > 0
            """)
            stats['retry_tasks'] = cursor.fetchone()[0]
            
            # 成功率
            total = stats['total_follow_tasks']
            completed = status_counts.get('completed', 0)
            partial = status_counts.get('partial_success', 0)
            
            if total > 0:
                stats['success_rate'] = round((completed + partial * 0.5) / total * 100, 2)
            else:
                stats['success_rate'] = 0
            
            conn.close()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ 获取任务统计失败: {str(e)}")
            return {}
    
    def add_image_recognition_task(self, task_id: str, room_id: int, room_name: str, 
                                 run_time: datetime, interval_seconds: int, 
                                 remark: str = '', test_mode: bool = True) -> bool:
        """
        添加图像识别任务
        
        Args:
            task_id: 任务ID
            room_id: 直播间ID
            room_name: 直播间名称
            run_time: 执行时间
            interval_seconds: 间隔时间（秒）
            remark: 备注信息
            test_mode: 是否为测试模式
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 参数验证
            if not task_id or not room_id or not room_name:
                self.logger.error("❌ 任务参数不能为空")
                return False
            
            # 检查是否已存在相同的任务
            existing_task = self._get_task_by_id(task_id)
            if existing_task:
                self.logger.warning(f"⚠️ 图像识别任务已存在: {task_id}")
                return False
            
            # 添加任务到调度器
            self._add_image_recognition_job(
                task_id=task_id,
                room_id=room_id,
                room_name=room_name,
                run_time=run_time,
                interval_seconds=interval_seconds,
                remark=remark,
                test_mode=test_mode
            )
            
            # 保存任务到数据库
            self._save_image_recognition_task_to_db(
                task_id=task_id,
                room_id=room_id,
                room_name=room_name,
                run_time=run_time,
                interval_seconds=interval_seconds,
                remark=remark,
                test_mode=test_mode
            )
            
            self.logger.info(f"✅ 成功添加图像识别任务: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 添加图像识别任务失败: {str(e)}")
            return False
    
    def _add_image_recognition_job(self, task_id: str, room_id: int, room_name: str, 
                                 run_time: datetime, interval_seconds: int, 
                                 remark: str, test_mode: bool):
        """添加图像识别任务作业到调度器"""
        from datetime import timedelta
        
        # 导入全局执行函数
        from follwRoom import executeImageRecognitionTask
        
        self.scheduler.add_job(
            func=executeImageRecognitionTask,
            trigger='date',
            run_date=run_time,
            id=task_id,
            args=[task_id, room_id, room_name, interval_seconds, test_mode, self.db_path],
            replace_existing=True
        )
        
    def _save_image_recognition_task_to_db(self, task_id: str, room_id: int, room_name: str, 
                                         run_time: datetime, interval_seconds: int, 
                                         remark: str, test_mode: bool):
        """保存图像识别任务到数据库"""
        try:
            import json
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            run_time_str = run_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # 创建任务数据
            task_data = {
                'room_id': room_id,
                'interval_seconds': interval_seconds,
                'test_mode': test_mode
            }
            
            task_data_json = json.dumps(task_data, ensure_ascii=False)

            cursor.execute("""
                INSERT INTO tasks (task_id, task_type, room_ids, room_names, run_time, create_time, status, remark, retry_count, task_data)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?, 0, ?)
            """, (task_id, 'image_recognition', json.dumps([room_id]), json.dumps([room_name], ensure_ascii=False), run_time_str, create_time, remark, task_data_json))

            conn.commit()
            conn.close()

            self.logger.info(f"✅ 图像识别任务已保存到数据库: {task_id}")

        except Exception as e:
            self.logger.error(f"❌ 保存图像识别任务到数据库失败: {str(e)}")
            raise e

    def _check_all_danmu_tasks_completed(self, room_id: int, db_path: str) -> bool:
        """检查指定直播间的所有弹幕任务是否都已完成"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 查询该直播间的所有弹幕任务
            cursor.execute("""
                SELECT COUNT(*) as total, 
                       SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as completed
                FROM tasks 
                WHERE room_id = ? AND task_type = 'danmu_task'
            """, (room_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] > 0:  # 有弹幕任务
                total_tasks = result[0]
                completed_tasks = result[1] or 0
                
                print(f"📊 [TASK_CHECK] 直播间 {room_id} 弹幕任务统计:")
                print(f"📊 [TASK_CHECK]   - 总任务数: {total_tasks}")
                print(f"📊 [TASK_CHECK]   - 已完成: {completed_tasks}")
                print(f"📊 [TASK_CHECK]   - 未完成: {total_tasks - completed_tasks}")
                
                is_completed = completed_tasks == total_tasks
                print(f"📊 [TASK_CHECK]   - 全部完成: {'✅ 是' if is_completed else '❌ 否'}")
                
                return is_completed
            else:
                print(f"📊 [TASK_CHECK] 直播间 {room_id} 没有弹幕任务，认为已完成")
                return True
                
        except Exception as e:
            print(f"❌ [TASK_CHECK] 检查任务完成状态失败: {e}")
            return False

    def _check_all_danmu_tasks_completed_with_stats(self, room_id: int, db_path: str):
        """检查指定直播间的所有弹幕任务是否都已完成，并返回统计信息"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 查询该直播间的所有弹幕任务
            cursor.execute("""
                SELECT COUNT(*) as total, 
                       SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as completed
                FROM tasks 
                WHERE room_id = ? AND task_type = 'danmu_task'
            """, (room_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] > 0:  # 有弹幕任务
                total_tasks = result[0]
                completed_tasks = result[1] or 0
                
                stats = {
                    'total': total_tasks,
                    'completed': completed_tasks,
                    'remaining': total_tasks - completed_tasks
                }
                
                print(f"📊 [TASK_STATS] 直播间 {room_id} 弹幕发送统计:")
                print(f"📊 [TASK_STATS]   - 总任务数: {total_tasks}")
                print(f"📊 [TASK_STATS]   - 已完成: {completed_tasks}")
                print(f"📊 [TASK_STATS]   - 未完成: {total_tasks - completed_tasks}")
                
                is_completed = completed_tasks == total_tasks
                print(f"📊 [TASK_STATS]   - 全部完成: {'✅ 是' if is_completed else '❌ 否'}")
                
                return is_completed, stats
            else:
                stats = {'total': 0, 'completed': 0, 'remaining': 0}
                print(f"📊 [TASK_STATS] 直播间 {room_id} 没有弹幕任务，认为已完成")
                return True, stats
                
        except Exception as e:
            print(f"❌ [TASK_STATS] 检查任务完成状态失败: {e}")
            stats = {'total': 0, 'completed': 0, 'remaining': 0}
            return False, stats


# 全局任务管理器实例
_task_manager_instance = None


def get_task_manager() -> TaskManager:
    """获取全局任务管理器实例（单例模式）"""
    global _task_manager_instance
    if _task_manager_instance is None:
        _task_manager_instance = TaskManager()
    return _task_manager_instance


def init_task_manager() -> bool:
    """初始化任务管理器"""
    try:
        task_manager = get_task_manager()
        task_manager.start()

        # 同步现有的直播时间
        task_manager.sync_tasks_with_live_times()

        # 清理过期任务
        task_manager.cleanup_expired_tasks()

        return True

    except Exception as e:
        print(f"❌ 初始化任务管理器失败: {str(e)}")
        return False


def stop_task_manager():
    """停止任务管理器"""
    global _task_manager_instance
    if _task_manager_instance:
        _task_manager_instance.stop()
        _task_manager_instance = None


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试任务管理器...")

    # 初始化
    success = init_task_manager()
    if success:
        print("✅ 任务管理器初始化成功")

        # 获取活跃任务
        task_manager = get_task_manager()
        tasks = task_manager.get_active_tasks()
        print(f"📋 当前活跃任务数: {len(tasks)}")

        # 停止
        stop_task_manager()
        print("🛑 任务管理器已停止")
    else:
        print("❌ 任务管理器初始化失败")
