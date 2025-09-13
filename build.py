#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包脚本
使用PyInstaller打包应用程序
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
    """检查依赖"""
    # 包名和导入名的映射
    packages_to_check = {
        'PyInstaller': 'pyinstaller',  # 导入名: 包名
        'webview': 'pywebview',
        'openpyxl': 'openpyxl',
        'requests': 'requests'
    }

    missing_packages = []

    for import_name, package_name in packages_to_check.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name} 已安装")
        except ImportError:
            missing_packages.append(package_name)
            print(f"❌ {package_name} 未安装")

    if missing_packages:
        print(f"\n⚠️ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行以下命令安装:")
        for pkg in missing_packages:
            print(f"  pip install {pkg}")
        return False

    return True

def build_app():
    """构建应用程序"""
    print("🚀 开始构建应用程序...")
    
    # PyInstaller命令
    cmd = [
        'pyinstaller',
        '--onefile',  # 打包成单个文件
        '--windowed',  # 无控制台窗口
        '--name=办公辅助系统',  # 应用程序名称
        '--icon=icon.ico',  # 图标文件（如果有）
        '--add-data=web;web',  # 添加web目录
        '--hidden-import=openpyxl',
        '--hidden-import=openpyxl.workbook',
        '--hidden-import=openpyxl.worksheet',
        '--hidden-import=requests',
        '--hidden-import=requests.adapters',
        '--hidden-import=sqlite3',
        '--hidden-import=webview',
        '--hidden-import=webview.platforms',
        '--hidden-import=apis',
        '--hidden-import=cmm',
        '--hidden-import=sqlite3_util',
        '--hidden-import=json',
        '--hidden-import=time',
        '--hidden-import=threading',
        '--hidden-import=hashlib',
        '--hidden-import=datetime',
        '--clean',  # 清理临时文件
        'main.py'
    ]
    
    # 如果没有图标文件，移除图标参数
    if not os.path.exists('icon.ico'):
        cmd = [arg for arg in cmd if not arg.startswith('--icon')]
    
    try:
        print(f"📦 执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 构建成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def copy_additional_files():
    """复制额外文件到dist目录"""
    dist_dir = 'dist'
    if not os.path.exists(dist_dir):
        return
    
    additional_files = [
        'README.md',
        'requirements.txt',
        'system.db'  # 如果有数据库文件
    ]
    
    for file in additional_files:
        if os.path.exists(file):
            dest = os.path.join(dist_dir, file)
            shutil.copy2(file, dest)
            print(f"📄 复制文件: {file} -> {dest}")

def main():
    """主函数"""
    print("🏗️ 办公辅助系统打包工具")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 清理构建目录
    clean_build()
    
    # 构建应用程序
    if build_app():
        # 复制额外文件
        copy_additional_files()
        
        print("\n🎉 打包完成！")
        print("📁 输出目录: dist/")
        print("🚀 可执行文件: dist/办公辅助系统.exe")
        
        # 显示文件大小
        exe_path = os.path.join('dist', '办公辅助系统.exe')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"📊 文件大小: {size_mb:.1f} MB")
    else:
        print("\n❌ 打包失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
