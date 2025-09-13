#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整任务管理系统演示脚本
展示从直播提醒、自动跟播到任务日志管理的完整流程
"""

import sys
import os
import time
from datetime import datetime, timedelta

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_complete_workflow():
    """演示完整的任务管理工作流程"""
    print("🚀 完整任务管理系统演示")
    print("=" * 60)
    
    try:
        # 1. 初始化系统
        print("\n🔧 步骤1: 初始化任务管理系统")
        from task_manager import get_task_manager
        from apis import API
        
        task_manager = get_task_manager()
        if not task_manager.is_running:
            task_manager.start()
        
        api = API()
        print("✅ 任务管理器已启动")
        
        # 2. 创建直播提醒任务
        print("\n⏰ 步骤2: 创建直播提醒任务")
        
        # 设置5分钟后的提醒
        reminder_time = datetime.now() + timedelta(minutes=5)
        
        success = task_manager.add_live_reminder(
            room_id=70,
            run_time=reminder_time,
            remark="演示直播提醒 - 5分钟后自动跟播"
        )
        
        if success:
            print(f"✅ 直播提醒已设置: {reminder_time.strftime('%H:%M:%S')}")
            print("💡 提醒倒计时结束后将自动创建跟播任务")
        
        # 3. 立即创建跟播任务
        print("\n🎯 步骤3: 创建立即跟播任务")
        
        follow_success = task_manager.add_immediate_follow_task(
            room_ids=[70],
            room_names=["参半牙膏工厂店"],
            remark="演示立即跟播任务"
        )
        
        if follow_success:
            print("✅ 立即跟播任务已创建")
        
        # 4. 创建测试跟播任务
        print("\n🧪 步骤4: 创建测试跟播任务（仅测试，不实际发送）")
        
        test_follow_data = [
            {"id": 70, "name": "参半牙膏工厂店", "platform": "wechat"}
        ]
        
        test_result = api.start_test_follow(test_follow_data)
        if test_result.get('success'):
            print("✅ 测试跟播任务已创建")
            print("💡 将进入直播间测试所有话术，每7秒切换一次")
        
        # 5. 等待任务执行
        print("\n⏳ 步骤5: 等待任务执行（10秒）")
        for i in range(10):
            print(f"等待中... {10-i} 秒", end='\r')
            time.sleep(1)
        print()
        
        # 6. 查看任务状态
        print("\n📊 步骤6: 查看任务执行状态")
        
        task_list_result = api.get_task_list()
        if task_list_result.get('success'):
            tasks = task_list_result.get('data', [])
            active_tasks = [task for task in tasks if task.get('status') == 1]
            
            print(f"📋 当前活跃任务: {len(active_tasks)} 个")
            
            for task in active_tasks[-5:]:  # 显示最新的5个任务
                print(f"   - {task.get('task_type')} | {task.get('remark', '无备注')} | {task.get('create_time')}")
        
        # 7. 查看任务日志
        print("\n📝 步骤7: 查看任务执行日志")
        
        log_result = api.get_task_logs(10)
        if log_result.get('success'):
            logs = log_result.get('data', [])
            
            print(f"📄 最近任务日志: {len(logs)} 条")
            
            for log in logs[-5:]:  # 显示最新的5条日志
                status_text = "✅ 成功" if log.get('status') == 1 else "❌ 失败"
                print(f"   {status_text} | {log.get('message', '无消息')} | {log.get('execution_time')}")
        
        # 8. 演示任务失效功能
        print("\n❌ 步骤8: 演示任务失效功能")
        
        if active_tasks:
            # 选择第一个任务进行失效
            task_to_invalidate = active_tasks[0]
            task_id = task_to_invalidate.get('task_id')
            
            invalidate_result = api.invalidate_task(task_id)
            if invalidate_result.get('success'):
                print(f"✅ 任务已失效: {task_id}")
                print("💡 用户可以手动使不需要的任务失效")
        
        # 9. 功能总结
        print("\n🎯 步骤9: 系统功能总结")
        
        print("✅ 完整任务管理系统已演示完成！")
        print("\n📌 核心功能:")
        print("   1. ✅ 直播提醒 → 自动跟播链路")
        print("   2. ✅ 立即跟播任务")
        print("   3. ✅ 测试跟播（话术测试，不实际发送）")
        print("   4. ✅ 任务状态检查（防止重复执行）")
        print("   5. ✅ 详细任务日志记录")
        print("   6. ✅ 用户手动失效任务")
        print("   7. ✅ 重试机制（失败自动重试）")
        print("   8. ✅ 可视化界面（前端管理）")
        
        print("\n💡 改进的功能:")
        print("   - 🔧 修复了liveEnd函数逻辑错误")
        print("   - 📝 增强了失败原因记录（微信状态、网络、直播间名称等）")
        print("   - 🎯 实现了话术测试功能（7秒间隔切换）")
        print("   - 🗄️ 创建了task_log表进行日志管理")
        print("   - 🖥️ 添加了任务管理可视化界面")
        
        return True
        
    except Exception as e:
        print(f"❌ 演示过程出现异常: {str(e)}")
        return False

def show_system_architecture():
    """展示系统架构"""
    print("\n🏗️ 系统架构图")
    print("=" * 60)
    print("""
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   前端界面      │    │   API接口层     │    │   任务管理器    │
    │  (Vue + El)     │◄──►│  (Flask)        │◄──►│ (APScheduler)   │
    │                 │    │                 │    │                 │
    │ • 任务列表      │    │ • 任务CRUD      │    │ • 任务调度      │
    │ • 日志查看      │    │ • 日志查询      │    │ • 状态管理      │
    │ • 失效控制      │    │ • 状态控制      │    │ • 重试机制      │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
            │                       │                       │
            └───────────────────────┼───────────────────────┘
                                    │
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   SQLite数据库  │    │   跟播执行器    │    │   通知系统      │
    │                 │    │                 │    │                 │
    │ • tasks表       │◄──►│ • 微信自动化    │◄──►│ • 桌面通知      │
    │ • task_log表    │    │ • 话术发送      │    │ • 状态反馈      │
    │ • 状态管理      │    │ • 测试模式      │    │ • 错误提示      │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
    """)
    
    print("\n🔄 任务流程:")
    print("1. 用户创建直播提醒 → 2. 倒计时结束自动触发跟播")
    print("3. 检查任务状态 → 4. 执行跟播/测试 → 5. 记录日志")
    print("6. 失败自动重试 → 7. 用户可视化管理")

def main():
    """主函数"""
    print("🌟 完整任务管理系统演示程序")
    print("📝 展示从直播提醒到跟播执行的完整自动化流程")
    print()
    
    # 显示系统架构
    show_system_architecture()
    
    # 执行完整演示
    if demo_complete_workflow():
        print("\n🎉 演示完成！系统运行正常！")
        print("\n📖 使用指南:")
        print("   - 浏览器访问: http://localhost:5000/follow_wechat")
        print("   - 查看任务管理和日志界面")
        print("   - 创建跟播任务和测试任务")
        print("   - 监控任务执行状态")
        
        return True
    else:
        print("\n⚠️ 演示过程中遇到问题，请检查系统配置")
        return False

if __name__ == "__main__":
    main()