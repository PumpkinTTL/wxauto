#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最简单的webview窗口关闭测试
"""

import webview

class SimpleAPI:
    def __init__(self):
        self.window_ref = None
    
    def close_window(self):
        """关闭窗口"""
        print("📞 API: 收到关闭窗口请求")
        
        if self.window_ref:
            print("🔄 正在关闭窗口...")
            try:
                self.window_ref.destroy()
                print("✅ 窗口已关闭")
                return {"success": True, "message": "窗口已关闭"}
            except Exception as e:
                print(f"❌ 关闭窗口失败: {e}")
                return {"success": False, "message": f"关闭失败: {e}"}
        else:
            print("❌ 窗口引用为空")
            return {"success": False, "message": "窗口引用为空"}

def main():
    """主函数"""
    print("🧪 最简单的窗口关闭测试")
    
    # 创建API实例
    api = SimpleAPI()
    
    # 最简单的HTML
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>简单测试</title>
        <meta charset="UTF-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                padding: 50px;
                text-align: center;
                background: #f0f0f0;
            }
            button {
                padding: 20px 40px;
                font-size: 18px;
                background: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            button:hover {
                background: #d32f2f;
            }
            .log {
                margin-top: 20px;
                padding: 10px;
                background: white;
                border-radius: 5px;
                text-align: left;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <h2>🧪 简单窗口关闭测试</h2>
        <button onclick="closeWindow()">关闭窗口</button>
        
        <div class="log" id="log">
            <div>📋 页面已加载</div>
        </div>
        
        <script>
            function addLog(message) {
                const log = document.getElementById('log');
                const div = document.createElement('div');
                div.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
                log.appendChild(div);
            }
            
            async function closeWindow() {
                try {
                    addLog('🔥 DEBUG: closeWindow 函数被调用');
                    
                    // 检查API
                    addLog('🔥 DEBUG: window.pywebview类型: ' + typeof window.pywebview);
                    addLog('🔥 DEBUG: window.pywebview.api类型: ' + typeof window.pywebview?.api);
                    addLog('🔥 DEBUG: close_window函数类型: ' + typeof window.pywebview?.api?.close_window);
                    
                    if (window.pywebview && window.pywebview.api && window.pywebview.api.close_window) {
                        addLog('📞 正在调用关闭API...');
                        const result = await window.pywebview.api.close_window();
                        addLog('✅ API调用结果: ' + JSON.stringify(result));
                    } else {
                        addLog('❌ API不可用');
                    }
                    
                } catch (error) {
                    addLog('❌ 异常: ' + error.message);
                    console.error('关闭窗口异常:', error);
                }
            }
            
            // 页面加载完成后检查API
            window.addEventListener('load', () => {
                addLog('✅ 页面加载完成');
                
                setTimeout(() => {
                    if (window.pywebview && window.pywebview.api) {
                        addLog('✅ API已准备就绪');
                        addLog('📋 可用方法: ' + Object.getOwnPropertyNames(window.pywebview.api).join(', '));
                    } else {
                        addLog('❌ API未准备');
                    }
                }, 1000);
            });
        </script>
    </body>
    </html>
    """
    
    # 创建窗口
    window = webview.create_window(
        title='🧪 简单关闭测试',
        html=html_content,
        width=400,
        height=300,
        js_api=api,
        resizable=True
    )
    
    # 保存窗口引用
    api.window_ref = window
    
    print("✅ 窗口创建成功")
    print("📋 请点击'关闭窗口'按钮测试")
    
    # 启动webview
    webview.start(debug=True)
    
    print("🔄 程序结束")

if __name__ == "__main__":
    main()
