# yolo_detector.py
# 把接收的图片，用 YOLO 模型推理，数据交于 fen_converter 用于转换成 FEN

import sys
import cv2 # 用于图像读取
from ultralytics import YOLO
from tool_utils import print_fen_board 

# 导入 FEN 转换核心逻辑
from fen_converter import generate_fen

# --- 配置 ---
MODEL_PATH = "best.pt" 
DEFAULT_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"

# 全局变量，稍后在 try 块中填充
yolo_model = None
CLASS_NAMES = []

# 初始化模型（在程序启动时加载一次）
try:
    print(f"⏳ 正在加载 YOLO 模型: {MODEL_PATH} ...")
    yolo_model = YOLO(MODEL_PATH)
    
    # 自动从模型中读取类别名称，不再需要手动从 data.yaml 中更新
    # model.names 是一个字典 {0: 'b_jiang', 1: 'b_ju', ...}
    # 按 ID 排序转换成列表，确保顺序绝对正确
    model_names_dict = yolo_model.names
    CLASS_NAMES = [model_names_dict[i] for i in sorted(model_names_dict.keys())]
    
    print(f"✅ 成功加载模型。自动识别到的类别顺序:")
    print(CLASS_NAMES)

except Exception as e:
    print(f"❌ 错误：YOLO 模型加载失败。请确认 '{MODEL_PATH}' 文件在根目录下。")
    print(f"错误信息: {e}")
    yolo_model = None 


def detect_and_generate_fen(image_path):
    """
    功能：接收图片路径，使用 YOLO 模型检测，并返回 FEN 字符串。
    
    Args:
        image_path (str): 待检测的图片文件路径。
    """
    
    # 检查模型是否加载成功
    if yolo_model is None:
        print("⚠️ 模型未加载，跳过检测，返回默认 FEN。")
        return DEFAULT_FEN
        
    print(f"2. 正在使用 YOLO 模型检测图片: {image_path}")
    
    # 1. 使用 YOLO 模型进行推理
    results = yolo_model.predict(
        source=image_path, 
        verbose=False, 
        conf=0.4,   # 只有模型确信度超过 40% 的才算数。这能过滤掉绝大多数光点、木纹、阴影等噪点
        save=False, # ❌ 关掉自动保存，这样就不会生成 run/detect/predictxx 文件夹了
        show=False
    )

    # 2. 手动处理并保存图片
    # results 是一个列表（因为 YOLO 支持批量预测），我们只有一张图，所以取 results[0]
    if results:
        r = results[0]
        annotated_frame = r.plot()

        save_path = "uploads/current_board_result.jpg"
        
        # --- 🟢 防止 uploads 文件夹不存在导致保存失败 ---
        import os
        # 获取 save_path 的目录部分 (即 "uploads")
        directory = os.path.dirname(save_path)
        # 如果目录不为空且不存在，就创建它
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        # ----------------------------------------------------

        cv2.imwrite(save_path, annotated_frame)
        print(f"✅ 识别结果已保存至: {save_path}")
        
    # 3. 读取图像尺寸 (用于归一化坐标还原)
    # 注意：重新读取是为了获取宽高，变量名稍微区分一下防止混淆
    img_data = cv2.imread(image_path, cv2.IMREAD_COLOR) 
    if img_data is None:
        print(f"错误：无法读取图片文件 {image_path}")
        return DEFAULT_FEN
    
    # 获取图像高度、宽度
    h, w, _ = img_data.shape 
    
    # 4. 调用 FEN 转换核心逻辑
    # 注意：这里传入的是自动获取的 CLASS_NAMES，永远不会错
    detected_fen = generate_fen(results, w, h, CLASS_NAMES)
    
    if detected_fen is None:
        print("警告：FEN 转换失败，使用默认 FEN。")
        detected_fen = DEFAULT_FEN 
    
    print(f"3. 图片检测完成，真实 FEN: {detected_fen}")

    print_fen_board(detected_fen)
    
    return detected_fen