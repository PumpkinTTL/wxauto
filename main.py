# -*- coding: utf-8 -*-
# 核心库导入
import os
import sys


# 检测是否为打包后的exe运行
def is_frozen():
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


# 如果是打包后的exe，禁用控制台输出
if is_frozen():
    import io

    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

# 第三方库导入
try:
    import webview

    # 检查webview是否可用
    webview_available = True
except ImportError as e:
    print(f"❌ pywebview库导入失败: {e}")
    print("请安装: pip install pywebview")
    webview_available = False
    if not is_frozen():
        sys.exit(1)


# 本地模块导入
try:
    from apis import API
except ImportError as e:
    print(f"❌ APIs模块导入失败: {e}")
    sys.exit(1)

try:
    from sqlite3_util import init_database
except ImportError as e:
    print(f"❌ 数据库模块导入失败: {e}")
    sys.exit(1)

try:
    from task_manager import init_task_manager, stop_task_manager
except ImportError as e:
    print(f"❌ 任务管理器模块导入失败: {e}")
    sys.exit(1)


def show_error_dialog(message):
    """显示错误对话框"""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        messagebox.showerror("启动错误", message)
        root.destroy()
    except:
        print(f"错误: {message}")
        input("按回车键退出...")


def main():
    print("[启动] 办公辅助系统...")

    # 初始化数据库
    print("\n[数据库] 初始化数据库...")
    db_init_success = init_database()
    if not db_init_success:
        print("[错误] 数据库初始化失败，程序退出")
        return

    # 初始化任务管理器
    print("\n[任务管理器] 初始化定时任务管理器...")
    task_manager_success = init_task_manager()
    if not task_manager_success:
        print("[警告] 任务管理器初始化失败，定时功能可能不可用")
    else:
        print("[成功] 任务管理器初始化成功")

    print("\n[API] 初始化API...")
    api = API()

    # 获取web目录和HTML文件路径
    print("\n[界面] 准备启动窗体界面...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    web_dir = os.path.join(current_dir, "web")
    html_path = os.path.join(web_dir, "pages", "index.html")
    
    print(f"   Web目录: {web_dir}")
    print(f"   HTML文件: {html_path}")

    # 确保文件存在
    if not os.path.exists(html_path):
        print(f"[错误] GUI文件不存在: {html_path}")
        return
    else:
        print("[成功] GUI文件存在，准备启动...")

    # 检查webview可用性并启动
    try:
        if not webview_available:
            raise ImportError("pywebview不可用")

        print("\n[窗口] 创建应用窗口...")
        webview.create_window(
            title="智能办公系统v1.4",
            url=html_path,
            width=1560,
            height=900,
            min_size=(1000, 700),
            resizable=True,
            maximized=False,
            js_api=api,
        )
        print("[启动] 启动应用...")
        # 启动webview
        webview.start(debug=True)
        print("[关闭] 应用已关闭")
        # 停止任务管理器
        print("\n[任务管理器] 停止定时任务管理器...")
        stop_task_manager()
        print("[成功] 任务管理器已停止")

    except Exception as e:
        error_msg = f"""启动失败: {str(e)}

可能的解决方案:
1. 安装 .NET Framework 4.7.2 或更高版本
2. 安装 Microsoft Edge WebView2 Runtime
3. 重新安装 Microsoft Visual C++ Redistributable

错误详情: {str(e)}"""

        print(f"[错误] {error_msg}")

        if is_frozen():
            show_error_dialog(error_msg)
        else:
            input("按回车键退出...")


if __name__ == "__main__":
    main()
