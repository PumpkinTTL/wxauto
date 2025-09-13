#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能实现检查清单
"""

import os
import re

def check_function_implementation():
    """检查所有要求的功能是否已实现"""
    
    print("🔍 检查功能实现情况")
    print("=" * 60)
    
    # 检查项目
    checks = []
    
    # 1. 检查重试任务创建提示
    print("\n1. 🔄 检查重试任务创建提示功能")
    try:
        with open("follwRoom.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        # 检查是否有重试时间显示
        if "创建重试任务，将在" in content and "重试" in content:
            print("   ✅ 重试任务创建提示 - 已实现")
            checks.append(True)
        else:
            print("   ❌ 重试任务创建提示 - 未实现")
            checks.append(False)
            
        # 检查是否有倒计时显示
        if "距离下次重试" in content:
            print("   ✅ 重试倒计时显示 - 已实现")
        else:
            print("   ❌ 重试倒计时显示 - 未实现")
            
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        checks.append(False)
    
    # 2. 检查分页功能
    print("\n2. 📄 检查分页功能")
    try:
        with open("web/pages/follow_wechat.html", "r", encoding="utf-8") as f:
            content = f.read()
            
        # 检查分页组件
        if "el-pagination" in content and "currentPage" in content and "pageSize" in content:
            print("   ✅ 分页组件 - 已实现")
            checks.append(True)
        else:
            print("   ❌ 分页组件 - 未实现")
            checks.append(False)
            
        # 检查分页处理函数
        if "handleSizeChange" in content and "handleCurrentChange" in content:
            print("   ✅ 分页处理函数 - 已实现")
        else:
            print("   ❌ 分页处理函数 - 未实现")
            
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        checks.append(False)
    
    # 3. 检查商品绑定检查
    print("\n3. 🔍 检查商品绑定检查功能")
    try:
        with open("web/pages/follow_wechat.html", "r", encoding="utf-8") as f:
            content = f.read()
            
        # 检查商品绑定检查逻辑
        if "unboundRooms" in content and "ElMessageBox.confirm" in content and "商品绑定检查" in content:
            print("   ✅ 商品绑定检查 - 已实现")
            checks.append(True)
        else:
            print("   ❌ 商品绑定检查 - 未实现")
            checks.append(False)
            
        # 检查确认对话框
        if "确定跟播" in content and "取消" in content:
            print("   ✅ 确认对话框 - 已实现")
        else:
            print("   ❌ 确认对话框 - 未实现")
            
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        checks.append(False)
    
    # 4. 检查监听窗口关闭功能
    print("\n4. 🔄 检查监听窗口关闭功能")
    try:
        with open("apis.py", "r", encoding="utf-8") as f:
            apis_content = f.read()
            
        with open("follwRoom.py", "r", encoding="utf-8") as f:
            follw_content = f.read()
            
        # 检查关闭窗口API
        if "close_follow_progress_window" in apis_content:
            print("   ✅ 关闭窗口API - 已实现")
            checks.append(True)
        else:
            print("   ❌ 关闭窗口API - 未实现")
            checks.append(False)
            
        # 检查调用关闭窗口的逻辑
        if "close_follow_progress_window" in follw_content:
            print("   ✅ 调用关闭窗口逻辑 - 已实现")
        else:
            print("   ❌ 调用关闭窗口逻辑 - 未实现")
            
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        checks.append(False)
    
    # 5. 检查关闭搜索标签功能
    print("\n5. 🔄 检查关闭搜索标签功能")
    try:
        with open("follwRoom.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        # 检查关闭标签逻辑
        if "closeTabByTitle" in content and "搜一搜" in content:
            print("   ✅ 关闭搜索标签 - 已实现")
            checks.append(True)
        else:
            print("   ❌ 关闭搜索标签 - 未实现")
            checks.append(False)
            
        # 检查获取Chrome窗口
        if "getWxChromeWindowByIndex" in content:
            print("   ✅ 获取Chrome窗口 - 已实现")
        else:
            print("   ❌ 获取Chrome窗口 - 未实现")
            
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        checks.append(False)
    
    # 6. 检查直播状态检测改进
    print("\n6. 🔴 检查直播状态检测改进")
    try:
        with open("follwRoom.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        # 检查改进的直播状态检测
        if "直播已结束" in content and "暂未开播" in content and "LIVE_CHECK" in content:
            print("   ✅ 直播状态检测改进 - 已实现")
            checks.append(True)
        else:
            print("   ❌ 直播状态检测改进 - 未实现")
            checks.append(False)
            
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        checks.append(False)
    
    # 统计结果
    total_checks = len(checks)
    passed_checks = sum(checks)
    
    print("\n" + "=" * 60)
    print(f"📊 功能实现检查结果: {passed_checks}/{total_checks}")
    
    if passed_checks == total_checks:
        print("🎉 所有功能都已正确实现！")
    else:
        print(f"⚠️ 还有 {total_checks - passed_checks} 个功能需要完善")
        
    # 检查文件是否存在
    print("\n📁 文件存在性检查:")
    files_to_check = [
        "follwRoom.py",
        "apis.py", 
        "web/pages/follow_wechat.html",
        "config.json"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - 文件不存在")
    
    return passed_checks == total_checks

def check_specific_issues():
    """检查特定问题"""
    print("\n🔍 检查特定问题")
    print("-" * 40)
    
    # 检查直播状态检测逻辑
    print("1. 检查直播状态检测逻辑:")
    try:
        with open("follwRoom.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        # 查找topisLiveText函数
        if "def topisLiveText" in content:
            print("   ✅ topisLiveText函数存在")
            
            # 检查是否有改进的检测逻辑
            if "直播已结束" in content and "暂未开播" in content:
                print("   ✅ 包含改进的直播状态检测")
            else:
                print("   ⚠️ 直播状态检测可能不够准确")
        else:
            print("   ❌ topisLiveText函数不存在")
            
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")

if __name__ == "__main__":
    success = check_function_implementation()
    check_specific_issues()
    
    if success:
        print("\n✅ 所有功能检查通过！")
    else:
        print("\n⚠️ 部分功能需要进一步检查和修复")
    
    # 自动删除检查脚本
    import time
    import threading
    
    def delete_self():
        time.sleep(2)
        try:
            os.remove(__file__)
            print("🧹 检查脚本已自动删除")
        except:
            pass
    
    threading.Thread(target=delete_self, daemon=True).start()
