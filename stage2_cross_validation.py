import os
import sys
import base64
from openai import OpenAI
from stage1_scene_classifier import classify_scene, encode_image, API_KEY, BASE_URL, MODEL_NAME
from stage2_feature_extractor import run_stage2

# 从独立文件导入各场景的 Prompt
import prompts.prompt_document as prompt_document
import prompts.prompt_natural as prompt_natural
import prompts.prompt_digitalart as prompt_digitalart
import prompts.prompt_screenshot as prompt_screenshot


# =============================================================
# 场景 → Prompt 映射 (从独立文件加载)
# =============================================================
AGENT_A_PROMPTS = {
    "Document":    prompt_document.AGENT_A_PROMPT,
    "Natural":     prompt_natural.AGENT_A_PROMPT,
    "Digital_Art": prompt_digitalart.AGENT_A_PROMPT,
    "Screenshot":  prompt_screenshot.AGENT_A_PROMPT,
}

AGENT_B_PROMPTS = {
    "Document":    prompt_document.AGENT_B_PROMPT,
    "Natural":     prompt_natural.AGENT_B_PROMPT,
    "Digital_Art": prompt_digitalart.AGENT_B_PROMPT,
    "Screenshot":  prompt_screenshot.AGENT_B_PROMPT,
}


# =============================================================
# VLM 调用工具
import httpx

# =============================================================
def _call_vlm(image_paths, prompt):
    """向 VLM 发送一张或多张图片 + 文本 prompt，流式返回结果"""
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout=httpx.Timeout(connect=30, read=300, write=30, pool=30),
    )

    content = [{"type": "text", "text": prompt}]
    for p in image_paths:
        b64 = encode_image(p)
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
        })

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": content}],
        stream=True,
    )

    result = ""
    for chunk in response:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
            result += delta.content
    print()
    return result.strip()


# =============================================================
# Agent 运行函数
# =============================================================
def run_agent_a(image_path, scene_key):
    """Agent A：语义侦探 — 只看原图"""
    prompt = AGENT_A_PROMPTS.get(scene_key)
    if prompt is None:
        print(f"[Agent A] 暂不支持场景: {scene_key}")
        return ""
    print("-" * 50)
    print("[Agent A] 语义侦探分析中...\n")
    return _call_vlm([image_path], prompt)


def run_agent_b(feature_paths, scene_key):
    """Agent B：痕迹专家 — 只看特征图"""
    prompt = AGENT_B_PROMPTS.get(scene_key)
    if prompt is None:
        print(f"[Agent B] 暂不支持场景: {scene_key}")
        return ""
    if not feature_paths:
        print("[Agent B] 无可用特征图，跳过。")
        return ""
    print("-" * 50)
    print("[Agent B] 痕迹专家分析中...\n")
    return _call_vlm(feature_paths, prompt)


# =============================================================
# 交叉验证摘要
# =============================================================
def print_cross_validation(agent_a_result, agent_b_result):
    print("\n" + "=" * 60)
    print("          交叉验证摘要 (Cross-Validation)")
    print("=" * 60)

    print("\n[Agent A — 语义侦探] 发现:")
    print(agent_a_result if agent_a_result else "  (无输出)")

    print("\n[Agent B — 痕迹专家] 发现:")
    print(agent_b_result if agent_b_result else "  (无输出)")

    print("\n" + "-" * 60)
    a_found = "ANOMALIES FOUND: 0" not in agent_a_result
    b_found = "TAMPERED REGIONS: 0" not in agent_b_result

    if a_found and b_found:
        verdict = "双重确认 — Agent A 和 Agent B 均发现异常，篡改可能性高。"
    elif a_found or b_found:
        verdict = "单方发现 — 仅一个 Agent 发现异常，需进一步审查。"
    else:
        verdict = "未发现明显篡改痕迹。"

    print(f"综合判定: {verdict}")
    print("=" * 60)


# =============================================================
# 主程序：Stage1 → 特征提取 → Agent A + B → 交叉验证
# =============================================================
if __name__ == "__main__":
    image_path = "./extracted_receipts/image-000000001.jpg"
    if len(sys.argv) > 1:
        image_path = sys.argv[1]

    print("=" * 60)
    print(f"  篡改检测流水线 — {image_path}")
    print("=" * 60)

    # ---- Stage 1: 场景分类 ----
    print("\n>>> Stage 1: 场景分类")
    scene_type = classify_scene(image_path)
    print(f"分类结果: {scene_type}")

    # 匹配场景关键词
    scene_key = None
    for key in AGENT_A_PROMPTS:
        if key.lower() in scene_type.lower():
            scene_key = key
            break
    if scene_key is None:
        print(f"暂不支持场景类型: {scene_type}")
        sys.exit(1)

    # ---- 特征提取 ----
    print("\n>>> 特征提取")
    feature_paths = run_stage2(image_path, scene_type)
    print(f"生成特征图: {feature_paths}")

    # ---- Stage 2: 盲审交叉验证 ----
    print("\n>>> Stage 2: 领域自适应盲审交叉验证")

    agent_a_result = run_agent_a(image_path, scene_key)
    agent_b_result = run_agent_b(feature_paths, scene_key)

    # ---- 交叉验证 ----
    print_cross_validation(agent_a_result, agent_b_result)
