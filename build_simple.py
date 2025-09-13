#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版打包脚本
"""

import os
import sys
import subprocess

def main():
    """主函数"""
    print("🏗️ 办公辅助系统 - 简化打包")
    print("="*50)
    
    # 检查main.py是否存在
    if not os.path.exists('main.py'):
        print("❌ main.py 文件不存在")
        return
    
    # 检查web目录是否存在
    if not os.path.exists('web'):
        print("❌ web 目录不存在")
        return
    
    print("✅ 文件检查通过")
    
    # 构建PyInstaller命令
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed', 
        '--name=办公辅助系统',
        '--add-data=web;web',
        '--hidden-import=openpyxl',
        '--hidden-import=requests',
        '--hidden-import=webview',
        '--hidden-import=apis',
        '--hidden-import=cmm', 
        '--hidden-import=sqlite3_util',
        '--clean',
        'main.py'
    ]
    
    # 如果有图标文件，添加图标参数
    if os.path.exists('icon.ico'):
        cmd.insert(-2, '--icon=icon.ico')
        print("✅ 找到图标文件")
    
    print(f"\n📦 执行打包命令:")
    print(' '.join(cmd))
    print()
    
    try:
        # 执行打包
        subprocess.run(cmd, check=True)
        print("\n✅ 打包成功！")
        
        # 检查输出文件
        exe_path = os.path.join('dist', '办公辅助系统.exe')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"📁 输出文件: {exe_path}")
            print(f"📊 文件大小: {size_mb:.1f} MB")
        else:
            print("⚠️ 未找到输出文件")
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败: {e}")
        print("\n💡 可能的解决方案:")
        print("1. 确保已安装 PyInstaller: pip install pyinstaller")
        print("2. 确保已安装所有依赖: pip install -r requirements.txt")
        print("3. 检查Python版本是否为3.7+")
        
    except FileNotFoundError:
        print("\n❌ PyInstaller 未找到")
        print("请安装: pip install pyinstaller")

if __name__ == "__main__":
    main()
