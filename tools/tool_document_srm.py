import cv2
import numpy as np


def extract_feature(image_path, output_path):
    """提取文档图像的 SRM (Spatial Rich Model) 噪声残差特征，用于检测篡改区域"""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"无法读取图片: {image_path}")

    img_float = img.astype(np.float64)

    # ---- SRM 高通滤波器组 ----
    # 1st-order 边缘残差
    f1_h = np.array([[0, 0, 0],
                     [0, -1, 1],
                     [0, 0, 0]], dtype=np.float64)
    f1_v = np.array([[0, 0, 0],
                     [0, -1, 0],
                     [0, 1, 0]], dtype=np.float64)

    # 2nd-order 边缘残差
    f2_h = np.array([[0, 0, 0],
                     [1, -2, 1],
                     [0, 0, 0]], dtype=np.float64)
    f2_v = np.array([[0, 1, 0],
                     [0, -2, 0],
                     [0, 1, 0]], dtype=np.float64)

    # 3rd-order SQUARE 滤波器
    f3_square = np.array([[0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0],
                          [0, 1, -3, 3, -1],
                          [0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0]], dtype=np.float64)

    # EDGE 3x3 滤波器
    f_edge3 = np.array([[-1, 2, -1],
                        [2, -4, 2],
                        [-1, 2, -1]], dtype=np.float64)

    # SQUARE 5x5 滤波器 (经典 SRM 核心)
    f_square5 = np.array([[-1, 2, -2, 2, -1],
                          [2, -6, 8, -6, 2],
                          [-2, 8, -12, 8, -2],
                          [2, -6, 8, -6, 2],
                          [-1, 2, -2, 2, -1]], dtype=np.float64) / 12.0

    filters = [f1_h, f1_v, f2_h, f2_v, f3_square, f_edge3, f_square5]

    # ---- 对每个滤波器计算残差并融合 ----
    residual_sum = np.zeros_like(img_float)

    for f in filters:
        res = cv2.filter2D(img_float, cv2.CV_64F, f)
        residual_sum += np.abs(res)

    # 局部平均聚合 —— 使篡改区域更连续、更明显
    residual_avg = cv2.blur(residual_sum, (7, 7))

    # 归一化到 0-255
    srm_norm = cv2.normalize(residual_avg, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # 生成彩色热力图
    heatmap = cv2.applyColorMap(srm_norm, cv2.COLORMAP_JET)
    cv2.imwrite(output_path, heatmap)
    return output_path
