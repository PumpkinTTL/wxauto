#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立测试监听窗口的取消功能
"""

import webview
import sqlite3
import json
import time
from datetime import datetime
windows = {}
class API:
    # 关闭当前窗口
    def closeWindown(self,message):
        print(f"📞 API: 收到关闭请求 - {message}")
        window.destroy()
    # 关闭指定窗口
    def closeWindowById(self,window_id):
        """根据 JS 传来的 window_id 关闭指定窗口"""
        if window_id in windows:
            windows[window_id].destroy()  # 关闭窗口
            del windows[window_id]  # 从字典移除
        else:
            print(f"错误：窗口 {window_id} 不存在！")
    # 创建窗口
    def createWindown(self,name):
        html_content="""
                <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>子界面</title>
        </head>
        <body>
            <button onclick="onClose()">关闭子界面</button>
        </body>
        <script>
            function onClose(){
                pywebview.api.closeWindowById('win2');
            }
        </script>
        </html>
                
        """
        api = API()
        win= webview.create_window(
            title=name,
            html=html_content,
            width=500,
            height=600,
            js_api=api,
            resizable=True
        )
        windows['win2'] = win
        
if __name__ == "__main__":
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>测试</title>
        </head>
        <body>
            <button onclick="onClose()">测试关闭按钮</button>
            <button onclick="createWindown()">创建子界面</button>
        </body>
        <script>
            
            function onClose(){
                pywebview.api.closeWindowById('win1');
                console.log('前端触发关闭');
            }
            
              function createWindown(){
                pywebview.api.createWindown('前端触发创建子界面按钮');
                console.log('前端触发创建子界面按钮');
            }
        </script>
        </html>
            """
        api = API()
        window = webview.create_window(
            title='🧪 跟播进度监控测试',
            html=html_content,
            width=500,
            height=600,
            js_api=api,
            resizable=True
        )
        windows['win1'] = window
        webview.start(debug=True)