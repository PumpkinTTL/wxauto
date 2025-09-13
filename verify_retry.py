#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证重试任务是否真的执行
"""

import sys
import os
import time
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_retry():
    print("🔍 验证重试任务执行")
    
    # 1. 启动任务管理器
    from task_manager import get_task_manager
    task_manager = get_task_manager()
    
    if not task_manager.is_running:
        task_manager.start()
    
    print(f"📊 任务管理器状态: {'运行中' if task_manager.is_running else '未运行'}")
    
    # 2. 检查活跃任务
    active_tasks = task_manager.get_active_tasks()
    retry_tasks = [t for t in active_tasks if 'retry' in t.get('task_id', '')]
    
    print(f"📋 活跃任务总数: {len(active_tasks)}")
    print(f"🔄 重试任务数: {len(retry_tasks)}")
    
    if retry_tasks:
        for task in retry_tasks:
            task_id = task.get('task_id')
            run_time = task.get('run_time')
            status = task.get('status')
            
            print(f"\n📋 重试任务: {task_id}")
            print(f"   执行时间: {run_time}")
            print(f"   状态: {status} ({'等待触发' if status == 0 else '已触发'})")
            
            # 检查执行时间
            try:
                exec_time = datetime.fromisoformat(run_time)
                now = datetime.now()
                diff = (exec_time - now).total_seconds()
                
                if diff < 0:
                    print(f"   ⏰ 已过期 {abs(diff):.0f} 秒")
                    print(f"   🔧 尝试手动触发任务...")
                    
                    # 手动执行重试任务
                    from task_manager import execute_follow_task
                    import json
                    
                    room_ids = json.loads(task.get('room_ids', '[72]'))
                    room_names = json.loads(task.get('room_names', '["哈利路亚"]'))
                    
                    print(f"   🎯 手动执行重试任务: {room_ids} - {room_names}")
                    execute_follow_task(task_id, room_ids, room_names, 'system.db', retry_count=1)
                    
                else:
                    print(f"   ⏰ 还有 {diff:.0f} 秒执行")
                    
            except Exception as e:
                print(f"   ❌ 时间解析失败: {str(e)}")
    
    # 3. 手动创建一个新的重试任务进行测试
    print(f"\n🧪 创建新的重试任务测试")
    
    test_time = datetime.now() + timedelta(seconds=5)
    test_task_id = f"test_retry_{int(test_time.timestamp())}"
    
    success = task_manager.add_follow_task(
        task_id=test_task_id,
        room_ids=[72],
        room_names=["哈利路亚"],
        run_time=test_time,
        remark="手动测试重试任务 - 5秒后执行",
        retry_count=1
    )
    
    if success:
        print(f"✅ 测试重试任务创建成功: {test_task_id}")
        print(f"⏰ 将在5秒后执行，请等待...")
        
        # 等待执行
        for i in range(8):
            print(f"倒计时... {8-i} 秒", end='\r')
            time.sleep(1)
        print()
        
        print(f"✅ 重试任务应该已经执行完成")
    else:
        print(f"❌ 测试重试任务创建失败")

if __name__ == "__main__":
    verify_retry()