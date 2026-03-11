import cv2
import numpy as np


def extract_feature(image_path, output_path):
    """提取截图的像素级一致性差异图

    原理: 截图由渲染引擎生成，像素完全精确（无压缩噪声）。
    篡改区域（粘贴、涂抹、文字覆盖）会引入与周围像素不一致的
    微小噪声或边缘过渡。通过比较每个像素与其邻域的一致性，
    异常区域会被高亮。
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法读取图片: {image_path}")

    # 转 LAB 色彩空间，对亮度和色度分别分析
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float64)

    # 对每个通道计算局部标准差
    ksize = 5
    combined = np.zeros(lab.shape[:2], dtype=np.float64)

    for c in range(3):
        channel = lab[:, :, c]
        mu = cv2.blur(channel, (ksize, ksize))
        sq_mu = cv2.blur(channel ** 2, (ksize, ksize))
        std = np.sqrt(np.maximum(sq_mu - mu ** 2, 0))
        combined += std

    # 对纯色/渲染区域，标准差接近0；篡改区域标准差偏高
    # 中值滤波去除单像素噪声
    combined = cv2.medianBlur(combined.astype(np.float32), 3).astype(np.float64)

    norm = cv2.normalize(combined, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    heatmap = cv2.applyColorMap(norm, cv2.COLORMAP_JET)

    cv2.imwrite(output_path, heatmap)
    return output_path
