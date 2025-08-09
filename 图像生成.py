# generate_image.py
import openai
from myhexin.config_manager import ConfigManager

def generate_image(prompt: str):
    # 加载配置
    config = ConfigManager().validate_and_setup()
    model = config['image_generation']['provider']
    dalle_config = config['image_generation'].get(model, {})

    # 设置 API Key
    openai.api_key = config['openai_api_key']

    # 调用 OpenAI 图像生成接口
    response = openai.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        style="natural",
        n=1
    )

    # 获取图片 URL
    image_url = response.data[0].url
    print(f"✅ 成功生成图片：{image_url}")
    return image_url


if __name__ == "__main__":
    prompt = input("请输入图片生成描述（Prompt）：")
    generate_image(prompt)