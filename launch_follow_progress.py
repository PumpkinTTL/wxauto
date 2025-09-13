#!/usr/bin/env python3
import webview
import os

# API类
class ProgressAPI:
    def create_child_progress_window(self):
        try:
            html_path = r"d:\DevelopmentProject\python\wxauto\web\pages\follow_progress.html"
            child_window = webview.create_window(
                title='子进度窗口 - 参半牙膏工厂店',
                url=html_path,
                width=300,
                height=350,
                x=100,
                y=100
            )
            return {"success": True, "message": "子窗口创建成功"}
        except Exception as e:
            return {"success": False, "message": str(e)}

# 主窗口
html_path = r"d:\DevelopmentProject\python\wxauto\web\pages\follow_progress.html"
window = webview.create_window(
    title='跟播进度 - 参半牙膏工厂店',
    url=html_path,
    width=350,
    height=400,
    js_api=ProgressAPI()
)

# 启动
webview.start(debug=False)
