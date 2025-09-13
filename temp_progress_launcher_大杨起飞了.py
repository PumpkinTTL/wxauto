#!/usr/bin/env python3
import webview
import os
import sys

# 添加当前目录到Python路径，确保能导入apis模块
sys.path.insert(0, r"d:\DevelopmentProject\python\wxauto")

try:
    from apis import API
    api = API()
except ImportError:
    # 如果导入失败，创建一个简单的API类
    class SimpleAPI:
        pass
    api = SimpleAPI()

# 创建监听窗口
html_path = r"d:\DevelopmentProject\python\wxauto\web\pages\follow_progress.html"
window = webview.create_window(
    title='🎯 跟播进度监控 - 大杨起飞了',
    url=html_path,
    width=450,
    height=600,
    min_size=(400, 500),
    resizable=True,
    js_api=api,
    x=1450,
    y=50
)

# 启动窗口
webview.start(debug=False)
