# Chinese Chess Assistant

[简体中文](README.md) | English

Upload a screenshot of a Chinese chess (Xiangqi) board to recognize the position, calculate a recommended move, and optionally generate commentary in Chinese with DeepSeek.

This project is a **Python / Flask HTTP service** for use with command-line clients, mobile shortcuts, or a frontend you build yourself. The repository currently has no web interface, automatic screen capture, or automated piece movement.

## Features and workflow

- **Board recognition**: Detects the board and red/black pieces using Ultralytics YOLO and the included `best.pt` weights.
- **Position conversion**: Maps detections onto a board with 9 files and 10 ranks and generates FEN. When multiple boards are detected, the one with the highest confidence is selected. Rules and confidence scores resolve conflicting piece detections on the same square.
- **Engine analysis**: Communicates with Pikafish through UCI to obtain the best move, evaluation, and principal variation.
- **Chinese move notation**: Converts UCI coordinates such as `h2e2` into notation such as “炮二平五” and handles inverted board orientation.
- **Optional AI commentary**: Uses DeepSeek's `deepseek-chat` model to describe the opponent's position, the player's position, and the purpose of the recommended move. If no key is configured or the API call fails, the engine's recommendation is still returned.
- **Debug images**: Saves the latest uploaded image and annotated detections for inspection.

```text
Screenshot → POST /analyze → YOLO detection → FEN position
           → Pikafish analysis → Chinese move notation
           → DeepSeek commentary (optional) → JSON
```

## Requirements

Use a dedicated virtual environment with **Python 3.10 or 3.11**. Dependencies include PyTorch, OpenCV, and Ultralytics, so installation requires some time and disk space. The dependency file pins an older PyTorch version; Python 3.14 is not recommended for this setup.

Before running the service, prepare:

1. The `best.pt` YOLO weights included in this repository.
2. A Pikafish executable matching your operating system and CPU architecture, together with any NNUE weights required by that engine version.
3. Your own DeepSeek API key and available API credit if you want natural-language commentary. Engine-only analysis does not require a key.

Only LLM commentary requires access to DeepSeek. Images are processed locally. When commentary is enabled, the service sends FEN, piece coordinates, and engine analysis to DeepSeek; the current implementation does not send the original image directly to the LLM.

## Installation and startup

### 1. Clone the repository and install dependencies

```bash
git clone https://github.com/ButcherV/chineseChessAssistant.git
cd chineseChessAssistant
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

If you have Python 3.10 instead, replace `python3.11` with `python3.10` when creating the environment. Run subsequent commands from the project root with the virtual environment activated.

### 2. Set up Pikafish

Download a suitable release from the [official Pikafish project's](https://github.com/official-pikafish/Pikafish) [Releases page](https://github.com/official-pikafish/Pikafish/releases). Follow that release's instructions for its executable and NNUE weights. Do not mix network files from different engine versions.

The current `run_engine.py` expects the **lowercase path `pikafish/engine`**:

```text
chineseChessAssistant/
└── pikafish/
    ├── engine             # Executable extracted from the release and renamed
    └── pikafish.nnue      # Name and need for an external file depend on the release
```

The uppercase `Pikafish` entry in this repository is a Git submodule reference without a corresponding `.gitmodules` configuration. A normal clone does not populate it with a working engine; you still need to complete the setup above. On a case-insensitive filesystem, `Pikafish` and `pikafish` may refer to the same directory. On Linux and other case-sensitive systems, the actual path must match the code.

On macOS / Linux, make the downloaded executable runnable:

```bash
chmod +x pikafish/engine
./pikafish/engine
```

At the engine prompt, enter `uci` and `isready`, check for `uciok` and `readyok`, then enter `quit`. Also verify that the engine can locate and load its NNUE file during an actual search.

On Windows, change `ENGINE_PATH` in `run_engine.py` to the actual `.exe` path. The repository currently does not automatically download the engine, choose a CPU instruction set, or adapt the executable path for Windows.

### 3. Configure optional AI commentary

```bash
cp .env.example .env
```

Set `DEEPSEEK_API_KEY` in your local `.env` file to your own key. Alternatively, set the same variable in your environment before starting the service.

| Variable | Purpose | Default behavior |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | DeepSeek API credentials | If empty, disables AI commentary and keeps engine recommendations |

The application automatically loads `.env` from the project root. Existing environment variables take precedence. Restart the service after changing configuration. The API base URL `https://api.deepseek.com` and model `deepseek-chat` are currently defined in `ai_service.py`, rather than configured through environment variables.

