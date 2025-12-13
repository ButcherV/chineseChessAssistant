
def print_fen_board(fen):
    """
    在控制台打印中国象棋棋盘，方便验证
    改进点：
    1. 增加楚河汉界分割线。
    2. 黑棋使用繁体字(車/馬/砲)，复制纯文本也能区分红黑。
    """
    board_str = fen.split(" ")[0]
    rows = board_str.split("/")
    
    # --- 颜色配置 (保留颜色，为了在终端看更爽) ---
    RED = '\033[91m'     # 红字
    BLACK = '\033[32m'   # 绿字 (黑色背景下绿色比黑色更显眼，也可改 \033[30m)
    RESET = '\033[0m'
    
    # --- 棋子映射 (关键修改) ---
    # 为了防止复制粘贴丢失颜色，我们在【字形】上也做了区分：
    # 红方：车、马、炮 (简体)
    # 黑方：車、馬、砲 (繁体/异体)
    piece_map = {
        # 红方 (大写)
        'R': f"{RED}车{RESET}", 
        'N': f"{RED}马{RESET}", 
        'B': f"{RED}相{RESET}", 
        'A': f"{RED}仕{RESET}", 
        'K': f"{RED}帅{RESET}", 
        'C': f"{RED}炮{RESET}", 
        'P': f"{RED}兵{RESET}",
        
        # 黑方 (小写) - 使用不同字形，不仅靠颜色
        'r': f"{BLACK}車{RESET}", 
        'n': f"{BLACK}馬{RESET}", 
        'b': f"{BLACK}象{RESET}", 
        'a': f"{BLACK}士{RESET}", 
        'k': f"{BLACK}将{RESET}", 
        'c': f"{BLACK}砲{RESET}", 
        'p': f"{BLACK}卒{RESET}",
    }

    # 空位符号
    EMPTY_SYMBOL = f"\033[90m十{RESET}" 

    print("\n" + "═"*36) 
    print("      👀 FEN 布局可视化确认")
    print("═"*36)
    
    # 打印顶部坐标
    print("     Ａ Ｂ Ｃ Ｄ Ｅ Ｆ Ｇ Ｈ Ｉ") 
    print("   " + "┌" + "─"*28 + "┐") 

    for r_idx, row_str in enumerate(rows):
        
        # ================= 🟢 新增：楚河汉界 =================
        # 象棋的河界在第 4 行和第 5 行之间 (数组索引 4 和 5)
        # FEN 是从第 0 行(物理9)开始画的，所以是画完第 4 行准备画第 5 行时插入
        if r_idx == 5:
            # 打印一条特殊的分割线
            print("   │" + "─"*8 + " 楚河  汉界 " + "─"*8 + "│")
        # ====================================================

        line_visual = []
        for char in row_str:
            if char.isdigit():
                count = int(char)
                for _ in range(count):
                    line_visual.append(EMPTY_SYMBOL)
            else:
                line_visual.append(piece_map.get(char, char))
        
        row_content = " ".join(line_visual)
        
        # 打印行
        print(f" {r_idx} │ {row_content} │ {r_idx}")

    print("   " + "└" + "─"*28 + "┘") 
    print("     Ａ Ｂ Ｃ Ｄ Ｅ Ｆ Ｇ Ｈ Ｉ")
    print("═"*36 + "\n")


def flip_fen(fen):
    """
    将 FEN 字符串旋转 180 度。
    用于把“红上黑下”的倒置局面，转成引擎能理解的“红下黑上”标准局面。
    """
    board_part, turn, castling, en_passant, half, full = fen.split(' ')
    
    # 1. 翻转棋盘布局
    rows = board_part.split('/')
    # 倒序排列行，并且每一行内部的字符串也要反转
    # 例如: "1NBAK" -> "KABN1" (这一步不需要，因为左右翻转是行内的逻辑？)
    # 不，旋转180度 = 上下颠倒 + 左右颠倒
    reversed_rows = [row[::-1] for row in rows[::-1]]
    new_board_part = "/".join(reversed_rows)
    
    return f"{new_board_part} {turn} {castling} {en_passant} {half} {full}"


def flip_move(move_uci):
    """
    将 UCI 招法旋转 180 度 (用于倒置局面的还原)。
    必须同时翻转列 (a-i) 和 行 (0-9)。
    例如: h2e2 -> b7e7
    """
    if not move_uci: return move_uci
    
    # 制作映射表：
    # 列: a<->i, b<->h ...
    # 行: 0<->9, 1<->8 ...
    trans_table = str.maketrans(
        "abcdefghi0123456789", 
        "ihgfedcba9876543210"
    )
    
    return move_uci.translate(trans_table)