# 中国象棋助手 · Chinese Chess Assistant

上传一张中国象棋截图，识别棋盘布局，计算推荐招法，并可通过 DeepSeek 生成中文局势解说。

项目是一个 **Python / Flask HTTP 服务**，适合搭配命令行、手机快捷指令或自行开发的前端使用。当前仓库没有网页界面，也不会自动截屏或操作棋子。

## 功能与处理流程

- **棋盘识别**：使用 Ultralytics YOLO 和仓库中的 `best.pt` 检测棋盘、红黑棋子。
- **局面转换**：将识别结果映射到 9 列、10 行的棋盘网格，生成 FEN；多个棋盘取置信度最高者，同一格的冲突由规则和置信度处理。
- **引擎分析**：通过 UCI 协议调用 Pikafish，获取最佳招法、评分与主要变化。
- **中文记谱**：将 `h2e2` 等 UCI 坐标招法转换为“炮二平五”等中文描述，并处理倒置视角。
- **可选 AI 解说**：通过 DeepSeek 的 `deepseek-chat` 模型生成敌方局势、我方局势和推荐意图；未配置密钥或调用失败时返回引擎招法。
- **调试图片**：保存最近一次上传图和标注结果，便于检查识别是否正确。

```text
截图 → POST /analyze → YOLO 检测 → FEN 局面
     → Pikafish 计算 → 中文招法 → DeepSeek 解说（可选）→ JSON
```

## 环境与准备

建议使用 **Python 3.10 或 3.11** 的独立虚拟环境。依赖包含 PyTorch、OpenCV 和 Ultralytics，安装需要一定时间和磁盘空间。当前依赖固定了较早版本的 PyTorch，不建议直接使用 Python 3.14。

运行前需要：

1. 仓库中的 YOLO 权重 `best.pt`。
2. 与操作系统、CPU 架构匹配的 Pikafish 可执行文件，以及该版本需要的 NNUE 权重。
3. 如需自然语言解说，准备自己的 DeepSeek API Key 和可用的 API 额度；纯引擎分析不需要密钥。

仅 LLM 解说需要访问 DeepSeek。棋盘图像在本地识别；启用解说时，FEN、棋子坐标和引擎分析信息会发送给 DeepSeek，当前代码不直接上传原始图片到 LLM。

## 安装与启动

### 1. 下载并安装依赖

```bash
git clone https://github.com/ButcherV/chineseChessAssistant.git
cd chineseChessAssistant
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows PowerShell 激活环境使用：

```powershell
.venv\Scripts\Activate.ps1
```

若本机只有 Python 3.10，可将创建环境时的 `python3.11` 改为 `python3.10`。后续命令都在项目根目录、已激活虚拟环境的终端执行。

### 2. 准备 Pikafish 引擎

从 [Pikafish 官方项目](https://github.com/official-pikafish/Pikafish) 的 [Releases](https://github.com/official-pikafish/Pikafish/releases) 下载适合本机的发行包。按该版本说明准备可执行文件和 NNUE 权重；不要混用不同版本的网络文件。

当前 `run_engine.py` 查找的路径为 **小写的 `pikafish/engine`**：

```text
chineseChessAssistant/
└── pikafish/
    ├── engine             # 从发行包中取出并重命名的可执行文件
    └── pikafish.nnue      # 具体名称、是否需要外置文件以发行包为准