Git ignores `.env` and `.env.*`, with `.env.example` explicitly allowed. Never put real credentials in source code, screenshots, logs, issues, or example configuration files.

**If a key has ever been committed to a public repository, revoke it and generate a replacement in the provider's console. Deleting files or rewriting Git history cannot make an exposed key safe again.**

### 4. Start the service

```bash
python app.py
```

The default bind address is `0.0.0.0:5001`. For local requests, use `http://127.0.0.1:5001/analyze`. YOLO weights are loaded during startup, which may take some time on the first run.

The application currently uses Flask's development server. The endpoint has no authentication, upload size limit, or request isolation for concurrent users. Use it locally or on a trusted LAN; public deployment requires additional access controls and an appropriate serving setup.

## API usage

### Analyze a screenshot

- Endpoint: `POST /analyze`
- Content type: `multipart/form-data`
- Field: `file`, containing an image that clearly shows the entire board and its pieces.

```bash
curl -X POST http://127.0.0.1:5001/analyze \
  -F 'file=@uploads/current_board.jpg'
```

Replace the file path with your own screenshot if needed, for example `-F 'file=@/path/to/board.png'`. The repository includes `uploads/current_board.jpg` for manual experimentation. Each request overwrites the latest uploaded file.

Example successful response (the move, evaluation, and commentary depend on the position):

```json
{
  "error": false,
  "title": "🚀🚀🚀 炮二平五 【 30 】🚀🚀🚀",
  "body": "\n━━━━━━━━━━━━━━\n【 局面评分 】 30\n【 推荐招法 】 炮二平五\n━━━━━━━━━━━━━━\n\n🗣️ 建议行棋：炮二平五"
}
```

Response text, move notation, and AI commentary are currently in Chinese. The example above shows the engine-only fallback: “建议行棋” means “recommended move.” This English document does not change the application's output language.

| Field | Description |
| --- | --- |
| `title` | Text suitable for a notification or shortcut result title |
| `body` | Recommended move, evaluation, and optional AI commentary |
| `error` | Included in some application responses; it is not sufficient on its own to determine whether analysis succeeded |

The evaluation is returned directly from the engine, generally from the side-to-move perspective; it is not a win probability percentage. Mate scores are mapped to `9999` or `-9999` in the code. The LLM prompt's interpretation of positive and negative scores as red/black advantage still has limitations, so check the actual position and engine move.

### Status codes and errors

| HTTP status | Scenario | Response |
| --- | --- | --- |
| `200` | Normal analysis or an application-level message | `title` and `body`, usually with `error: false` |
| `400` | Missing `file` field or empty filename | `title: 上传失败` (upload failed) and a reason |
| `500` | File save failure or an exception during analysis | `title: 保存失败` (save failed) or `系统错误` (system error) |

There is no page at `/`; a browser request to that path returns `404`. Upload an image to `/analyze` using POST instead.

### Connecting a mobile shortcut

1. Capture a screenshot of the current board.
2. Send a POST request to `http://YOUR_COMPUTER_LAN_IP:5001/analyze`, attaching the image in the `file` form field.
3. Read `title` and `body` from the returned JSON and display them in a notification or result view.

