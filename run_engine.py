# run_engine.py
import subprocess
import time

# pikafish engine
ENGINE_PATH = "./engine"

def get_best_move(fen, think_time=1000):
    """
    调用 Pikafish 引擎计算最佳一步
    :param fen: 当前棋盘的 FEN 串
    :param think_time: 思考时间 (毫秒)
    :return: 最佳招法 (如 h2e2)，以及分数
    """
    
    # 1. 启动引擎进程
    process = subprocess.Popen(
        ENGINE_PATH,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True, 
        bufsize=1 
    )
    
    try:
        # 2. 发送指令给引擎 (UCI 协议)
        commands = [
            "uci",                # 握手
            "isready",            # 准备
            f"position fen {fen}", # 设置棋盘
            f"go movetime {think_time}" # 开始思考
        ]
        
        for cmd in commands:
            process.stdin.write(cmd + "\n")
        process.stdin.flush()
        
        # 3. 读取结果
        best_move = None
        score = 0
        
        while True:
            line = process.stdout.readline()
            if not line: break
            line = line.strip()
            
            # 抓取分数 (cp 100 代表优势 100分)
            if "score cp" in line:
                try:
                    parts = line.split()
                    idx = parts.index("cp")
                    score = int(parts[idx + 1])
                except: pass
            
            # 抓取绝杀分数 (mate)
            if "score mate" in line:
                try:
                    parts = line.split()
                    idx = parts.index("mate")
                    mate = int(parts[idx + 1])
                    score = 9999 if mate > 0 else -9999
                except: pass

            # 抓取最终招法
            if line.startswith("bestmove"):
                best_move = line.split()[1]
                break 
        
        return best_move, score

    except Exception as e:
        print(f"出错啦: {e}")
        return None, 0
    finally:
        # 记得关闭引擎，不然占内存
        process.kill()

# --- 联合测试：引擎 + 翻译 ---
if __name__ == "__main__":
    from logic import uci_to_chinese # 引入刚才写的翻译官
    
    # 一个标准开局 FEN
    start_fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
    
    print("🤖 正在让皮卡鱼思考...")
    
    # 让它想 0.5 秒
    move, score = get_best_move(start_fen, think_time=500)
    
    if move:
        # 把 h2e2 翻译成 炮二平五
        chn_move = uci_to_chinese(move, start_fen)
        print(f"✅ 引擎计算完毕！")
        print(f"推荐招法: {chn_move} (代码: {move})")
        print(f"当前分数: {score}")
    else:
        print("❌ 引擎没反应，请检查路径对不对")