# gpt4o_chat.py
import openai
from myhexin.config_manager import ConfigManager

def chat_with_gpt4o(prompt: str, system_prompt: str = "你是一个乐于助人的助手"):
    # 加载配置并设置 API key
    cfg = ConfigManager().validate_and_setup()
    openai.api_key = cfg['openai_api_key']

    # 调用 GPT-5 模型
    response = openai.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )

    # 输出回复
    reply = response.choices[0].message.content
    print("🤖 GPT-5 回复：\n", reply)
    return reply

if __name__ == "__main__":
    user_input = input("请输入你的问题：")
    chat_with_gpt4o(user_input)