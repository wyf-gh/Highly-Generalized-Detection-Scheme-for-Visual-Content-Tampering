import cv2
import numpy as np


def _detect_text_regions(gray):
    """
    纯 OpenCV 文字行检测：
    Otsu → 较大水平膨胀核合并字符为行级块 → 面积过滤
    """
    h, w = gray.shape

    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 大核水平膨胀，将同一行文字合并为整行块
    kw = max(15, int(w * 0.05))
    kh = max(3, int(h * 0.006))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kw, kh))
    dilated = cv2.dilate(binary, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    min_area = max(500, w * h * 0.001)
    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        area = bw * bh
        if area > min_area and bw < w * 0.9 and bh < h * 0.9:
            boxes.append((x, y, bw, bh))

    return boxes


def extract_feature(image_path, output_path):
    """
    生成文字区域异常标注图（只高亮异常区域）：
    1. SRM 滤波器计算噪声残差
    2. OpenCV 检测文字行区域
    3. 用 Z-score 统计找出异常偏高的区域
    4. 只对异常区域绘制红色标注框+半透明填充，正常区域不画
    """
    img_color = cv2.imread(image_path)
    img_gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img_color is None:
        raise ValueError(f"无法读取图片: {image_path}")

    img_float = img_gray.astype(np.float64)
    h, w = img_gray.shape

    # ---- SRM 高通滤波器 ----
    filters = [
        np.array([[0, 0, 0], [0, -1, 1], [0, 0, 0]], dtype=np.float64),
        np.array([[0, 0, 0], [0, -1, 0], [0, 1, 0]], dtype=np.float64),
        np.array([[0, 0, 0], [1, -2, 1], [0, 0, 0]], dtype=np.float64),
        np.array([[0, 1, 0], [0, -2, 0], [0, 1, 0]], dtype=np.float64),
        np.array([[-1, 2, -1], [2, -4, 2], [-1, 2, -1]], dtype=np.float64),
        np.array([[-1, 2, -2, 2, -1],
                  [2, -6, 8, -6, 2],
                  [-2, 8, -12, 8, -2],
                  [2, -6, 8, -6, 2],
                  [-1, 2, -2, 2, -1]], dtype=np.float64) / 12.0,
    ]

    residual = np.zeros_like(img_float)
    for f in filters:
        residual += np.abs(cv2.filter2D(img_float, cv2.CV_64F, f))
    residual = cv2.blur(residual, (7, 7))

    # ---- 文字行检测 ----
    boxes = _detect_text_regions(img_gray)

    if not boxes:
        cv2.imwrite(output_path, img_color)
        return output_path

    # ---- 计算每个区域的 SRM 原始均值 (不做全局归一化) ----
    scores = []
    for (x, y, bw, bh) in boxes:
        region = residual[y:y + bh, x:x + bw]
        scores.append(float(region.mean()))

    scores_arr = np.array(scores)
    mean_score = scores_arr.mean()
    std_score = scores_arr.std()

    # ---- 只标注统计异常区域 (Z-score > 1.0) ----
    overlay = img_color.copy()
    fill_layer = img_color.copy()

    thickness = max(2, int(min(w, h) * 0.006))
    font_scale = max(0.35, min(w, h) * 0.0012)
    suspicious_count = 0

    for i, (x, y, bw, bh) in enumerate(boxes):
        x2 = min(w - 1, x + bw)
        y2 = min(h - 1, y + bh)

        z = (scores[i] - mean_score) / (std_score + 1e-10)

        if z > 1.0:
            # 异常区域：红色框 + 半透明填充
            color = (0, 0, 255)
            cv2.rectangle(overlay, (x, y), (x2, y2), color, thickness)
            cv2.rectangle(fill_layer, (x, y), (x2, y2), (0, 0, 255), cv2.FILLED)

            label = f"z={z:.1f}"
            cv2.putText(overlay, label, (x, max(y - 6, 14)),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2, cv2.LINE_AA)
            suspicious_count += 1

        elif z > 0.5:
            # 轻微偏高：黄色细框
            color = (0, 200, 255)
            cv2.rectangle(overlay, (x, y), (x2, y2), color, max(1, thickness // 2))

    # 混合填充
    alpha = 0.3 if suspicious_count > 0 else 0
    cv2.addWeighted(fill_layer, alpha, overlay, 1 - alpha, 0, overlay)

    cv2.imwrite(output_path, overlay)
    return output_path
