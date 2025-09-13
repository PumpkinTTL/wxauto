#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最精简的webview测试
"""

import webview

class API:
    def __init__(self):
        self.window_ref = None
    
    def closeWindown(self, message):
        """关闭窗口"""
        print(f"📞 API: 收到关闭请求 - {message}")
        
        if self.window_ref:
            print("🔄 正在关闭窗口...")
            self.window_ref.destroy()
            print("✅ 窗口已关闭")
        else:
            print("❌ 窗口引用为空")

def main():
    print("🧪 最精简测试")
    
    # HTML内容
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
    </body>
    <script>
        function onClose(){
            console.log('🔥 DEBUG: onClose函数被调用');
            console.log('🔥 DEBUG: pywebview类型:', typeof pywebview);
            console.log('🔥 DEBUG: pywebview.api类型:', typeof pywebview?.api);
            console.log('🔥 DEBUG: closeWindown函数类型:', typeof pywebview?.api?.closeWindown);
            
            pywebview.api.closeWindown('前端触发按钮');
        }
    </script>
    </html>
    """
    
    # 创建API
    api = API()
    
    # 创建窗口
    window = webview.create_window(
        title='测试',
        html=html_content,
        width=300,
        height=200,
        js_api=api
    )
    
    # 保存窗口引用
    api.window_ref = window
    
    print("✅ 窗口创建成功")
    
    # 启动
    webview.start(debug=True)
    
    print("🔄 程序结束")

if __name__ == "__main__":
    main()
