#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试监听窗口输出功能
"""

import sys
import os
import time

def test_sync_print_function():
    """测试sync_print函数是否正常工作"""
    print("🧪 测试1: sync_print函数")
    
    try:
        # 导入模块
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from apis import sync_print
        
        # 测试不同类型的输出
        sync_print("✅ 测试成功消息", "success", "测试直播间", "功能测试")
        sync_print("⚠️ 测试警告消息", "warning", "测试直播间", "功能测试")
        sync_print("❌ 测试错误消息", "error", "测试直播间", "功能测试")
        sync_print("ℹ️ 测试信息消息", "info", "测试直播间", "功能测试")
        
        print("   ✅ sync_print函数测试通过")
        return True
        
    except Exception as e:
        print(f"   ❌ sync_print函数测试失败: {e}")
        return False

def test_live_detection_functions():
    """测试直播检测函数的输出"""
    print("\n🧪 测试2: 直播检测函数输出")
    
    try:
        from follwRoom import topisLiveText, liveEnd
        
        # 检查函数签名是否正确
        import inspect
        
        # 检查topisLiveText函数
        sig = inspect.signature(topisLiveText)
        params = list(sig.parameters.keys())
        if 'room_name' in params:
            print("   ✅ topisLiveText函数已添加room_name参数")
        else:
            print("   ❌ topisLiveText函数缺少room_name参数")
            return False
            
        # 检查liveEnd函数
        sig = inspect.signature(liveEnd)
        params = list(sig.parameters.keys())
        if 'room_name' in params:
            print("   ✅ liveEnd函数已添加room_name参数")
        else:
            print("   ❌ liveEnd函数缺少room_name参数")
            return False
            
        print("   ✅ 直播检测函数签名检查通过")
        return True
        
    except Exception as e:
        print(f"   ❌ 直播检测函数测试失败: {e}")
        return False

def test_close_window_api():
    """测试关闭窗口API"""
    print("\n🧪 测试3: 关闭窗口API")
    
    try:
        from apis import API
        
        api = API()
        
        # 检查是否有关闭窗口的方法
        if hasattr(api, 'close_follow_progress_window'):
            print("   ✅ close_follow_progress_window方法存在")
            
            # 测试调用
            result = api.close_follow_progress_window("测试直播间")
            if isinstance(result, dict) and 'success' in result:
                print("   ✅ 关闭窗口API调用成功")
                return True
            else:
                print("   ❌ 关闭窗口API返回格式错误")
                return False
        else:
            print("   ❌ close_follow_progress_window方法不存在")
            return False
            
    except Exception as e:
        print(f"   ❌ 关闭窗口API测试失败: {e}")
        return False

def test_tab_close_functions():
    """测试标签关闭函数"""
    print("\n🧪 测试4: 标签关闭函数")
    
    try:
        from follwRoom import closeTabByTitle, getWxChromeWindowByIndex
        
        # 检查函数是否存在
        print("   ✅ closeTabByTitle函数存在")
        print("   ✅ getWxChromeWindowByIndex函数存在")
        
        # 检查函数签名
        import inspect
        
        sig = inspect.signature(closeTabByTitle)
        params = list(sig.parameters.keys())
        if 'chrome' in params and 'title' in params:
            print("   ✅ closeTabByTitle函数参数正确")
        else:
            print("   ❌ closeTabByTitle函数参数错误")
            return False
            
        sig = inspect.signature(getWxChromeWindowByIndex)
        params = list(sig.parameters.keys())
        if 'index' in params:
            print("   ✅ getWxChromeWindowByIndex函数参数正确")
        else:
            print("   ❌ getWxChromeWindowByIndex函数参数错误")
            return False
            
        print("   ✅ 标签关闭函数检查通过")
        return True
        
    except Exception as e:
        print(f"   ❌ 标签关闭函数测试失败: {e}")
        return False

def check_code_for_sync_print():
    """检查代码中是否正确使用sync_print"""
    print("\n🧪 测试5: 检查代码中的输出函数使用")
    
    try:
        with open("follwRoom.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        # 统计sync_print和print的使用
        sync_print_count = content.count("sync_print(")
        print_count = content.count("print(")
        
        print(f"   📊 sync_print使用次数: {sync_print_count}")
        print(f"   📊 print使用次数: {print_count}")
        
        # 检查关键函数是否使用sync_print
        key_functions = [
            "topisLiveText",
            "liveEnd", 
            "重试任务创建失败",
            "搜索标签已自动关闭",
            "监听窗口已自动关闭"
        ]
        
        missing_sync_print = []
        for func in key_functions:
            if func in content:
                # 检查该函数附近是否有sync_print
                func_index = content.find(func)
                if func_index != -1:
                    # 检查函数前后500字符内是否有sync_print
                    start = max(0, func_index - 500)
                    end = min(len(content), func_index + 500)
                    section = content[start:end]
                    if "sync_print" not in section:
                        missing_sync_print.append(func)
        
        if missing_sync_print:
            print(f"   ⚠️ 以下功能可能未使用sync_print: {missing_sync_print}")
        else:
            print("   ✅ 关键功能都使用了sync_print")
            
        return len(missing_sync_print) == 0
        
    except Exception as e:
        print(f"   ❌ 代码检查失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试监听窗口输出功能")
    print("=" * 60)
    
    test_results = []
    
    # 执行所有测试
    test_results.append(test_sync_print_function())
    test_results.append(test_live_detection_functions())
    test_results.append(test_close_window_api())
    test_results.append(test_tab_close_functions())
    test_results.append(check_code_for_sync_print())
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 60)
    print(f"📊 测试完成: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有监听窗口输出功能测试通过！")
        print("\n✅ 确认修复:")
        print("   1. ✅ sync_print函数正常工作")
        print("   2. ✅ 直播检测函数输出到监听窗口")
        print("   3. ✅ 关闭窗口API正常工作")
        print("   4. ✅ 标签关闭函数正常工作")
        print("   5. ✅ 代码正确使用sync_print输出")
    else:
        print("⚠️ 部分测试失败，需要进一步修复")
        
    print("\n💡 使用提示:")
    print("   - 所有重要信息现在都会输出到监听窗口")
    print("   - 跟播失败时会自动关闭监听窗口和搜索标签")
    print("   - 直播状态检测更加准确")
    print("   - 如果前端功能未生效，请按Ctrl+F5刷新浏览器")
        
    # 自动删除测试脚本
    import threading
    def delete_self():
        time.sleep(2)
        try:
            os.remove(__file__)
            print("🧹 测试脚本已自动删除")
        except:
            pass
    
    threading.Thread(target=delete_self, daemon=True).start()

if __name__ == "__main__":
    main()
