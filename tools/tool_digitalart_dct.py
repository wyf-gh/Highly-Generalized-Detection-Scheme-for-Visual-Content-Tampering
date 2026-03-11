import cv2
import numpy as np


def extract_feature(image_path, output_path):
    """提取 AI 生成图像 / 数字艺术的 DCT 频域异常特征

    原理: 真实照片在 DCT 频域有自然衰减的频谱分布，
    而 AI 生成或 CG 图像、以及局部篡改区域会破坏这种分布。
    对图像分块做 DCT，提取每块的高频能量占比，
    异常高或异常低的区域可能被篡改或 AI 生成。
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"无法读取图片: {image_path}")

    img_float = img.astype(np.float64)
    h, w = img_float.shape

    block_size = 8
    # 裁剪到 block_size 的整数倍
    h_crop = (h // block_size) * block_size
    w_crop = (w // block_size) * block_size
    img_crop = img_float[:h_crop, :w_crop]

    energy_map = np.zeros((h_crop // block_size, w_crop // block_size), dtype=np.float64)

    for i in range(0, h_crop, block_size):
        for j in range(0, w_crop, block_size):
            block = img_crop[i:i + block_size, j:j + block_size]
            dct_block = cv2.dct(block)

            # 总能量
            total = np.sum(dct_block ** 2)
            # 高频能量 (排除左上角 3x3 的低频系数)
            low_freq = dct_block[:3, :3].copy()
            high_freq_energy = total - np.sum(low_freq ** 2)

            ratio = high_freq_energy / (total + 1e-10)
            energy_map[i // block_size, j // block_size] = ratio

    # 上采样回原图尺寸
    energy_full = cv2.resize(energy_map, (w_crop, h_crop), interpolation=cv2.INTER_LINEAR)

    # 如果原图比裁剪后大，补边
    if energy_full.shape != (h, w):
        padded = np.zeros((h, w), dtype=np.float64)
        padded[:h_crop, :w_crop] = energy_full
        energy_full = padded

    # 归一化
    hf_norm = cv2.normalize(energy_full, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    heatmap = cv2.applyColorMap(hf_norm, cv2.COLORMAP_JET)

    cv2.imwrite(output_path, heatmap)
    return output_path
