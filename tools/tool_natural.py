import cv2
import numpy as np

def extract_feature(image_path, output_path, quality=90):
    """提取自然图像的 ELA 特征"""
    original = cv2.imread(image_path)
    if original is None: 
        raise ValueError(f"无法读取图片: {image_path}")
        
    # 二次压缩与求差
    _, encoded = cv2.imencode('.jpg', original, [cv2.IMWRITE_JPEG_QUALITY, quality])
    compressed = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    diff = cv2.absdiff(original, compressed)
    
    # 灰度化与归一化拉伸
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    ela_enhanced = cv2.normalize(gray_diff, None, 0, 255, cv2.NORM_MINMAX)
    
    # 转换为 Agent B 最喜欢的彩色热力图
    heatmap = cv2.applyColorMap(ela_enhanced, cv2.COLORMAP_JET)
    cv2.imwrite(output_path, heatmap)
    return output_path