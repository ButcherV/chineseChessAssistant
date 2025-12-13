import numpy as np
import cv2
from collections import defaultdict

CLASS_TO_FEN = {
    'r_shuai': 'K', 'r_shi': 'A', 'r_xiang': 'B', 'r_ma': 'N', 'r_ju': 'R', 'r_pao': 'C', 'r_bing': 'P',
    'b_jiang': 'k', 'b_shi': 'a', 'b_xiang': 'b', 'b_ma': 'n', 'b_ju': 'r', 'b_pao': 'c', 'b_zu': 'p'
}

def find_board_corners(board_bbox):
    # ⚡️ 棋盘重新严格标注，无缩放
    xc, yc, w, h = board_bbox 
    x1 = int(xc - w / 2)
    y1 = int(yc - h / 2)
    x2 = int(xc + w / 2)
    y2 = int(yc + h / 2)
    return np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], dtype="float32")

def get_grid_coordinates(corners):
    (tl, tr, br, bl) = corners
    grid = np.zeros((10, 9, 2), dtype=np.float32)
    for col in range(9):
        alpha = col / 8.0
        T = tl + (tr - tl) * alpha
        B = bl + (br - bl) * alpha
        for row in range(10):
            beta = row / 9.0
            P = T + (B - T) * beta
            grid[row, col] = P
    return grid

def pixel_to_grid_index(x, y, grid):
    min_dist = float('inf')
    best_index = (-1, -1)
    for r in range(10):
        for c in range(9):
            grid_x, grid_y = grid[r, c]
            dist = (x - grid_x)**2 + (y - grid_y)**2 
            if dist < min_dist:
                min_dist = dist
                best_index = (r, c)
    return best_index, np.sqrt(min_dist)