```

仓库中的大写 `Pikafish` 是一个缺少 `.gitmodules` 配置的 Git 引用，普通克隆后不会提供可用的引擎，不能代替上述安装步骤。在大小写不敏感的文件系统上，它可能与 `pikafish` 指向同一目录；在 Linux 等环境必须确保实际路径与代码一致。

macOS / Linux 需要为下载的引擎增加执行权限：

```bash
chmod +x pikafish/engine
./pikafish/engine
```

进入引擎后输入 `uci`、`isready`，确认出现 `uciok`、`readyok`，再输入 `quit` 退出。检查实际分析时也能找到并加载 NNUE 文件。

Windows 可将 `run_engine.py` 中的 `ENGINE_PATH` 改为实际的 `.exe` 路径。当前仓库未提供自动下载引擎、自动选择 CPU 指令集或 Windows 路径适配。

### 3. 配置可选的 AI 解说

```bash
cp .env.example .env
```

在本地 `.env` 文件中设置 `DEEPSEEK_API_KEY`，值填写自己的密钥。也可以在启动服务前通过系统环境变量设置同名变量。

| 配置项 | 用途 | 默认行为 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | DeepSeek API 身份凭据 | 留空时禁用 AI 解说，保留引擎推荐 |

程序会自动读取项目根目录的 `.env`；已存在的系统环境变量优先。更改配置后需要重启服务。接口地址 `https://api.deepseek.com` 和模型 `deepseek-chat` 目前定义在 `ai_service.py`，不是环境变量配置项。

`.env`、`.env.*` 已被 Git 忽略，仅 `.env.example` 可提交。不要在源码、截图、日志、Issue 或示例配置中写入真实密钥。

**如果密钥曾经提交到公开仓库，应先在服务商控制台撤销并重新生成。删除文件或改写 Git 历史无法让已经泄露的密钥重新安全。**

### 4. 启动服务

```bash
python app.py
```

默认监听 `0.0.0.0:5001`，本机请求地址为 `http://127.0.0.1:5001/analyze`。启动时会加载 YOLO 权重，首次加载可能较慢。

当前使用 Flask 开发服务器，且接口没有身份验证、上传大小限制或并发隔离。请在本机或可信局域网使用；公网部署前需要另行完善访问控制和运行方式。

## 使用接口

### 分析截图

- 路径：`POST /analyze`
- 请求类型：`multipart/form-data`
- 字段：`file`，上传一张能完整看清棋盘和棋子的图片。

```bash
curl -X POST http://127.0.0.1:5001/analyze \
  -F 'file=@uploads/current_board.jpg'
```

也可以将文件路径替换成自己的截图，例如 `-F 'file=@/path/to/board.png'`。仓库已有 `uploads/current_board.jpg` 可用于手工尝试；请求会覆盖最近一次上传文件。

成功响应示意（具体招法、评分、解说随局面变化）：

```json
{
  "error": false,
  "title": "🚀🚀🚀 炮二平五 【 30 】🚀🚀🚀",
  "body": "\n━━━━━━━━━━━━━━\n【 局面评分 】 30\n【 推荐招法 】 炮二平五\n━━━━━━━━━━━━━━\n\n🗣️ 建议行棋：炮二平五"
}
```

| 字段 | 说明 |
| --- | --- |
| `title` | 适合通知或快捷指令标题的文本 |
| `body` | 推荐招法、评分及可选的 AI 解说 |
| `error` | 部分业务响应提供此字段；当前不能仅凭它判断分析是否成功 |

评分原样来自引擎，通常以当前走棋方为视角；它不是胜率百分比。将杀评分在代码中映射为 `9999` 或 `-9999`。当前 LLM 提示词对正负分的红黑解释仍有局限，应以实际局面和引擎招法为准。

### 状态码与错误

| HTTP 状态 | 场景 | 响应内容 |
| --- | --- | --- |
| `200` | 正常分析或业务提示 | `title`、`body`，通常包含 `error: false` |
| `400` | 缺少 `file` 或文件名为空 | `title: 上传失败` 及原因 |
| `500` | 文件保存失败或分析过程抛出异常 | `title: 保存失败` 或 `系统错误` |

根路径 `/` 没有页面，浏览器访问它返回 `404` 属于当前行为。必须向 `/analyze` 发起文件上传请求。

### 手机快捷指令接入思路

1. 获取一张当前棋盘截图。
2. 向 `http://电脑局域网IP:5001/analyze` 发起 POST 请求，在表单字段 `file` 中传入图片。
3. 读取返回 JSON 的 `title` 和 `body`，通过通知或“显示结果”展示。

