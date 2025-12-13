# 象棋助手 (Chinese Chess Assistant) ♟️

这是一个基于 Python 的中国象棋辅助工具。它结合了 YOLO 视觉识别、Pikafish 强力引擎计算以及 LLM 的自然语言解说，通过截图快速分析当前局势并给出建议。

## ✨ 功能特点

* **👁️ 视觉识别**: 自动识别屏幕上的象棋棋盘和棋子布局 (基于 YOLOv8)。
* **🧠 引擎计算**: 集成 Pikafish (皮卡鱼) 引擎，提供特级大师水准的招法分析。
* **🗣️ AI 解说**: 使用 LLM，生成局势解读与战术建议。
* **🔄 智能纠错**: 自动处理倒置棋盘、红黑方判断及多子同列（前炮/后炮）的记谱问题。

## 📂 项目结构

```text
chineseChessAssistant/
├── ai_service.py        # LLM 接口调用与文案生成
├── app.py               # Flask 主程序入口
├── core_flow.py         # 核心业务流程控制
├── fen_converter.py     # 视觉识别结果转 FEN 串
├── logic.py             # 招法翻译与规则逻辑 (uci_to_chinese)
├── run_engine.py        # Pikafish 引擎调用封装
├── tool_utils.py        # 工具函数
├── yolo_detector.py     # YOLO 图像识别模块
├── requirements.txt     # Python 依赖列表
├── best.pt              # YOLO 识别模型权重
├── .env                 # (需自行创建) API Key 配置文件
└── pikafish/            # 象棋引擎文件夹
    ├── engine           # 引擎执行文件
    └── pikafish.nnue    # 引擎神经网络权重