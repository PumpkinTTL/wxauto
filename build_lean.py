#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精简版打包脚本
移除了不需要的依赖，减小打包体积
"""

import os
import sys
import shutil
import subprocess

def clean_build():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🧹 清理目录: {dir_name}")
            shutil.rmtree(dir_name)
    
    # 清理.spec文件
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            print(f"🧹 清理文件: {file}")
            os.remove(file)

def check_dependencies():
    """检查核心依赖"""
    core_packages = {
        'webview': 'pywebview',
        'openpyxl': 'openpyxl',
        'requests': 'requests'
    }

    missing_packages = []
    for import_name, package_name in core_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name} 已安装")
        except ImportError:
            missing_packages.append(package_name)
            print(f"❌ {package_name} 未安装")

    if missing_packages:
        print(f"\n⚠️ 缺少核心依赖包: {', '.join(missing_packages)}")
        return False
    return True

def build_app():
    """构建应用程序"""
    print("🚀 开始构建精简版应用程序...")
    
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=办公辅助系统',
        '--add-data=web;web',
        '--hidden-import=openpyxl',
        '--hidden-import=requests',
        '--hidden-import=webview',
        '--hidden-import=webview.platforms.winforms',
        '--hidden-import=webview.platforms.cef',
        '--hidden-import=webview.platforms.edgechromium',
        '--hidden-import=apis',
        '--hidden-import=cmm',
        '--hidden-import=sqlite3_util',
        '--hidden-import=proxies_util',
        '--exclude-module=playwright',
        '--exclude-module=selenium',
        '--exclude-module=pyautogui',
        '--exclude-module=cv2',
        '--exclude-module=numpy',
        '--exclude-module=PIL',
        '--exclude-module=wxauto',
        '--exclude-module=uiautomation',
        '--collect-all=webview',
        '--clean',
        '--optimize=2',
        'main.py'
    ]
    
    if os.path.exists('icon.ico'):
        cmd.insert(-2, '--icon=icon.ico')
    
    try:
        print(f"📦 执行命令...")
        result = subprocess.run(cmd, check=True)
        print("✅ 构建成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        return False

def main():
    """主函数"""
    print("🏗️ 办公辅助系统 - 精简版打包工具")
    print("=" * 50)
    print("📋 优化特性:")
    print("  ✅ 移除了playwright及其驱动")
    print("  ✅ 排除了可选的图像处理库")
    print("  ✅ 排除了微信自动化库")
    print("  ✅ 只包含核心必需依赖")
    print("=" * 50)
    
    if not check_dependencies():
        sys.exit(1)
    
    clean_build()
    
    if build_app():
        exe_path = os.path.join('dist', '办公辅助系统.exe')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n🎉 精简版打包完成！")
            print(f"📊 文件大小: {size_mb:.1f} MB")
            print("💡 相比之前应该显著减小了体积")
    else:
        print("\n❌ 打包失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
