import base64
from openai import OpenAI


# -----------------------------
# 配置
# -----------------------------
API_KEY = "sk-pxizupebbwgijptggmseledfboqcfcqcjltbfiucswhxicow"
BASE_URL = "https://api.siliconflow.cn/v1"

MODEL_NAME = "Qwen/Qwen3-VL-8B-Instruct"


# -----------------------------
# 图片转 base64
# -----------------------------
def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# -----------------------------
# Scene 分类 Agent
# -----------------------------
def classify_scene(image_path):

    base64_image = encode_image(image_path)

    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL
    )

    prompt = """
You are the scene classification module of an image forensic system.

Your task is to classify the input image into ONE of the following categories:

1. Natural
   - photos taken by camera
   - landscapes
   - people
   - real-world scenes

2. Document
   - scanned documents
   - receipts
   - invoices
   - white background with text

3. Digital_Art
   - AI generated images
   - computer graphics
   - illustrations

4. Screenshot
   - UI interface
   - chat screenshots
   - mobile or computer screen captures

Rules:
- Output ONLY the category name
- Do not explain
- Do not output anything else
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        stream=True
    )

    print("Scene Classification Result: ", end="")

    result = ""

    for chunk in response:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta

        if delta.content:
            print(delta.content, end="", flush=True)
            result += delta.content

    print("\n")

    return result.strip()


# -----------------------------
# 主程序
# -----------------------------
if __name__ == "__main__":

    image_path = "./extracted_receipts/image-000000001.jpg"

    scene = classify_scene(image_path)

    print("Final Scene Type:", scene)