Your phone must be able to reach the computer over the network, and the computer's firewall must allow the port. On the phone, `127.0.0.1` points to the phone itself, not your computer. The repository does not include a ready-to-install shortcut package.

## Project structure

```text
chineseChessAssistant/
├── app.py                    # Flask entry point, upload storage, JSON responses
├── core_flow.py              # Orchestrates recognition, engine, notation, and LLM
├── yolo_detector.py          # Loads best.pt, runs detection, saves annotated images
├── fen_converter.py          # Grid mapping, conflict resolution, FEN generation
├── run_engine.py             # Pikafish process, UCI communication, orientation handling
├── uci_to_chinese.py         # Converts UCI coordinates to Chinese move notation
├── tool_utils.py             # Text board display, FEN and move rotation helpers
├── ai_service.py             # Local configuration, DeepSeek requests, fallback
├── best.pt                   # YOLO model weights
├── requirements.txt          # Python dependencies
├── .env.example              # Configuration template without credentials
├── .env                      # Create locally; do not commit
├── pikafish/                 # Engine runtime directory you prepare yourself
├── Pikafish/                 # Legacy Git reference, not a working engine installation
├── uploads/                  # Latest uploaded image and annotated detections
└── bad_cases/                # Collected recognition failure examples
```

## Troubleshooting

### Engine not found, or “game over” returned for an unfinished position

Check that `pikafish/engine` exists, is executable, matches your CPU architecture, and can load its NNUE weights. An engine startup failure can also produce an empty move, which the application currently treats as a terminal position. Do not infer the game's outcome from that message alone; inspect the engine errors in the terminal first.

### Recognized position does not match the screenshot

Inspect the bounding boxes and class labels in `uploads/current_board_result.jpg`, then compare them with the FEN and text board printed in the terminal. Use a complete, unobstructed screenshot viewed straight on. Avoid photographs with strong perspective distortion or overlapping boards.

Some failure paths, including model loading failure, image reading failure, or failure to generate FEN, fall back to the **standard starting-position FEN**. Receiving a recommended move therefore does not prove the screenshot was recognized successfully. Confirm successful model loading in the startup logs and inspect the annotated detections.

### AI commentary is missing

Check that `DEEPSEEK_API_KEY` is set in `.env`, restart the service, and verify network connectivity and account credit. With no key or after an API error, the response falls back to “建议行棋：…” (recommended move); the local engine still provides the move.

### Dependency installation fails

Start with a fresh Python 3.10 / 3.11 virtual environment rather than sharing dependencies with another project. The dependency file currently pins both `numpy==1.26.4` and `opencv-python==4.12.0.88`. If the resolver reports a NumPy version conflict, adjust the relevant constraints before installing; bypassing dependency checks does not establish that the environment works. PyTorch must also match your operating system and architecture.

### Analysis fails when identical pieces share a file

The duplicate-piece branch in `uci_to_chinese.py` currently uses `is_bottom_side` before assigning it. Some positions requiring “front cannon / rear cannon” notation can trigger an exception and produce a `500` response. Duplicate-piece notation should not yet be considered fully validated.

## Current limitations

- The player is assumed to be at the bottom of the image, with that side to move. A single screenshot cannot reliably establish the actual turn or move history.
- Each request overwrites `uploads/current_board.jpg` and `uploads/current_board_result.jpg`. The service is not yet suitable for concurrent requests or multiple users. Adding `.gitignore` rules does not untrack sample files already in Git.
- Detection-to-grid mapping assumes a rectangular board. Unfamiliar visual themes, occlusion, and angled photographs can reduce recognition accuracy.
- Terminal-position detection, evaluation interpretation, duplicate-piece notation, and failure fallbacks have the limitations described above. The service is not intended as an arbiter or a strict rules validator.
- This repository does not include a training pipeline, dataset, standalone frontend, or automated end-to-end tests. When contributing recognition examples, include the screenshot, expected position, and reproduction steps, and remove personal information and credentials.
