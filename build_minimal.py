#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超小体积打包脚本 - 目标15-20MB
专门针对办公辅助系统的最小化打包
"""

import os
import sys
import subprocess
import shutil
import json

def clean_all():
    """彻底清理所有构建文件"""
    print("🧹 彻底清理构建环境...")
    
    # 清理目录
    dirs_to_clean = ['build', 'dist', '__pycache__', '.pytest_cache']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"   🗑️ 删除目录: {dir_name}")
            shutil.rmtree(dir_name)
    
    # 清理文件
    files_to_clean = []
    for file in os.listdir('.'):
        if file.endswith(('.spec', '.pyc', '.pyo')):
            files_to_clean.append(file)
    
    for file in files_to_clean:
        print(f"   🗑️ 删除文件: {file}")
        os.remove(file)
    
    # 递归清理缓存
    for root, dirs, files in os.walk('.'):
        # 清理__pycache__
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            shutil.rmtree(pycache_path)
        
        # 清理.pyc文件
        for file in files:
            if file.endswith(('.pyc', '.pyo')):
                file_path = os.path.join(root, file)
                os.remove(file_path)

def create_minimal_spec():
    """创建最小化的spec文件"""
    print("📝 创建最小化spec配置...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 排除的模块列表 - 大幅减少文件大小
excludes = [
    'tkinter', 'tk', 'tcl',
    'matplotlib', 'numpy', 'scipy',
    'pandas', 'PIL', 'Pillow',
    'opencv-python', 'cv2',
    'pyautogui', 'wxauto', 'uiautomation',
    'pytest', 'setuptools', 'pip',
    'wheel', 'distutils',
    'email', 'html', 'http', 'urllib3',
    'xml', 'xmlrpc', 'pydoc',
    'doctest', 'unittest', 'test',
    'multiprocessing', 'concurrent',
    'asyncio', 'queue',
    'logging.handlers', 'logging.config'
]

# 隐藏导入 - 只包含必需的
hiddenimports = [
    'webview',
    'webview.platforms.winforms',
    'apis',
    'cmm', 
    'sqlite3_util',
    'openpyxl',
    'requests'
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('web', 'web')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 过滤掉不需要的文件
def filter_binaries(binaries):
    filtered = []
    exclude_patterns = [
        'api-ms-win',
        'ucrtbase',
        'msvcp',
        'vcruntime',
        'Qt5',
        'libssl',
        'libcrypto'
    ]
    
    for binary in binaries:
        name = binary[0].lower()
        if not any(pattern in name for pattern in exclude_patterns):
            filtered.append(binary)
    
    return filtered

a.binaries = filter_binaries(a.binaries)

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
    upx=False,  # 不使用UPX压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 无控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    optimize=2,  # 最高优化级别
)
'''
    
    with open('minimal.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ spec文件创建完成")

def build_ultra_minimal():
    """使用自定义spec文件构建超小体积exe"""
    print("🚀 开始超小体积打包...")
    
    # 检查必要文件
    if not os.path.exists('main.py'):
        print("❌ main.py 不存在")
        return False
    
    if not os.path.exists('web'):
        print("❌ web目录不存在")
        return False
    
    # 创建spec文件
    create_minimal_spec()
    
    # 使用spec文件打包
    cmd = ['pyinstaller', '--clean', 'minimal.spec']
    
    try:
        print("⚙️ 执行打包命令...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ 打包完成！")
        
        # 检查结果
        exe_path = os.path.join('dist', '办公辅助系统v1.3.exe')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"📁 输出文件: {exe_path}")
            print(f"📏 文件大小: {size_mb:.1f} MB")
            
            if size_mb <= 25:
                print("🎉 文件大小优秀！")
            elif size_mb <= 35:
                print("✅ 文件大小良好")
            else:
                print("⚠️ 文件大小仍需优化")
            
            return True
        else:
            print("❌ 未找到输出文件")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败: {e}")
        if e.stderr:
            print("错误信息:", e.stderr)
        return False

def main():
    """主函数"""
    print("🎯 办公辅助系统 - 超小体积打包工具")
    print("=" * 50)
    print("🎯 目标: 生成15-25MB的超精简exe")
    print("=" * 50)
    
    # 彻底清理
    clean_all()
    
    # 超小体积打包
    if build_ultra_minimal():
        print("\n🎉 超小体积打包成功！")
        print("📋 特点:")
        print("   • 🚫 无控制台")
        print("   • 📦 最小依赖")
        print("   • ⚡ 快速启动")
        print("   • 🎯 超小体积")
        
        # 清理spec文件
        if os.path.exists('minimal.spec'):
            os.remove('minimal.spec')
            print("🧹 清理临时文件完成")
    else:
        print("\n❌ 打包失败！")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
