# core_flow.py
# YOLO -> 逻辑 -> 引擎 -> AI

from yolo_detector import detect_and_generate_fen
from run_engine import get_best_move
from uci_to_chinese import uci_to_chinese
from ai_service import ask_deepseek

def process_chess_image(image_path):
    """
    输入图片路径，输出最终给前端的字典数据
    """
    # 1. 眼睛：识别 FEN
    print(f"👁️ [流程] 开始识别: {image_path}")
    current_fen = detect_and_generate_fen(image_path)

    if current_fen is None:
        return {
            "error": False, 
            "title": "未发现棋局",
            "body": "🤔 画面中似乎没有检测到中国象棋棋盘。"
        }
    
    # 2. 大脑：引擎计算
    print(f"🧠 [流程] 引擎计算中 (FEN: {current_fen})...")
    best_move_uci, score, pv_list = get_best_move(current_fen)

    # ================= 🔴 处理将死/困毙 =================
    if not best_move_uci:
        print("🛑 [流程] 引擎未返回招法 -> 判定为绝杀/困毙")
        
        # 1. 看 FEN，到底是谁的回合？
        # FEN 格式: "..... w - - 0 1"
        turn = current_fen.split(' ')[1] 
        is_red_turn = (turn == 'w')
        
        current_side = "红方" if is_red_turn else "黑方"
        enemy_side = "黑方" if is_red_turn else "红方"
        
        # 2. 结合引擎分数判断
        # score > 0 (9999) 代表“当前走棋方”赢了
        # score < 0 (-9999) 代表“当前走棋方”输了
        
        result_text = ""

        if score > 8000:
            # 当前方绝杀对方
            result_text = f"{enemy_side}已被将死。{current_side}胜！"
        elif score < -8000:
            # 当前方被对方绝杀
            result_text = f"{current_side}已被将死。{enemy_side}胜！"
        else:
            # 分数接近0，通常是困毙（无子可动但没被将军）或长将作和
            result_text = "和棋 (困毙或循环局面)"

        return {
            "error": False,  # 这不是系统错误，是游戏结束
            "title": "🏁 胜负已分",
            "body": f"\n{result_text}"
        }
    # ==========================================================
    
    # 3. 翻译：生成结果
    chinese_move = uci_to_chinese(best_move_uci, current_fen)
    
    # 4. LLM 辅助
    advice = ask_deepseek(current_fen, chinese_move, score, pv_list)

    # ================= 🟢 IOS「显示结果」的局限 - 纯文本视觉增强 =================
    ui_title = f"🚀🚀🚀 {chinese_move} 【 {score} 】🚀🚀🚀"

    formatted_body = (
        f"\n"
        f"━━━━━━━━━━━━━━\n"
        f"【 局面评分 】 {score}\n"
        f"【 推荐招法 】 {chinese_move}\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"🗣️ {advice}"
    )

    return {
        "error": False,
        "title": ui_title, 
        "body": formatted_body 
    }