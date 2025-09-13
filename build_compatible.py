#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
兼容性打包脚本 - 解决.NET运行时问题
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
    
    # 清理.spec文件
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            print(f"🧹 清理文件: {file}")
            os.remove(file)

def create_compatible_spec():
    """创建兼容性spec文件"""
    print("📝 创建兼容性spec配置...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 分析阶段
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('web', 'web')],
    hiddenimports=[
        'webview',
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
        'apis',
        'cmm',
        'sqlite3_util',
        'openpyxl',
        'requests',
        'tkinter',
        'tkinter.messagebox',
        'clr_loader',
        'pythonnet',
        'System',
        'System.Windows.Forms',
        'System.Drawing'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'opencv-python',
        'cv2',
        'pyautogui',
        'wxauto',
        'uiautomation',
        'Pillow',
        'PIL',
        'pytest',
        'setuptools',
        'pip'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 打包阶段
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='办公辅助系统v1.3',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    optimize=2,
)
'''
    
    with open('compatible.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ 兼容性spec文件创建完成")

def build_compatible():
    """构建兼容性exe"""
    print("🚀 开始兼容性打包...")
    
    # 检查必要文件
    if not os.path.exists('main.py'):
        print("❌ main.py 不存在")
        return False
    
    if not os.path.exists('web'):
        print("❌ web目录不存在")
        return False
    
    # 创建spec文件
    create_compatible_spec()
    
    # 使用spec文件打包
    cmd = ['pyinstaller', '--clean', 'compatible.spec']
    
    try:
        print("⚙️ 执行兼容性打包...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ 打包完成！")
        
        # 检查结果
        exe_path = os.path.join('dist', '办公辅助系统v1.3.exe')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"📁 输出文件: {exe_path}")
            print(f"📏 文件大小: {size_mb:.1f} MB")
            
            print("✨ 兼容性特性:")
            print("   • 包含.NET运行时支持")
            print("   • 包含错误处理对话框")
            print("   • 支持多种webview后端")
            print("   • 无控制台窗口")
            
            return True
        else:
            print("❌ 未找到输出文件")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败: {e}")
        if e.stderr:
            print("错误信息:", e.stderr)
        return False
    finally:
        # 清理spec文件
        if os.path.exists('compatible.spec'):
            os.remove('compatible.spec')

def create_runtime_installer():
    """创建运行时安装脚本"""
    print("📝 创建运行时安装脚本...")
    
    installer_content = '''@echo off
echo 正在检查和安装必要的运行时环境...
echo.

echo 1. 检查 .NET Framework...
reg query "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\NET Framework Setup\\NDP\\v4\\Full" /v Release >nul 2>&1
if %errorlevel% neq 0 (
    echo .NET Framework 4.7.2 或更高版本未安装
    echo 请从以下链接下载安装:
    echo https://dotnet.microsoft.com/download/dotnet-framework
    echo.
) else (
    echo .NET Framework 已安装
)

echo 2. 检查 Microsoft Edge WebView2...
if exist "%PROGRAMFILES(X86)%\\Microsoft\\EdgeWebView\\Application\\msedgewebview2.exe" (
    echo Microsoft Edge WebView2 已安装
) else (
    echo Microsoft Edge WebView2 未安装
    echo 请从以下链接下载安装:
    echo https://developer.microsoft.com/microsoft-edge/webview2/
    echo.
)

echo 3. 检查 Visual C++ Redistributable...
reg query "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64" >nul 2>&1
if %errorlevel% neq 0 (
    echo Visual C++ Redistributable 未安装
    echo 请从以下链接下载安装:
    echo https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo.
) else (
    echo Visual C++ Redistributable 已安装
)

echo.
echo 检查完成！如果有缺失的组件，请按照提示安装。
pause
'''
    
    with open('install_runtime.bat', 'w', encoding='gbk') as f:
        f.write(installer_content)
    
    print("✅ 运行时安装脚本已创建: install_runtime.bat")

def main():
    """主函数"""
    print("🔧 办公辅助系统 - 兼容性打包工具")
    print("=" * 50)
    print("🎯 解决.NET运行时和webview兼容性问题")
    print("=" * 50)
    
    # 清理旧文件
    clean_build()
    
    # 兼容性打包
    if build_compatible():
        print("\n🎉 兼容性打包成功！")
        
        # 创建运行时安装脚本
        create_runtime_installer()
        
        print("\n📋 部署说明:")
        print("   1. 将生成的exe文件分发给用户")
        print("   2. 如果用户遇到运行时错误，运行 install_runtime.bat")
        print("   3. 或者手动安装以下组件:")
        print("      • .NET Framework 4.7.2+")
        print("      • Microsoft Edge WebView2 Runtime")
        print("      • Visual C++ Redistributable")
        
    else:
        print("\n❌ 兼容性打包失败！")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
