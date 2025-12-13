# run_engine.py
import subprocess
import time
import os 
from tool_utils import flip_fen, flip_move 

# pikafish 引入
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_PATH = os.path.join(BASE_DIR, "pikafish", "engine")

# 只看老将位置，不看车马炮
def check_is_red_on_top(fen):
    """
    判断是否倒置（红帅在上方）。
    逻辑：
    1. 如果红帅(K)在 0-4 行 -> 倒置
    2. 如果黑将(k)在 5-9 行 -> 倒置 (说明红帅肯定在上)
    3. 其他情况 -> 正常
    """
    rows = fen.split(' ')[0].split('/')
    
    # 寻找 K 和 k 的行号
    red_k_row = -1
    blk_k_row = -1
    
    for i, row in enumerate(rows):
        if 'K' in row: red_k_row = i
        if 'k' in row: blk_k_row = i
            
    # 判定逻辑
    if red_k_row != -1 and red_k_row <= 4: return True
    if blk_k_row != -1 and blk_k_row >= 5: return True
    
    return False

# level=2850 是默认特级大师水平
# level=1800 大概是业余高手
# level=1200 是新手
def get_best_move(fen, think_time=2000, level=2850):
    """
    调用 Pikafish 引擎计算最佳一步
    :param fen: FEN 字符串
    :param think_time: 思考时间(毫秒)
    :param level: 棋力等级 (1350-2850)，默认 2850(最强)
    :return: (best_move, score, pv)
    """
    
    # ================= 1. 倒置检测 =================
    first_part = fen.split(' ')[0]
    first_row = first_part.split('/')[0]
    is_inverted = check_is_red_on_top(fen)
    
    engine_fen = fen
    if is_inverted:
        print(f"🔄 [中间层] 检测到倒置棋盘，翻转 FEN 给引擎...")
        engine_fen = flip_fen(fen)
        print(f"🔄 [中间层] 倒置后的 FEN: {engine_fen}")


    # ================= 2. 启动引擎 =================
    try:
        process = subprocess.Popen(
            ENGINE_PATH,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, 
            bufsize=1 
        )
    except FileNotFoundError:
        print(f"❌ 找不到引擎文件: {ENGINE_PATH}")
        return None, 0, "" 
    
    try:
        # 动态构建指令列表，加入等级设置
        commands = ["uci", "isready"]

        # 如果 level 小于 2850，开启限制模式
        if level < 2850:
            commands.append("setoption name UCI_LimitStrength value true")
            commands.append(f"setoption name UCI_Elo value {level}")
        else:
            # 否则火力全开
            commands.append("setoption name UCI_LimitStrength value false")

        # 继续原本的指令
        commands.append(f"position fen {engine_fen}")
        commands.append(f"go movetime {think_time}")
        
        # 发送指令
        for cmd in commands:
            process.stdin.write(cmd + "\n")
        process.stdin.flush()
        
        # ================= 3. 读取结果 =================
        best_move = None
        score = 0
        pv_str = ""
        
        while True:
            line = process.stdout.readline()
            if not line: break
            line = line.strip()
            
            # 抓取 PV
            if " pv " in line:
                try:
                    parts = line.split(" pv ")
                    if len(parts) > 1:
                        pv_str = parts[1].strip()
                except: pass

            # 抓取分数
            if "score cp" in line:
                try:
                    parts = line.split()
                    idx = parts.index("cp")
                    score = int(parts[idx + 1])
                except: pass
            
            # 抓取绝杀
            if "score mate" in line:
                try:
                    parts = line.split()
                    idx = parts.index("mate")
                    mate = int(parts[idx + 1])
                    score = 9999 if mate > 0 else -9999
                except: pass

            # 抓取最终 bestmove
            if line.startswith("bestmove"):
                parts = line.split()
                if len(parts) > 1:
                    best_move = parts[1]
                    if best_move == "(none)":
                        best_move = None
                break 
        
        # ================= 4. 结果处理与翻转还原 =================
        
        if is_inverted:
            # 1. 翻转最佳招法
            if best_move:
                original_move = best_move
                best_move = flip_move(best_move)
                print(f"🔄 [中间层] 招法翻转: {original_move} -> {best_move}")
            
            # 2. 翻转 PV
            if pv_str:
                moves = pv_str.split()
                flipped_moves = []
                for m in moves:
                    flipped_moves.append(flip_move(m))
                pv_str = " ".join(flipped_moves)
                print(f"🔄 [中间层] PV翻转完成")

        return best_move, score, pv_str

    except Exception as e:
        print(f"❌ 引擎运行出错: {e}")
        return None, 0, ""
    finally:
        if 'process' in locals():
            process.kill()