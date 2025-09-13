import webview
import threading

class Api:
    def __init__(self):
        self.child_windows = []
    
    def create_child_window(self):
        """创建子窗口的方法（由JS调用）"""
        def create_child():
            # 使用双大括号 {{ }} 来转义 CSS 中的大括号
            child_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        padding: 20px;
                        text-align: center;
                    }}
                    button {{
                        padding: 8px 16px;
                        background-color: #f44336;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                    }}
                </style>
            </head>
            <body>
                <h2>子窗口</h2>
                <p>这是新建的子窗口</p>
                <button onclick="window.close()">关闭窗口</button>
                <p>窗口ID: {window_id}</p>
            </body>
            </html>
            """.format(window_id=len(self.child_windows) + 1)
            
            child_window = webview.create_window(
                f'子窗口 #{len(self.child_windows) + 1}',
                html=child_html,
                width=400,
                height=300,
                x=100 + (len(self.child_windows) * 30),
                y=100 + (len(self.child_windows) * 30)
            )
            
            def on_closed():
                print(f"子窗口 #{len(self.child_windows)} 已关闭")
                self.child_windows.remove(child_window)
            
            child_window.events.closed += on_closed
            self.child_windows.append(child_window)
            webview.start()
        
        threading.Thread(target=create_child).start()

def main():
    """主程序入口"""
    api = Api()
    
    # 主窗口 HTML 也需要转义 CSS 大括号
    main_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 20px;
                text-align: center;
            }}
            button {{
                padding: 10px 20px;
                font-size: 16px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }}
            button:hover {{
                background-color: #45a049;
            }}
        </style>
    </head>
    <body>
        <h1>主窗口</h1>
        <p>点击下方按钮创建子窗口</p>
        <button onclick="createChildWindow()">新建子窗口</button>
    </body>
    <script>
        function createChildWindow() {{
            pywebview.api.create_child_window()
                .catch(error => console.error('调用失败:', error));
        }}
    </script>
    </html>
    """
    
    main_window = webview.create_window(
        '主窗口 - pywebview 示例',
        html=main_html,
        js_api=api,
        width=600,
        height=400,
        resizable=True
    )
    
    webview.start(debug=True)

if __name__ == '__main__':
    main()