def generate_fen(results, image_width, image_height, class_names):
    # --- 1. 识别出多个棋盘时的处理 ---
    best_board_bbox = None
    max_board_conf = -1.0  # 用于记录当前最大的置信度
    
    raw_pieces = [] 
    
    if not results: return None
    r = results[0]
    if r.boxes.xywhn.numel() == 0: return None

    boxes_n = r.boxes.xywhn.cpu().numpy() 
    classes = r.boxes.cls.cpu().numpy().astype(int)
    confs = r.boxes.conf.cpu().numpy() # 获取置信度
    
    # 遍历所有框
    for i, (box_n, cls_id) in enumerate(zip(boxes_n, classes)):
        class_name = class_names[cls_id]
        xc = int(box_n[0] * image_width)
        yc = int(box_n[1] * image_height)
        w = int(box_n[2] * image_width)
        h = int(box_n[3] * image_height)
        
        current_conf = confs[i] # 当前框的置信度

        if class_name == 'board':
            # 如果有多个 board，只保留置信度(conf)最高的那个
            if current_conf > max_board_conf:
                max_board_conf = current_conf
                best_board_bbox = (xc, yc, w, h)
        
        elif class_name in CLASS_TO_FEN:
            # 保存 'conf' 和 'class_name'，为了后面解决冲突用
            raw_pieces.append({
                'center': (xc, yc),
                'symbol': CLASS_TO_FEN[class_name],
                'conf': current_conf,      # 新增：存下分数
                'class_name': class_name   # 新增：存下原名(用于调试打印)
            })
            
    if best_board_bbox is None: 
        print("❌ 未检测到棋盘")
        return None
    
    # --- 2. 生成网格 ---
    board_corners = find_board_corners(best_board_bbox)
    grid_points = get_grid_coordinates(board_corners)

    # --- 3. 映射棋子 + 冲突处理 ---
    final_board = {} 
    
    # candidates[(r,c)] = [piece1, piece2...]
    candidates = defaultdict(list)

    cell_w = best_board_bbox[2] / 9.0
    cell_h = best_board_bbox[3] / 10.0
    max_dist_threshold = min(cell_w, cell_h) * 0.6 

    # 第一步：先把棋子扔进格子里，不急着去重
    for piece in raw_pieces:
        px, py = piece['center']
        (r, c), dist = pixel_to_grid_index(px, py, grid_points)
        
        if dist > max_dist_threshold: continue # 过滤太远的

        # 只要进来了，先存着
        candidates[(r, c)].append(piece)

    # 第二步：解决冲突 (帅/相打架的地方)
    for (r, c), pieces_list in candidates.items():
        if len(pieces_list) == 1:
            # 只有一个候选，直接录用
            final_board[(r, c)] = pieces_list[0]['symbol']
        else:
            # === 🔥 核心补丁：多重识别仲裁 ===
            symbols = [p['symbol'] for p in pieces_list]
            
            # 规则：如果同时出现 'K'(帅) 和 其他棋子，且其他棋子不是帅
            # 逻辑：帅很特殊，如果模型在犹豫它是帅还是相，通常它是相。
            has_red_king = 'K' in symbols
            has_black_king = 'k' in symbols
            
            selected_piece = None
            
            # 情况 1：红帅冲突
            if has_red_king:
                # 看看除了帅还有没有别的
                others = [p for p in pieces_list if p['symbol'] != 'K']
                if others:
                    # 如果有别的，强制选别的里面分最高的（这就把帅剔除了）
                    selected_piece = max(others, key=lambda x: x['conf'])
                    print(f"⚠️ 修正误判 ({r},{c}): 剔除了高分误检 'r_shuai(红帅)'，选择了 '{selected_piece['class_name']}'")

            # 情况 2：黑将冲突
            elif has_black_king:
                others = [p for p in pieces_list if p['symbol'] != 'k']
                if others:
                    selected_piece = max(others, key=lambda x: x['conf'])
                    print(f"⚠️ 修正误判 ({r},{c}): 剔除了高分误检 'b_jiang(黑将)'，选择了 '{selected_piece['class_name']}'")
            
            # 情况 3：普通冲突（比如两个兵重叠），谁分高信谁
            if selected_piece is None:
                selected_piece = max(pieces_list, key=lambda x: x['conf'])
            
            final_board[(r, c)] = selected_piece['symbol']

    # --- 4. 生成 FEN ---
    fen_parts = []
    for r in range(10):
        empty_count = 0
        row_fen = ""
        for c in range(9):
            if (r, c) in final_board:
                if empty_count > 0:
                    row_fen += str(empty_count)
                    empty_count = 0
                row_fen += final_board[(r, c)]
            else:
                empty_count += 1
        if empty_count > 0: row_fen += str(empty_count)
        fen_parts.append(row_fen)

    layout_fen = "/".join(fen_parts)
    
    # --- 5. 视角判断 + 生成完整 FEN ---
    # 逻辑：用户永远在屏幕下方。
    # 如果红帅(K)在棋盘下半截 -> 用户是红方 -> 轮到红走(w)
    # 如果黑将(k)在棋盘下半截 -> 用户是黑方 -> 轮到黑走(b)
    
    # 取出棋盘最下面的 3 行 (第7,8,9行，这是下方的防守区域)
    bottom_area_str = "".join(fen_parts[7:]) 
    
    has_red_king = 'K' in bottom_area_str
    has_black_king = 'k' in bottom_area_str
    
    if has_red_king and not has_black_king:
        # 红帅在下面 -> 肯定是红方视角
        active_color = 'w'
    elif has_black_king and not has_red_king:
        # 黑将在下面 -> 肯定是黑方视角
        active_color = 'b'
    else:
        # ⚠️ 兜底逻辑：如果两个老将都没识别出来，或者都有(极少见)，
        # 还是回退到旧的“数子法”
        print("⚠️ [警告] 无法通过老将位置判断，使用数量兜底...")
        bottom_2_rows = fen_parts[8] + fen_parts[9]
        red_cnt = sum(1 for c in bottom_2_rows if c.isupper())
        blk_cnt = sum(1 for c in bottom_2_rows if c.islower())
        active_color = 'w' if red_cnt >= blk_cnt else 'b'

    full_fen = f"{layout_fen} {active_color} - - 0 1"
    return full_fen