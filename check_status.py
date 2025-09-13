#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库状态检查脚本
用于检查 tasks 表和 time_of_live 表的状态数据
"""

import sqlite3
from datetime import datetime

def check_database_status():
    """检查数据库状态"""
    try:
        print("🔍 检查数据库状态...")
        print("=" * 60)
        
        conn = sqlite3.connect('system.db')
        cursor = conn.cursor()
        
        # 检查 tasks 表状态分布
        print("\n📋 Tasks 表状态分布:")
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM tasks 
            GROUP BY status 
            ORDER BY status
        """)
        
        task_status_results = cursor.fetchall()
        for status, count in task_status_results:
            status_text = "等待触发" if status == 0 else "已失效" if status == 1 else f"未知状态({status})"
            print(f"  状态 {status} ({status_text}): {count} 条记录")
        
        # 检查最近的 tasks 记录
        print("\n📝 最近5条 Tasks 记录:")
        cursor.execute("""
            SELECT task_id, task_type, status, create_time, remark
            FROM tasks 
            ORDER BY create_time DESC 
            LIMIT 5
        """)
        
        recent_tasks = cursor.fetchall()
        for task_id, task_type, status, create_time, remark in recent_tasks:
            status_text = "等待触发" if status == 0 else "已失效" if status == 1 else f"未知({status})"
            print(f"  {task_id[:30]}... | {task_type} | 状态:{status}({status_text}) | {create_time} | {remark}")
        
        # 检查 time_of_live 表状态分布
        print("\n🎬 Time_of_live 表状态分布:")
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM time_of_live 
            GROUP BY status 
            ORDER BY status
        """)
        
        live_status_results = cursor.fetchall()
        for status, count in live_status_results:
            status_text = "等待开播" if status == 0 else "已开播" if status == 1 else f"未知状态({status})"
            print(f"  状态 {status} ({status_text}): {count} 条记录")
        
        # 检查最近的 time_of_live 记录
        print("\n📅 最近5条 Time_of_live 记录:")
        cursor.execute("""
            SELECT t.room_id, r.name, t.live_time, t.status, t.create_time, t.remark
            FROM time_of_live t
            LEFT JOIN rooms r ON t.room_id = r.id
            ORDER BY t.create_time DESC 
            LIMIT 5
        """)
        
        recent_lives = cursor.fetchall()
        for room_id, room_name, live_time, status, create_time, remark in recent_lives:
            status_text = "等待开播" if status == 0 else "已开播" if status == 1 else f"未知({status})"
            room_display = room_name if room_name else f"ID:{room_id}"
            print(f"  {room_display} | {live_time} | 状态:{status}({status_text}) | {create_time} | {remark}")
        
        # 检查是否有状态不一致的问题
        print("\n⚠️  状态一致性检查:")
        cursor.execute("""
            SELECT COUNT(*) FROM tasks WHERE status NOT IN (0, 1)
        """)
        invalid_task_status = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM time_of_live WHERE status NOT IN (0, 1)
        """)
        invalid_live_status = cursor.fetchone()[0]
        
        if invalid_task_status > 0:
            print(f"  ❌ Tasks表中发现 {invalid_task_status} 条无效状态记录")
        else:
            print(f"  ✅ Tasks表状态正常")
            
        if invalid_live_status > 0:
            print(f"  ❌ Time_of_live表中发现 {invalid_live_status} 条无效状态记录")
        else:
            print(f"  ✅ Time_of_live表状态正常")
        
        conn.close()
        
        print("\n📊 状态定义说明:")
        print("  Tasks表: 0=等待触发, 1=已失效")
        print("  Time_of_live表: 0=等待开播, 1=已开播")
        print("\n✅ 数据库状态检查完成")
        
    except Exception as e:
        print(f"❌ 检查数据库状态失败: {str(e)}")

if __name__ == "__main__":
    check_database_status()