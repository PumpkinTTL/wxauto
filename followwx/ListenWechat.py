from pywechat import listen_on_chat


# 监听文件传输助手
def listen_file_helper():
    listen_on_chat(friend="文件传输助手",duration='1min')


if __name__ == "__main__":
    listen_file_helper()
