from flask import Flask, jsonify
# 引入这个万能库
from openai import OpenAI
from run_engine import get_best_move
from logic import uci_to_chinese

app = Flask(__name__)
# 让手机浏览器能直接显示中文
app.config['JSON_AS_ASCII'] = False

# ---这是 DeepSeek 的配置---
# 1. 你的 API Key (去 deepseek 官网申请的那个 sk-开头的)
API_KEY = "REMOVED_API_KEY" 
# 2. 关键！这里把地址改成了 DeepSeek，而不是 ChatGPT
BASE_URL = "https://api.deepseek.com"

# 初始化连接
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

DEFAULT_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"

def ask_deepseek(fen, move_chn, score):
    """专门负责跟 DeepSeek 聊天的函数"""
    print("正在呼叫 DeepSeek...")
    
    prompt = f"""
    你是象棋大师。
    当前局面: {fen}
    引擎推荐: {move_chn}
    分数: {score}
    请用60字以内解释这步棋的意图，犀利一点。
    """
    
    try:
        # 这里虽然调用的叫 chat.completions，但连的是 DeepSeek 服务器
        response = client.chat.completions.create(
            model="deepseek-chat", # 这一行指定用 DeepSeek 模型
            messages=[
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"DeepSeek 报错: {e}")
        return "（教练掉线了，没说话）"

@app.route('/analyze', methods=['GET'])
def analyze():
    print("1. 引擎计算中...")
    best_move_uci, score = get_best_move(DEFAULT_FEN, think_time=500)
    
    if best_move_uci:
        chinese_move = uci_to_chinese(best_move_uci, DEFAULT_FEN)
        
        # 调用上面的函数去问 DeepSeek
        advice = ask_deepseek(DEFAULT_FEN, chinese_move, score)
        
        return jsonify({
            "title": f"推荐：{chinese_move} ({score})",
            "body": advice 
        })
    else:
        return jsonify({"title": "错误", "body": "引擎没反应"})

if __name__ == '__main__':
    # 端口 5001
    app.run(host='0.0.0.0', port=5001)