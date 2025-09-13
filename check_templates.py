#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查templates目录下的OCR素材文件是否缺失
"""

import os
import re

def check_templates_files():
    """检查templates文件是否缺失"""
    print("🔍 检查templates目录下的OCR素材文件")
    print("=" * 60)
    
    # 1. 检查templates目录是否存在
    templates_dir = "templates"
    if not os.path.exists(templates_dir):
        print(f"❌ {templates_dir} 目录不存在")
        return False
    
    print(f"✅ {templates_dir} 目录存在")
    
    # 2. 列出templates目录中的所有文件
    print(f"\n📁 {templates_dir} 目录中的文件:")
    template_files = []
    for file in os.listdir(templates_dir):
        if file.endswith('.png'):
            template_files.append(file)
            file_path = os.path.join(templates_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"   ✅ {file} ({file_size} bytes)")
        else:
            print(f"   📄 {file} (非图片文件)")
    
    print(f"\n📊 总共找到 {len(template_files)} 个PNG图片文件")
    
    # 3. 检查代码中引用的templates文件
    print(f"\n🔍 检查代码中引用的templates文件:")
    
    # 需要检查的文件列表
    files_to_check = [
        "follwRoom.py",
        "followwx/wxChromeFollow.py", 
        "wechat_automation.py"
    ]
    
    referenced_files = set()
    missing_files = []
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"\n📄 检查文件: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 查找templates引用
            pattern = r'["\']\.?/?templates/([^"\']+\.png)["\']'
            matches = re.findall(pattern, content)
            
            if matches:
                for match in matches:
                    referenced_files.add(match)
                    template_path = os.path.join(templates_dir, match)
                    if os.path.exists(template_path):
                        file_size = os.path.getsize(template_path)
                        print(f"   ✅ {match} (存在, {file_size} bytes)")
                    else:
                        print(f"   ❌ {match} (缺失)")
                        missing_files.append(match)
            else:
                print(f"   ℹ️ 未找到templates引用")
        else:
            print(f"   ⚠️ 文件不存在: {file_path}")
    
    # 4. 总结检查结果
    print(f"\n" + "=" * 60)
    print(f"📊 检查结果总结:")
    print(f"   🗂️ templates目录中的PNG文件: {len(template_files)} 个")
    print(f"   🔗 代码中引用的文件: {len(referenced_files)} 个")
    print(f"   ❌ 缺失的文件: {len(missing_files)} 个")
    
    if missing_files:
        print(f"\n❌ 缺失的文件列表:")
        for file in missing_files:
            print(f"   - {file}")
        print(f"\n💡 解决方案:")
        print(f"   1. 检查文件名是否正确")
        print(f"   2. 确保文件已保存到templates目录")
        print(f"   3. 检查文件权限")
        return False
    else:
        print(f"\n🎉 所有引用的templates文件都存在！")
        
    # 5. 检查未使用的文件
    unused_files = set(template_files) - referenced_files
    if unused_files:
        print(f"\n📋 未被代码引用的文件 ({len(unused_files)} 个):")
        for file in unused_files:
            print(f"   - {file}")
        print(f"   💡 这些文件可能是备用文件或已废弃的文件")
    
    # 6. 详细的引用映射
    print(f"\n🔗 文件引用详情:")
    for ref_file in sorted(referenced_files):
        template_path = os.path.join(templates_dir, ref_file)
        if os.path.exists(template_path):
            file_size = os.path.getsize(template_path)
            print(f"   ✅ {ref_file} -> {file_size} bytes")
        else:
            print(f"   ❌ {ref_file} -> 文件缺失")
    
    return len(missing_files) == 0

def check_specific_functions():
    """检查特定函数的templates引用"""
    print(f"\n🔍 检查特定函数的templates引用:")
    
    # 检查follwRoom.py中的关键函数
    try:
        with open("follwRoom.py", 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查关键函数
        functions_to_check = [
            "clickByIMG",
            "topSearch", 
            "clickSendBtn",
            "clickChatBtn"
        ]
        
        for func_name in functions_to_check:
            if func_name in content:
                print(f"   ✅ 函数 {func_name} 存在")
                
                # 查找函数定义附近的templates引用
                func_pattern = rf'def {func_name}.*?(?=def|\Z)'
                func_match = re.search(func_pattern, content, re.DOTALL)
                if func_match:
                    func_content = func_match.group(0)
                    template_refs = re.findall(r'templates/([^"\']+\.png)', func_content)
                    if template_refs:
                        for ref in template_refs:
                            template_path = os.path.join("templates", ref)
                            if os.path.exists(template_path):
                                print(f"     ✅ 引用: {ref}")
                            else:
                                print(f"     ❌ 引用: {ref} (文件缺失)")
                    else:
                        print(f"     ℹ️ 未找到templates引用")
            else:
                print(f"   ❌ 函数 {func_name} 不存在")
                
    except Exception as e:
        print(f"   ❌ 检查函数引用失败: {e}")

def main():
    """主函数"""
    success = check_templates_files()
    check_specific_functions()
    
    if success:
        print(f"\n✅ 所有templates文件检查通过！")
    else:
        print(f"\n⚠️ 发现templates文件缺失，请检查并补充")
    
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

if __name__ == "__main__":
    main()
