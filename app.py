# app.py

from flask import Flask, request, Response 
import json
import os 
from core_flow import process_chess_image

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def make_json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False), 
        mimetype='application/json; charset=utf-8',
        status=status
    )

@app.route('/analyze', methods=['POST'])
def analyze():
    print("\n📱 [收到请求] ...")
    
    # --- 1. HTTP 层：接收文件 ---
    if 'file' not in request.files:
        return make_json_response({"title": "上传失败", "body": "没收到图片"}, 400)
    
    file = request.files['file']
    if file.filename == '':
        return make_json_response({"title": "上传失败", "body": "文件名为空"}, 400)

    # --- 2. 存储层：保存文件 ---
    # 时间戳，防止多线程并发时图片互相覆盖
    # save_path = os.path.join(UPLOAD_FOLDER, f"board_{int(time.time())}.jpg")
    save_path = os.path.join(UPLOAD_FOLDER, "current_board.jpg")
    
    try:
        file.save(save_path)
        print(f"✅ 图片已保存: {save_path}")
    except Exception as e:
        return make_json_response({"title": "保存失败", "body": str(e)}, 500)
    
    # --- 3. 逻辑层：调用指挥官 ---
    try:
        result = process_chess_image(save_path)
        
        if result.get("error"):
            return make_json_response(result) # 依然是 200 OK，只是业务逻辑上的无解
        else:
            return make_json_response(result)
            
    except Exception as e:
        print(f"❌ 严重错误: {e}")
        return make_json_response({"title": "系统错误", "body": "服务器内部报错"}, 500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)