#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小化打包脚本 - 生成20MB左右的精简exe
"""

import os
import sys
import subprocess
import shutil

def clean_build():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🧹 清理目录: {dir_name}")
            shutil.rmtree(dir_name)

    # 清理.spec文件和.pyc文件
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            print(f"🧹 清理文件: {file}")
            os.remove(file)

    # 递归清理所有__pycache__目录
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            print(f"🧹 清理缓存: {pycache_path}")
            shutil.rmtree(pycache_path)

def build_minimal_exe():
    """构建最小化的exe文件"""
    print("🚀 开始构建最小化exe文件...")

    # 检查必要文件
    entry_file = 'main.py'
    if not os.path.exists(entry_file):
        print(f"❌ 错误: {entry_file} 文件不存在")
        return False

    if not os.path.exists('web'):
        print("❌ 错误: web 目录不存在")
        return False

    print("📦 配置最小化打包参数...")

    # PyInstaller命令 - 最小化配置 + .NET运行时支持
    cmd = [
        'pyinstaller',
        '--onefile',                    # 单文件打包
        '--windowed',                   # 无控制台窗口
        '--name=办公辅助系统v1.3',        # 程序名
        '--add-data=web;web',           # 添加web目录

        # 核心依赖
        '--hidden-import=webview',      # pywebview核心
        '--hidden-import=webview.platforms.winforms',  # Windows平台支持
        '--hidden-import=apis',         # 本地API模块
        '--hidden-import=cmm',          # 蝉妈妈模块
        '--hidden-import=sqlite3_util', # 数据库工具
        '--hidden-import=openpyxl',     # Excel处理
        '--hidden-import=requests',     # HTTP请求
        '--hidden-import=tkinter',      # 保留tkinter用于错误对话框
        '--hidden-import=tkinter.messagebox',  # 消息框

        # .NET和webview相关
        '--hidden-import=clr',          # Python.NET
        '--hidden-import=pythonnet',    # Python.NET
        '--hidden-import=System',       # .NET System

        # 排除不需要的大型模块
        '--exclude-module=matplotlib',  # 排除matplotlib
        '--exclude-module=numpy',       # 排除numpy（如果不需要）
        '--exclude-module=opencv-python', # 排除opencv
        '--exclude-module=pyautogui',   # 排除pyautogui
        '--exclude-module=wxauto',      # 排除微信自动化
        '--exclude-module=uiautomation', # 排除UI自动化
        '--exclude-module=Pillow',      # 排除图像处理
        '--exclude-module=PIL',         # 排除PIL
        '--exclude-module=cv2',         # 排除opencv
        '--exclude-module=pytest',      # 排除测试框架
        '--exclude-module=setuptools',  # 排除setuptools
        '--exclude-module=pip',         # 排除pip

        # 优化选项
        '--clean',                      # 清理临时文件
        '--optimize=2',                 # 最高级别字节码优化
        '--strip',                      # 去除调试信息
        '--noupx',                      # 不使用UPX压缩（避免兼容性问题）

        entry_file                      # 入口文件
    ]
    
    try:
        print("⚙️ 执行打包命令...")
        print("📝 打包参数预览:")
        for i, arg in enumerate(cmd):
            if i == 0:
                print(f"   {arg}")
            else:
                print(f"     {arg}")

        print("\n🔄 开始打包...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        print("✅ 构建成功！")

        # 检查输出文件
        exe_path = os.path.join('dist', '办公辅助系统v1.3.exe')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"📁 输出文件: {exe_path}")
            print(f"📏 文件大小: {size_mb:.1f} MB")

            # 大小检查
            if size_mb <= 30:
                print("🎉 文件大小符合预期（≤30MB）")
            else:
                print("⚠️ 文件大小超出预期，可能需要进一步优化")

            print("✨ 特性:")
            print("   • 无控制台窗口")
            print("   • 最小化依赖")
            print("   • 单文件部署")
            print("   • 优化字节码")
            return True
        else:
            print("❌ 警告: 未找到输出文件")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        if e.stdout:
            print("标准输出:", e.stdout)
        if e.stderr:
            print("错误输出:", e.stderr)
        return False
    except FileNotFoundError:
        print("❌ 错误: PyInstaller 未找到")
        print("请安装: pip install pyinstaller")
        return False

def check_dependencies():
    """检查必要的依赖"""
    print("🔍 检查依赖...")

    required_modules = ['webview', 'openpyxl', 'requests']
    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} - 缺失")
            missing_modules.append(module)

    if missing_modules:
        print(f"\n❌ 缺少依赖: {', '.join(missing_modules)}")
        print("请安装: pip install " + " ".join(missing_modules))
        return False

    print("✅ 所有必要依赖已安装")
    return True

def main():
    """主函数"""
    print("🏢 办公辅助系统 - 最小化打包工具")
    print("=" * 50)
    print("🎯 目标: 生成20-30MB的精简exe文件")
    print("=" * 50)

    # 检查依赖
    if not check_dependencies():
        return 1

    # 清理旧文件
    clean_build()

    # 构建最小化exe
    if build_minimal_exe():
        print("\n🎉 打包成功！")
        print("📋 生成的exe文件特点:")
        print("   • 🚫 无控制台窗口")
        print("   • 📦 最小化依赖包")
        print("   • 🎯 精简文件大小")
        print("   • 🚀 单文件部署")
        print("   • ⚡ 优化启动速度")
        print("\n💡 提示: 如果文件仍然过大，可以考虑:")
        print("   • 检查是否有未排除的大型依赖")
        print("   • 使用虚拟环境进行打包")
        print("   • 进一步精简web资源文件")
    else:
        print("\n❌ 打包失败！")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
