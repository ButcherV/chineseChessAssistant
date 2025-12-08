# logic.py

def parse_fen(fen):
    """
    把 FEN 字符串解析成 10行x9列 的二维数组
    FEN 的第一行是棋盘顶部(黑方大本营)，最后一行是底部(红方大本营)
    """
    board = []
    # 取 FEN 的第一部分（棋盘布局），去掉后面的 w - - 0 1
    position = fen.split(' ')[0]
    rows = position.split('/')

    for row_str in rows:
        current_row = []
        for char in row_str:
            if char.isdigit():
                # 如果是数字 n，说明有 n 个空位
                # 我们用 '.' 代表空位
                for _ in range(int(char)):
                    current_row.append('.')
            else:
                # 如果是字母，直接放入
                current_row.append(char)
        board.append(current_row)
    
    return board

def get_piece_name(piece_char):
    """把 FEN 里的字母翻译成中文棋子名"""
    # 大写是红，小写是黑
    mapping = {
        'R': '车', 'N': '马', 'B': '相', 'A': '仕', 'K': '帅', 'C': '炮', 'P': '兵',
        'r': '车', 'n': '马', 'b': '象', 'a': '士', 'k': '将', 'c': '炮', 'p': '卒'
    }
    return mapping.get(piece_char, '未知')

def uci_to_chinese(move, fen):
    """
    输入招法(b0c2) 和 棋盘(FEN)，自动识别棋子并翻译
    """
    # 1. 解析 FEN 为二维数组
    board = parse_fen(fen)

    # 2. 解析 UCI 坐标
    # 引擎坐标: x(a-i)对应 0-8, y(0-9)对应 底部到顶部
    # 注意：FEN 数组的 row 0 是顶部。
    # 所以：FEN_row = 9 - engine_y
    
    col_map = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4, 'f':5, 'g':6, 'h':7, 'i':8}
    
    start_x = col_map[move[0]]    # b -> 1
    start_y_engine = int(move[1]) # 0
    end_x = col_map[move[2]]      # c -> 2
    end_y_engine = int(move[3])   # 2

    # 换算成 board 数组的行号 (数组第0行是棋盘最上面，即engine_y=9)
    start_row_fen = 9 - start_y_engine
    
    # 3. 去棋盘上查：起点到底是个什么鬼？
    piece_char = board[start_row_fen][start_x]
    
    # 如果查出来是空('.')，说明出错了
    if piece_char == '.':
        return f"错误：起点 {move[:2]} 没有棋子"

    # 翻译棋子名 (例如 'N' -> '马')
    piece_name = get_piece_name(piece_char)
    
    # 判断是谁在走棋 (大写是红方)
    is_red = piece_char.isupper()

    # 4. 开始构造中文术语
    # --- 翻译“路数” ---
    if is_red:
        # 红方路数：x=0(九路) ... x=8(一路)
        chn_nums = ['九', '八', '七', '六', '五', '四', '三', '二', '一']
    else:
        # 黑方路数：x=0(1路) ... x=8(9路)
        chn_nums = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
    
    start_col_name = chn_nums[start_x]
    end_col_name = chn_nums[end_x]

    # --- 翻译“动作” (进/退/平) ---
    action = ""
    # 步数差 (绝对值)
    step_diff = abs(end_y_engine - start_y_engine)
    
    # 映射中文数字 1-9
    step_nums = {1:'一', 2:'二', 3:'三', 4:'四', 5:'五', 6:'六', 7:'七', 8:'八', 9:'九'}
    if not is_red: # 黑方步数也要转成中文数字吗？通常习惯用 123
       step_nums = {1:'1', 2:'2', 3:'3', 4:'4', 5:'5', 6:'6', 7:'7', 8:'8', 9:'9'}

    if start_y_engine == end_y_engine:
        action = "平"
    elif is_red:
        if end_y_engine > start_y_engine: action = "进"
        else: action = "退"
    else: # 黑方
        if end_y_engine < start_y_engine: action = "进" # 黑方往下是进
        else: action = "退"

    # --- 翻译“落点” ---
    # 马、相、仕：只看落在哪一路
    if piece_name in ['马', '相', '仕', '象', '士']:
        result_suffix = end_col_name
    else:
        # 车、炮、兵、将：
        if action == "平":
            result_suffix = end_col_name # 平车看路数
        else:
            # 进退看步数
            result_suffix = step_nums.get(step_diff, str(step_diff))

    return f"{piece_name}{start_col_name}{action}{result_suffix}"

# --- 测试代码 ---
if __name__ == "__main__":
    # 这是一个标准的开局 FEN (红方在下)
    start_fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
    
    print("--- 测试 1: 红马 ---")
    # b0 是红马 (N) 的位置，走到 c2
    print(f"输入: b0c2 -> {uci_to_chinese('b0c2', start_fen)}")
    
    print("\n--- 测试 2: 红炮 ---")
    # h2 是红炮 (C) 的位置，走到 e2 (中路)
    print(f"输入: h2e2 -> {uci_to_chinese('h2e2', start_fen)}")

    print("\n--- 测试 3: 红车 ---")
    # i0 是红车 (R) 的位置，往前走 1 步到 i1
    print(f"输入: i0i1 -> {uci_to_chinese('i0i1', start_fen)}")