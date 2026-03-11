import lmdb
import cv2
import numpy as np
import os

def extract_lmdb_to_images(lmdb_path, output_dir):
    """
    将 LMDB 数据库中的图片提取到本地文件夹
    :param lmdb_path: 包含 data.mdb 的文件夹路径
    :param output_dir: 提取后图片保存的路径
    """
    # 1. 创建输出文件夹
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 2. 打开 LMDB 环境 (注意：传入的是包含 mdb 文件的目录，不是文件本身)
    env = lmdb.open(lmdb_path, readonly=True, lock=False, readahead=False, meminit=False)
    
    # 3. 开启事务读取数据
    with env.begin(write=False) as txn:
        cursor = txn.cursor()
        
        count = 0
        print("开始提取图片，请稍候...")
        
        # 4. 遍历数据库中的每一个键值对
        for key, value in cursor:
            # 大多数图像数据集的 key 是图片名（bytes），value 是图像编码（bytes）
            img_name = key.decode('utf-8')
            
            # 如果名字没有后缀，加上 .jpg
            if not img_name.endswith(('.jpg', '.png', '.jpeg')):
                img_name += '.jpg'
                
            # 将 byte 转换为 numpy 数组，再用 OpenCV 解码
            img_array = np.frombuffer(value, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if img is not None:
                # 5. 保存图片到本地
                save_path = os.path.join(output_dir, img_name)
                cv2.imwrite(save_path, img)
                count += 1
                
                # 打印进度
                if count % 100 == 0:
                    print(f"已提取 {count} 张图片...")
            else:
                print(f"警告：图片 {img_name} 解码失败。")

    print(f"提取完成！共提取了 {count} 张图片，保存在: {output_dir}")

# ================= 使用方法 =================
if __name__ == "__main__":
    
    YOUR_LMDB_FOLDER = "./DocTamper_LMDB_Dataset" 
    
    OUTPUT_FOLDER = "./extracted_receipts" 
    
    extract_lmdb_to_images(YOUR_LMDB_FOLDER, OUTPUT_FOLDER)