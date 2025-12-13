
def uci_to_chinese(move, fen):
    """
    将 UCI 招法 (如 h2e2) 转换为中文招法 (如 炮二平五)。
    兼容倒置棋盘（红在上）。
    """
    if not move: return "无招法"
    
    # 1. 解析 FEN，获取棋盘矩阵 (10行9列)
    #    注意：这里必须把 FEN 展开成二维数组 board[y][x]
    board = []
    rows = fen.split(' ')[0].split('/')
    for row in rows:
        row_line = []
        for char in row:
            if char.isdigit():
                row_line.extend([None] * int(char))
            else:
                row_line.append(char)
        board.append(row_line)

    # 2. 解析 UCI 坐标
    #    UCI 坐标系：左下角是 a0，右上角是 i9
    #    board 数组：board[0][0] 是左上角
    
    # 将 UCI 字母坐标 (a-i) 转为 x (0-8)
    # 将 UCI 数字坐标 (0-9) 转为 y (9-0) -> 注意：UCI的0是数组的9
    col_map = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4, 'f':5, 'g':6, 'h':7, 'i':8}
    
    src_x = col_map[move[0]]
    src_y = 9 - int(move[1])  # UCI的 row 9 是 数组的 index 0
    dst_x = col_map[move[2]]
    dst_y = 9 - int(move[3])
    
    # 3. 获取棋子
    piece = board[src_y][src_x]
    
    # 🚨🚨🚨 核心修正点：找不到棋子时的处理 🚨🚨🚨
    if piece is None:
        print(f"❌ [严重错误] 在坐标 {move[0]}{move[1]} (数组[{src_y}][{src_x}]) 没找到棋子！")
        print(f"    当前 FEN: {fen}")
        return move # 找不到就直接返回英文，别崩
        
    # 4. 判断红黑
    is_red = piece.isupper() # 大写是红棋
    
    # 5. 再次检测是否倒置 (修正版)
    #    逻辑：寻找红帅 'K' 的位置
    #    如果 'K' 在 0-4 行 -> 红在上 (倒置)
    #    如果 'K' 在 5-9 行 -> 红在下 (正常)
    
    red_k_row = -1
    for i, r in enumerate(rows):
        if 'K' in r:
            red_k_row = i
            break
            
    if red_k_row != -1:
        is_red_on_top = (red_k_row <= 4)
    else:
        # 兜底：如果没帅，才看第一行杂兵
        is_red_on_top = any(c.isupper() for c in rows[0])

    print(f"🕵️ [调试] 棋子:{piece} | 红棋:{is_red} | 红在上:{is_red_on_top} | 招法:{move}")

    # ==========================================
    # 6. 多子同列检测 (前后区分)
    # ==========================================
    
    # 扫描当前列 (src_x)，找出所有同类棋子
    same_pieces_y = []
    for y in range(10):
        if board[y][src_x] == piece:
            same_pieces_y.append(y)
    
    is_duplicate = len(same_pieces_y) > 1
    prefix_char = "" 
    
    if is_duplicate:
        # 排序逻辑：
        # 在下方(Bottom)的人：Y越小离对手越近，是"前" -> 升序
        # 在上方(Top)的人：   Y越大离对手越近，是"前" -> 降序
        if is_bottom_side:
            same_pieces_y.sort() 
        else:
            same_pieces_y.sort(reverse=True)
            
        # 找到自己排第几
        idx = same_pieces_y.index(src_y)
        count = len(same_pieces_y)
        
        # 映射文字
        if count == 2:
            prefix_char = "前" if idx == 0 else "后"
        elif count >= 3:
            if idx == 0: prefix_char = "前"
            elif idx == 1: prefix_char = "中"
            else: prefix_char = "后"
    
    # ==========================================
    # 7. 生成中文招法
    # ==========================================
    
    # 映射表
    piece_map = {
        'R': '车', 'H': '马', 'N': '马', 'C': '炮', 'A': '仕', 'E': '相', 'B': '相', 'K': '帅', 'P': '兵',
        'r': '车', 'h': '马', 'n': '马', 'c': '炮', 'a': '士', 'e': '象', 'b': '象', 'k': '将', 'p': '卒'
    }
    
    chn_nums = ['一', '二', '三', '四', '五', '六', '七', '八', '九']
    arab_nums = ['1', '2', '3', '4', '5', '6', '7', '8', '9']

    # --- 坐标标准化 (保留你原本正确的逻辑) ---
    real_src_col = src_x
    real_dst_col = dst_x
    
    # 逻辑列号计算
    if (is_red and not is_red_on_top) or (not is_red and is_red_on_top):
        # 阵地在下方：x=8是第一列
        src_col_idx = 8 - real_src_col
        dst_col_idx = 8 - real_dst_col
    else:
        # 阵地在上方：x=0是第一列
        src_col_idx = real_src_col
        dst_col_idx = real_dst_col

    # 动作判断 (进/退/平)
    # 同样取决于阵地在上下方
    is_bottom_side = (is_red and not is_red_on_top) or (not is_red and is_red_on_top)
    
    if src_y == dst_y:
        action = '平'
    else:
        # 如果在本方在下方，y 减小(往上走)是进
        if is_bottom_side:
            action = '进' if dst_y < src_y else '退'
        else:
            action = '进' if dst_y > src_y else '退'

    # 获取棋子名称
    name = piece_map.get(piece, piece)

    # --- 计算“第四个字”（落点/步数） ---
    # 这部分逻辑对“普通情况”和“重子情况”是通用的，所以提取出来
    
    dst_char = ""
    # 判断是否是斜行棋子 (马相仕士象) -> 显示落点列号
    is_slant_piece = name in ['马', '相', '仕', '士', '象']
    
    if is_red:
        # 红方：全汉字
        if action == '平' or is_slant_piece:
            dst_char = chn_nums[dst_col_idx] # 用列号
        else:
            # 直行棋子(车炮兵)进退 -> 用步数
            steps = abs(src_y - dst_y)
            dst_char = chn_nums[steps - 1]
    else:
        # 黑方：全数字
        if action == '平' or is_slant_piece:
            dst_char = arab_nums[dst_col_idx] # 用列号
        else:
            # 直行棋子进退 -> 用步数
            steps = abs(src_y - dst_y)
            dst_char = arab_nums[steps - 1]

    # ==========================================
    # 8. 最终拼装 (区分有无重子)
    # ==========================================
    
    if is_duplicate:
        # 🟢 情况 A: 有重子 (例如：前炮平五)
        # prefix_char 在 Step 6 里算出来了 (前/后/中)
        # 格式：[前][炮][平][五]
        print(f"{prefix_char}{name}{action}{dst_char}")
        return f"{prefix_char}{name}{action}{dst_char}"
    else:
        # 🔵 情况 B: 普通 (例如：炮二平五)
        # 需要计算第二个字：[源列号]
        if is_red:
            src_col_char = chn_nums[src_col_idx]
        else:
            src_col_char = arab_nums[src_col_idx]
            
        # 格式：[炮][二][平][五]
        print(f"中文招法：{name}{src_col_char}{action}{dst_char}")
        return f"{name}{src_col_char}{action}{dst_char}"