手机和电脑需要网络互通，电脑防火墙需允许该端口。不要在手机上使用 `127.0.0.1` 指向电脑。仓库目前没有预制的快捷指令安装包。

## 项目结构

```text
chineseChessAssistant/
├── app.py                    # Flask 入口、上传保存与 JSON 响应
├── core_flow.py              # 串联识别、引擎、中文记谱和 LLM
├── yolo_detector.py          # 加载 best.pt，执行检测并保存标注图
├── fen_converter.py          # 棋盘网格映射、冲突处理、FEN 生成
├── run_engine.py             # Pikafish 子进程及 UCI 通信、倒置处理
├── uci_to_chinese.py         # UCI 坐标转中文招法
├── tool_utils.py             # 文本棋盘、FEN 与招法旋转工具
├── ai_service.py             # 本地配置加载、DeepSeek 请求与回退
├── best.pt                   # YOLO 模型权重
├── requirements.txt          # Python 依赖
├── .env.example              # 不含密钥的配置模板
├── .env                      # 自行创建，不提交
├── pikafish/                 # 自行准备的引擎运行目录
├── Pikafish/                 # 历史遗留的 Git 引用，非可用引擎安装包
├── uploads/                  # 最近一次上传图和识别标注图
└── bad_cases/                # 已收集的识别问题样例
```

## 调试与常见问题

### 提示找不到引擎 / 返回“胜负已分”但局面明显未结束

检查 `pikafish/engine` 是否存在、可执行、架构匹配且能加载 NNUE。当前引擎启动失败也可能返回空招法，业务层会把它当作终局，不能仅凭提示认定胜负。先查看终端的引擎错误日志。

### 识别结果与截图不符

查看 `uploads/current_board_result.jpg` 中的检测框和类别，再对照终端打印的 FEN 与字符棋盘。尽量使用正视、完整、无遮挡的棋盘截图，避免透视明显的实拍照片和多个重叠棋盘。

当前模型加载失败、图像读取失败或无法生成 FEN 时，部分路径会回退到**标准开局 FEN**，因此接口返回招法不代表截图识别成功。请先确认启动日志显示模型加载成功，并核对标注结果。

### 没有 AI 解说

确认 `.env` 中设置了 `DEEPSEEK_API_KEY`，重启服务，并检查网络及账号额度。未配置密钥或 API 请求异常时，程序会返回“建议行棋：……”；推荐招法仍由本地引擎提供。

### 依赖安装失败

优先使用 Python 3.10 / 3.11 的全新虚拟环境，避免与其他项目共用依赖。当前依赖表同时固定了 `numpy==1.26.4` 和 `opencv-python==4.12.0.88`；如果解析器提示 NumPy 版本冲突，需要先调整相应版本约束，不能通过忽略依赖强行认定安装成功。PyTorch 安装还需匹配本机系统与架构。

### 同列棋子分析报错

当前 `uci_to_chinese.py` 的重子分支存在 `is_bottom_side` 在赋值前使用的问题，某些“前炮 / 后炮”等局面可能触发异常；这类响应会表现为 `500`。目前不应将重子记谱视为已完整验证的能力。

## 当前限制

- 默认假定用户在画面下方，且轮到下方走棋；单张截图无法可靠还原真实轮次和历史走子。
- 每次请求覆盖 `uploads/current_board.jpg` 和 `uploads/current_board_result.jpg`，暂不适合并发或多用户使用；`.gitignore` 不会自动取消已跟踪样例文件的跟踪状态。
- 检测框到网格的映射基于矩形棋盘，复杂主题、遮挡及斜拍可能降低识别准确率。
- 终局判定、评分解释、重子记谱和错误回退仍有上述边界，不应作为裁判或严格规则验证器。
- 本仓库未附训练流程、数据集、独立前端或自动化端到端测试。贡献识别样例时，请同时提供截图、预期局面及复现方式，并移除个人信息和凭据。
