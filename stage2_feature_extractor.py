import os
import sys
from stage1_scene_classifier import classify_scene


# -------------------------------------------------------
# 场景 → 工具映射
# -------------------------------------------------------
SCENE_TOOLS = {
    "Natural": [
        ("tools.tool_natural", "ela"),                   # ELA 压缩差异
    ],
    "Document": [
        ("tools.tool_document_srm", "srm"),              # SRM 噪声残差热力图
        ("tools.tool_document_ocr_diff", "ocr_diff"),    # 文字区域异常标注图
    ],
    "Digital_Art": [
        ("tools.tool_digitalart_dct", "dct"),            # DCT 频域异常
        ("tools.tool_natural", "ela"),                   # ELA (复用，AI图也有压缩痕迹差异)
    ],
    "Screenshot": [
        ("tools.tool_document_srm", "srm"),              # SRM 噪声残差 (复用)
        ("tools.tool_screenshot_pixel", "pixel_diff"),   # 像素一致性差异
    ],
}


def run_stage2(image_path, scene_type, output_dir="./output"):
    """
    根据 stage1 的分类结果，调用对应的特征提取工具，
    输出可视化热力图保存到 output_dir。
    """
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(image_path))[0]

    # 清理分类结果（去掉可能的多余文字）
    scene_key = None
    for key in SCENE_TOOLS:
        if key.lower() in scene_type.lower():
            scene_key = key
            break

    if scene_key is None:
        print(f"[Stage2] 暂无工具支持场景类型: {scene_type}，跳过特征提取。")
        return []

    tools = SCENE_TOOLS[scene_key]
    results = []

    for module_name, tag in tools:
        # 动态导入对应工具模块
        import importlib
        module = importlib.import_module(module_name)
        out_path = os.path.join(output_dir, f"{tag}_{base_name}.jpg")

        print(f"[Stage2] 正在运行 {module_name}.extract_feature → {out_path}")
        module.extract_feature(image_path, out_path)
        results.append(out_path)
        print(f"[Stage2] 已保存: {out_path}")

    return results


# -------------------------------------------------------
# 主程序：stage1 → stage2 完整流水线
# -------------------------------------------------------
if __name__ == "__main__":
    # 默认测试图片，可通过命令行参数覆盖
    image_path = "./extracted_receipts/image-000000001.jpg"
    if len(sys.argv) > 1:
        image_path = sys.argv[1]

    print("=" * 50)
    print(f"[Pipeline] 输入图片: {image_path}")
    print("=" * 50)

    # ---- Stage 1: 场景分类 ----
    print("\n>>> Stage 1: 场景分类")
    scene_type = classify_scene(image_path)
    print(f"[Stage1] 分类结果: {scene_type}")

    # ---- Stage 2: 特征提取 ----
    print("\n>>> Stage 2: 特征提取")
    output_files = run_stage2(image_path, scene_type)

    # ---- 汇总 ----
    print("\n" + "=" * 50)
    if output_files:
        print(f"[Pipeline] 完成！共生成 {len(output_files)} 张特征图:")
        for f in output_files:
            print(f"  - {f}")
    else:
        print("[Pipeline] 未生成特征图。")
    print("=" * 50)
