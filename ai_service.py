from openai import OpenAI
import sys
import io
import re
import os
from contextlib import redirect_stdout

# 引用你的工具
from tool_utils import print_fen_board

# --- 配置 ---
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = "https://api.deepseek.com"

if not API_KEY:
    print("❌ 错误: 未找到 API_KEY，请检查 .env 文件配置")
    sys.exit(1)

try:
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    print("✅ DeepSeek Client 初始化成功.")
except Exception as e:
    sys.exit(1)

# --- 1. 抓取字符棋盘 (复用 tool_utils) ---
def get_board_string_from_tool(fen):
    f = io.StringIO()
    with redirect_stdout(f):
        print_fen_board(fen)
    raw_output = f.getvalue()
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', raw_output)

# --- 2. 把 FEN 翻译成文字版坐标清单 ---
def get_piece_locations(fen):
    """
    解析 FEN，生成详细的棋子位置列表。
    例如：
    红方棋子：帅[E列9行], 车[I列9行]...
    黑方棋子：将[E列0行], 砲[B列2行]...
    """
    board_part = fen.split(" ")[0]
    rows = board_part.split("/")
    
    # 坐标列号映射 A-I
    col_labels = "ABCDEFGHI"
    
    red_pieces = []
    blk_pieces = []
    
    # 棋子名称映射
    names = {
        'R':'红车', 'N':'红马', 'B':'红相', 'A':'红仕', 'K':'红帅', 'C':'红炮', 'P':'红兵',
        'r':'黑車', 'n':'黑馬', 'b':'黑象', 'a':'黑士', 'k':'黑将', 'c':'黑砲', 'p':'黑卒'
    }

    # 遍历每一行
    for r_idx, row_str in enumerate(rows):
        c_idx = 0 # 当前列索引 (0-8)
        for char in row_str:
            if char.isdigit():
                #如果是数字，跳过对应数量的格子
                c_idx += int(char)
            else:
                # 是棋子
                col_name = col_labels[c_idx] # 获取 A-I
                pos_desc = f"{col_name}{r_idx}" # 例如 E9, A0
                
                piece_name = names.get(char, char)
                full_desc = f"{piece_name}({pos_desc})"
                
                if char.isupper():
                    red_pieces.append(full_desc)
                else:
                    blk_pieces.append(full_desc)
                
                c_idx += 1
                
    return f"【红方棋子清单】: {', '.join(red_pieces)}\n【黑方棋子清单】: {', '.join(blk_pieces)}"

# --- 3. 动态判断阵地防伪 ---
def get_orientation_desc(fen):
    """
    根据 FEN 判断谁在上方，谁在下方。
    逻辑：扫描 FEN 的最后几行（棋盘底部，也就是用户这一侧）。
    """
    try:
        # 取出棋盘部分
        board_part = fen.split(" ")[0]
        rows = board_part.split("/")
        
        # 取出最下面的 3 行 (用户阵地)
        bottom_area = "".join(rows[-3:])
        
        # 判断：下面是谁
        if 'K' in bottom_area:
            # 红帅(K)在下面 -> 用户是红方
            return "(位置：上方为黑方阵地，下方为红方阵地)"
        elif 'k' in bottom_area:
            # 黑将(k)在下面 -> 用户是黑方
            return "(位置：上方为红方阵地，下方为黑方阵地)"
        else:
            # 兜底：如果老将都跑出九宫了，或者识别漏了，默认红下黑上
            return "(位置：上方为黑方阵地，下方为红方阵地)"
    except:
        return "(位置：无法确定阵营方向)"

# --- 4. 主函数 ---
def ask_deepseek(fen, move_chn, score, pv_list):
    
    # 1. 抓取棋盘图
    text_board = get_board_string_from_tool(fen)

    # 2. 获取文字坐标清单 (双重保险)
    text_locations = get_piece_locations(fen)
    
    # 3. 获取动态方位说明
    orientation_desc = get_orientation_desc(fen)
    
    # 4. 简单的局势文案
    score_val = int(score)
    situation = "均势"
    if score_val > 200: situation = "红方优势"
    elif score_val < -200: situation = "黑方优势"

    print("🎤 正在请求 DeepSeek 全局解读...")

    # 4. Prompt
    prompt = f"""
        这是一盘正在对弈中的中国象棋。
        局势代码(FEN): {fen}
        引擎评分: {score_val} ({situation})
        推荐招法: {move_chn}

        【棋盘图示】
        - 棋子「车马炮相仕帅兵」表示红方
        - 棋子「車馬砲象士将卒」表示黑方
        - {orientation_desc}

        {text_board}

        【全盘棋子坐标精细清单】
        {text_locations}

        【任务】
        请你是中国象棋特级大师，结合上面的【棋盘图示】，
        一定要先在脑海中重建完整的红黑双方兵力分布，搞清楚每一个子在哪！！！千万别出错！！！
        请在反复确认无误后，请以严谨、简练、理性的古典中华文人气质，左右方向以下方视角为准，回答以下三点：

        【敌方局势】：(30 字内。上方为对手，刚下完一步，请点评对手目前的阵型虚实)
        【我方局势】：(30 字内。我是下方的棋手，马上就要应对，点评我方安危与要害)
        【推荐意图】：(30 字内。结合当前盘面，解释为什么要走“{move_chn}”？是攻是守？)

        要求：不要输出多余的客套话，直接输出三段核心分析。
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7, 
            max_tokens=300
        )
        content = response.choices[0].message.content.strip()
        return content.replace("```", "").strip()

    except Exception as e:
        return f"建议行棋：{move_chn}"