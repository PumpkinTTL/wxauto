from openai import OpenAI

# sk-WJElSrFaD3Qn0BjQLDfEkV0vLNVjZGp7f1z6GwzZjYWHagkv


class AI:
    def __init__(self):
        self.MdClient = OpenAI(
            base_url="https://api-inference.modelscope.cn/v1",
            api_key="ms-5f8d23a7-14b6-4d43-828c-c46dee1a40e2",
        )
        self.HyClient = OpenAI(
            base_url="https://api.hunyuan.cloud.tencent.com/v1",
            api_key="sk-WJElSrFaD3Qn0BjQLDfEkV0vLNVjZGp7f1z6GwzZjYWHagkv",
        )

    def requestMdDeepSeekV3_1(self, messages, stream=False):
        response = self.MdClient.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3.1",
            messages=messages,
            stream=stream,
        )

        if stream:
            full_response = ""
            for chunk in response:
                content_chunk = chunk.choices[0].delta.content
                if content_chunk:
                    full_response += content_chunk
                    yield content_chunk  # 流式返回数据块
        else:
            return response.choices[0].message.content

    def rquestHyLite(self, messages, stream=False):
        response = self.HyClient.chat.completions.create(
            model="hunyuan-lite",
            messages=messages,
            stream=stream,
        )
        if stream:
            full_response = ""
            for chunk in response:
                content_chunk = chunk.choices[0].delta.content
                if content_chunk:
                    full_response += content_chunk
                    yield content_chunk  # 流式返回数据块
        else:
            return response.choices[0].message.content


if __name__ == "__main__":
    ai = AI()
    conversation_history = []  # 在 main 中管理历史

    # 示例对话
    print("AI: 你好！我是你的助手，请问有什么可以帮你的？")
    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() in ["退出", "exit", "q"]:
            print("AI: 再见！")
            break

        # 添加用户输入到历史
        conversation_history.append({"role": "user", "content": user_input})

        # 流式调用
        print("AI: ", end="", flush=True)
        full_response = ""
        for chunk in ai.requestMdDeepSeekV3_1(conversation_history, stream=True):
            print(chunk, end="", flush=True)  # 实时输出
            full_response += chunk

        # 将AI回复添加到历史
        conversation_history.append({"role": "assistant", "content": full_response})
