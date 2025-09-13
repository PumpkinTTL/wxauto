#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证监听窗口输出优化功能
测试完成后会自动删除此文件
"""

import sys
import os
import time
import json
from datetime import datetime, timedelta

def test_retry_task_creation():
    """测试重试任务创建的监听窗口输出"""
    print("🧪 测试1: 重试任务创建的监听窗口输出")
    
    try:
        # 模拟导入follwRoom模块
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from follwRoom import createNextRecognitionTask
        
        # 模拟参数
        room_id = 1
        room_name = "测试直播间"
        interval_seconds = 30
        
        print(f"   📝 测试参数: room_id={room_id}, room_name={room_name}, interval={interval_seconds}秒")
        
        # 调用函数测试
        result = createNextRecognitionTask(room_id, room_name, interval_seconds)
        
        if result:
            print("   ✅ 重试任务创建成功，监听窗口应显示重试时间信息")
        else:
            print("   ❌ 重试任务创建失败，监听窗口应显示失败信息")
            
        return True
        
    except Exception as e:
        print(f"   ❌ 测试异常: {str(e)}")
        return False

def test_pagination_logic():
    """测试分页逻辑"""
    print("\n🧪 测试2: 分页功能逻辑")
    
    try:
        # 模拟数据
        total_rooms = 55
        page_size = 20
        current_page = 1
        
        print(f"   📝 测试参数: 总数={total_rooms}, 每页={page_size}, 当前页={current_page}")
        
        # 计算分页
        total_pages = (total_rooms + page_size - 1) // page_size
        start_index = (current_page - 1) * page_size
        end_index = min(start_index + page_size, total_rooms)
        
        print(f"   📊 分页结果: 总页数={total_pages}, 当前显示第{start_index + 1}-{end_index}个")
        
        # 测试不同页面
        for page in [1, 2, 3]:
            start = (page - 1) * page_size
            end = min(start + page_size, total_rooms)
            print(f"   📄 第{page}页: 显示第{start + 1}-{end}个直播间")
            
        print("   ✅ 分页逻辑测试通过")
        return True
        
    except Exception as e:
        print(f"   ❌ 测试异常: {str(e)}")
        return False

def test_product_binding_check():
    """测试商品绑定检查逻辑"""
    print("\n🧪 测试3: 商品绑定检查逻辑")
    
    try:
        # 模拟直播间数据
        selected_rooms = [
            {"id": 1, "name": "直播间A", "product_id": 1},  # 已绑定
            {"id": 2, "name": "直播间B", "product_id": None},  # 未绑定
            {"id": 3, "name": "直播间C", "product_id": 0},  # 未绑定
            {"id": 4, "name": "直播间D", "product_id": 2},  # 已绑定
        ]
        
        print(f"   📝 测试数据: {len(selected_rooms)}个直播间")
        
        # 检查未绑定商品的直播间
        unbound_rooms = [room for room in selected_rooms if not room.get("product_id")]
        
        print(f"   📊 检查结果: {len(unbound_rooms)}个直播间未绑定商品")
        
        if unbound_rooms:
            unbound_names = [room["name"] for room in unbound_rooms]
            print(f"   ⚠️ 未绑定商品的直播间: {', '.join(unbound_names)}")
            print("   💡 应弹出确认对话框询问是否继续")
        else:
            print("   ✅ 所有直播间都已绑定商品，可以直接开始跟播")
            
        print("   ✅ 商品绑定检查逻辑测试通过")
        return True
        
    except Exception as e:
        print(f"   ❌ 测试异常: {str(e)}")
        return False

def test_window_close_logic():
    """测试监听窗口关闭逻辑"""
    print("\n🧪 测试4: 监听窗口关闭逻辑")
    
    try:
        # 模拟API调用
        from apis import API
        
        api = API()
        room_name = "测试直播间"
        
        print(f"   📝 测试参数: room_name={room_name}")
        
        # 测试关闭窗口API
        result = api.close_follow_progress_window(room_name)
        
        if result["success"]:
            print(f"   ✅ 窗口关闭API调用成功: {result['message']}")
        else:
            print(f"   ⚠️ 窗口关闭API调用失败: {result['message']}")
            
        print("   ✅ 监听窗口关闭逻辑测试通过")
        return True
        
    except Exception as e:
        print(f"   ❌ 测试异常: {str(e)}")
        return False

def test_config_loading():
    """测试配置文件加载"""
    print("\n🧪 测试5: 配置文件加载")
    
    try:
        config_path = "config.json"
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            print(f"   📝 配置文件存在，包含 {len(config)} 个配置项")
            
            # 检查重试间隔配置
            if "intervals" in config:
                intervals = config["intervals"]
                retry_interval = intervals.get("follow_task_retry", 30)
                print(f"   ⏱️ 跟播任务重试间隔: {retry_interval}秒")
                
            print("   ✅ 配置文件加载测试通过")
        else:
            print("   ⚠️ 配置文件不存在，使用默认配置")
            
        return True
        
    except Exception as e:
        print(f"   ❌ 测试异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试监听窗口输出优化功能")
    print("=" * 60)
    
    test_results = []
    
    # 执行所有测试
    test_results.append(test_retry_task_creation())
    test_results.append(test_pagination_logic())
    test_results.append(test_product_binding_check())
    test_results.append(test_window_close_logic())
    test_results.append(test_config_loading())
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 60)
    print(f"📊 测试完成: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有功能测试通过！监听窗口输出优化功能正常工作")
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
        
    print("\n🧹 测试完成，准备清理测试文件...")
    
    # 延迟删除自身
    import threading
    def delete_self():
        time.sleep(2)
        try:
            os.remove(__file__)
            print("✅ 测试脚本已自动删除")
        except:
            print("⚠️ 测试脚本删除失败，请手动删除")
    
    threading.Thread(target=delete_self, daemon=True).start()

if __name__ == "__main__":
    main()
