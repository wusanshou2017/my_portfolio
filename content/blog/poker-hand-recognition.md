---
title: 德州扑克手牌识别 — 基于 YOLOv8 的实时目标检测
date: 2026-05-14
tags: [YOLOv8, 目标检测, Python, OpenCV, 深度学习]
description: 使用 YOLOv8 训练自定义模型，实现德州扑克手牌与公共牌的自动识别与分类，支持多窗口场景。
---

## 项目背景

德州扑克是一种信息不完整的博弈游戏，牌面信息的快速识别是构建辅助工具的第一步。这个项目用 **YOLOv8** 训练了一个扑克牌检测模型，能够从截图或视频流中自动识别每张牌的花色和点数，并将识别结果区分为**手牌**和**公共牌**。

## 技术栈

| 技术 | 用途 |
|---|---|
| YOLOv8 (Ultralytics) | 目标检测模型训练与推理 |
| OpenCV | 图像处理、绘制检测框 |
| NumPy | 聚类算法实现 |
| Python | 整体开发语言 |

## 识别效果展示

### 单窗口场景

输入原始扑克牌面截图：

![单窗口原始输入](/images/poker/1.png)

模型推理后的检测结果：

![单窗口检测结果](/images/poker/1_result.jpg)

绿色框标记**手牌**，黄色框标记**公共牌**。每张牌旁边标注了类别名称，方便直观验证。

### 多窗口场景

当截图中包含多个游戏窗口时，模型同样能逐窗口识别并分组：

![多窗口原始输入](/images/poker/7.png)

![多窗口检测结果](/images/poker/7_result.jpg)

不同窗口用不同颜色的外框区分（蓝、绿、红等），每个窗口内部的手牌和公共牌分别用绿色和黄色标注。

### 复杂牌面

![复杂牌面输入](/images/poker/10.png)

![复杂牌面检测结果](/images/poker/10_result.jpg)

即使牌面密集、角度多样，模型仍能准确定位每张牌的位置和类别。

## 核心算法

项目的核心不只是目标检测，还包括检测后的**智能分组**逻辑。整个推理流程如下：

```
输入图片
    │
    ▼
┌──────────────────────────┐
│  YOLOv8 模型推理          │
│  → 检测所有扑克牌的位置    │
│    和类别（52种牌）        │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│  cluster_cards() 聚类     │
│  → 将空间上相近的牌       │
│    分到同一个游戏窗口      │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│  split_hand_community()  │
│  → 每个窗口内区分         │
│    手牌 vs 公共牌          │
│  (按 Y 坐标分行)          │
└────────────┬─────────────┘
             │
             ▼
  输出: 每个窗口的手牌和公共牌列表
```

### 1. YOLOv8 目标检测

使用 Ultralytics 的 YOLOv8 框架加载训练好的模型权重 `best.pt`：

```python
from ultralytics import YOLO

model = YOLO("best.pt")
results = model(image_path, conf=0.25)
```

模型输出每张牌的：
- **边界框** (bounding box)：`(x1, y1, x2, y2)`
- **类别** (class)：52 种牌中的哪一张
- **置信度** (confidence)：检测的可靠程度

### 2. 多窗口聚类 — cluster_cards()

当截图中存在多个游戏窗口时，需要将属于同一窗口的牌归为一组。这里实现了一个基于距离的连通域聚类算法：

```python
def cluster_cards(card_infos, img_w, img_h):
    positions = np.array([[c["cx"], c["cy"]] for c in card_infos])

    card_h = np.median([c["bbox"][3] - c["bbox"][1] for c in card_infos])
    eps = card_h * 4

    labels = [-1] * len(positions)
    current_label = 0

    for i in range(len(positions)):
        if labels[i] != -1:
            continue
        labels[i] = current_label
        stack = [i]
        while stack:
            idx = stack.pop()
            for j in range(len(positions)):
                if labels[j] != -1:
                    continue
                dist = np.sqrt((positions[idx][0] - positions[j][0]) ** 2 +
                               (positions[idx][1] - positions[j][1]) ** 2)
                if dist < eps:
                    labels[j] = current_label
                    stack.append(j)
        current_label += 1
```

核心思路：

| 概念 | 实现 |
|---|---|
| 距离阈值 | `eps = card_h * 4`，以牌高度的中位数为基准，两张牌中心距离小于 4 倍牌高则视为同一窗口 |
| 聚类方式 | 连通域标记算法（类似 DBSCAN 的简化版），从一张牌出发，把所有距离在阈值内的牌标记为同一组 |
| 排序 | 聚类后按 Y 坐标优先、X 坐标次之排序，保证窗口顺序从上到下、从左到右 |

### 3. 手牌与公共牌分离 — split_hand_community()

在同一个窗口内，需要区分哪些是手牌、哪些是公共牌。德州扑克的牌面布局有一个视觉特征：**手牌在上方，公共牌在下方**。

```python
def split_hand_community(cards_in_window):
    sorted_cards = sorted(cards_in_window, key=lambda c: c["cy"])

    card_h = np.median([c["bbox"][3] - c["bbox"][1] for c in sorted_cards])
    gap_threshold = card_h * 1.5

    groups = []
    current_group = [sorted_cards[0]]
    for i in range(1, len(sorted_cards)):
        if sorted_cards[i]["cy"] - current_group[-1]["cy"] < gap_threshold:
            current_group.append(sorted_cards[i])
        else:
            groups.append(current_group)
            current_group = [sorted_cards[i]]
    groups.append(current_group)
```

算法步骤：

1. 按 Y 坐标排序所有牌
2. 以 `card_h * 1.5` 为阈值，Y 坐标差距超过阈值的牌视为不同行
3. Y 坐标较大（位置更低）的一行是**手牌**，其余是**公共牌**
4. 每组内按 X 坐标排序，保证牌的顺序从左到右

## 位置识别（Position Detection）

在德州扑克中，**位置**是决策的核心因素之一。同一个手牌在不同位置的策略截然不同。为了实现完整的辅助决策，我们需要知道玩家当前处于哪个位置（UTG、MP、CO、BTN、SB、BB）。

### 如何判断位置？

德州扑克的牌桌上有一个**庄家按钮（D按钮）**，它是确定所有位置编号的锚点。D按钮在每一手牌后顺时针移动一位。

我们训练了一个独立的 YOLOv8 模型 `dealer.pt` 来检测 D 按钮的位置，然后根据 D 按钮相对于牌桌中心的角度推算出当前座位的位置。

![位置检测结果](/images/poker/1_pos.jpg)

黄色圆圈标记检测到的 D 按钮，旁边标注推断出的位置名称。

### 位置识别算法

```python
SEAT_ANGLES_6MAX = [90, 30, 330, 270, 210, 150]
POSITION_MAP = {0: "BTN", 1: "SB", 2: "BB", 3: "UTG", 4: "MP", 5: "CO"}

def detect_position(dealer_model, img, conf=0.5):
    h, w = img.shape[:2]
    center_x = w // 2
    center_y = int(h * 0.45)

    dealer = detect_dealer_button(dealer_model, img, conf)
    if dealer is None:
        return "BTN", None, 0.0

    dx = dealer["cx"] - center_x
    dy = dealer["cy"] - center_y

    angle = np.degrees(np.arctan2(dy, dx))
    if angle < 0:
        angle += 360

    seat = angle_to_seat(angle)
    position = POSITION_MAP.get(seat, "BTN")
    return position, dealer_pos, dealer["confidence"]
```

算法步骤：

1. 用 `dealer.pt` 模型检测 D 按钮的位置（中心点坐标）
2. 计算 D 按钮相对于牌桌中心的偏移 `(dx, dy)`
3. 用 `arctan2` 将偏移转换为角度（0°~360°）
4. 将角度匹配到最近的座位角度（6 人桌有 6 个预定义角度）
5. 通过座位编号映射到位置名称

```
6人桌座位角度分布（俯视图）:

         BTN(90°)
          ↑
   CO(150°) ←  → SB(30°)
   MP(210°) ←  → BB(330°)
          ↓
        UTG(270°)

   当 D 按钮检测角度 ≈ 90° → 座位0 → BTN
   当 D 按钮检测角度 ≈ 30° → 座位1 → SB
   ...
```

## GTO 策略匹配

识别出手牌和位置后，下一步就是**根据 GTO（Game Theory Optimal）策略给出行动建议**。

### 什么是 GTO 策略？

GTO 策略是基于博弈论纳什均衡的最优策略。它不是"赢最多"的策略，而是"不可被剥削"的策略。在翻前（Preflop）阶段，GTO 策略为每种手牌 × 每个位置组合都分配了一组概率：

```
手牌: AKs  位置: BTN
→ RAISE: 85%  CALL: 10%  FOLD: 5%  ALLIN: 0%

手牌: 72o  位置: UTG
→ RAISE: 0%  CALL: 0%  FOLD: 100%  ALLIN: 0%
```

系统根据这些概率随机选择一个行动，从而实现不可预测的混合策略。

### 手牌标准化

52 张牌可以组成 1326 种两手牌组合，但 GTO 策略将它们归类为 **169 种标准化手牌**：

```python
def normalize_hand(card1, card2):
    r1, s1 = parse_card(card1)  # 如 "A", "s"
    r2, s2 = parse_card(card2)  # 如 "K", "s"

    if RANK_VALUE[r1] < RANK_VALUE[r2]:
        r1, r2 = r2, r1
        s1, s2 = s2, s1

    if r1 == r2:
        return r1 + r2           # 对子: "AA", "KK", "77"
    elif s1 == s2:
        return r1 + r2 + "s"     # 同花: "AKs", "QJs"
    else:
        return r1 + r2 + "o"     # 杂色: "AKo", "QJo"
```

### 策略查询与决策

策略数据存储在 PostgreSQL 数据库中（845 条 RFI 数据），查询流程如下：

```
识别结果: 手牌 = [As, Kh]  位置 = CO
          │
          ▼
    normalize_hand("As", "Kh")
          │
          ▼
    hand_key = "AKs"
          │
          ▼
    查询数据库: SELECT * FROM gto_strategy
                WHERE hand='AKs' AND position='CO'
          │
          ▼
    概率分布: RAISE=0.85, CALL=0.10, FOLD=0.05, ALLIN=0
          │
          ▼
    随机采样 → 输出: RAISE
```

### 完整推理管线效果

以下是牌面识别 + 位置检测 + GTO 策略匹配的完整管线输出：

![完整管线检测结果](/images/poker/1_result_result.jpg)

画面中同时展示了：手牌/公共牌的检测框、D 按钮位置标记、推断的座位位置，以及基于 GTO 策略的行动建议。

### 翻前范围可视化

项目还内置了一个 **13×13 扑克矩阵范围查看器**（Vue 3 + Vite + FastAPI），支持按场景（RFI / 3-Bet / BB Defense）和位置切换，悬停可查看每手牌的动作频率和置信度。

范围查看器的核心数据来自 GTO 求解器（PioSOLVER / GTO Wizard），涵盖 6 人桌 100BB 深度下所有位置的翻前范围：

| 位置 | RFI 范围 | 位置 EV (bb/100) | 策略特征 |
|---|---|---|---|
| LJ (UTG) | ~17.6% | -4.8 | 最紧范围，强牌+优质同花连张 |
| HJ | ~21.4% | +2.1 | 加入中小对子，扩展同花连张 |
| CO | ~27.8% | +11.2 | 加入更多投机手牌，不同花高张 |
| BTN | ~43.5% | +30.5 | 最宽范围，大量杂色+连张，位置主导 |
| SB | ~62.3% | -14.7 | Raise/Call混合，对BB极宽，翻后OOP |

## 多桌同时处理

实际使用中，玩家通常会同时开多个桌（6 桌），需要从一张截图中同时处理所有牌桌。

### 多桌分割

系统通过分析图像的灰度均值，自动检测桌与桌之间的间隙，将截图均匀分割为网格：

```python
def find_gaps(img, rows, cols):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    col_mean = np.mean(gray, axis=0)
    row_mean = np.mean(gray, axis=1)

    for i in range(1, cols):
        center = w * i // cols
        lo = max(0, center - 200)
        hi = min(w, center + 200)
        best = lo
        best_val = float('inf')
        for x in range(lo, hi):
            if col_mean[x] < best_val:
                best_val = col_mean[x]
                best = x
        splits.append(best)
```

### 6 桌同时推理

![6桌原始输入](/images/poker/6tables.png)

![6桌推理结果](/images/poker/6tables_result.jpg)

每个窗口独立完成：牌面识别 → 位置检测 → GTO 策略匹配 → 行动建议，互不干扰。

## 完整系统架构

整个系统从单张图片的手牌识别，演进为一个完整的辅助决策平台：

```
┌─────────────────────────────────────────────────────────────┐
│                     完整系统架构                              │
│                                                             │
│  输入层                                                      │
│  ├── 图片文件推理 (main.py)                                  │
│  ├── HDMI 采集实时推理 (server.py)                           │
│  └── 屏幕截图推理                                            │
│                                                             │
│  感知层                                                      │
│  ├── hands_detect.pt → 52 类扑克牌检测（YOLOv8 / RKNN）     │
│  ├── dealer.pt → D 按钮检测                                 │
│  └── 多桌分割 → 网格裁剪 + 间隙检测                          │
│                                                             │
│  决策层                                                      │
│  ├── position.py → 角度映射 → 6 人桌位置                     │
│  ├── strategy.py → normalize_hand → GTO 策略查询            │
│  └── PostgreSQL → 845 条翻前 RFI 数据                       │
│                                                             │
│  展示层                                                      │
│  ├── OpenCV 绘制检测框 + 行动建议                            │
│  ├── FastAPI + Vue LiveDashboard → 浏览器实时查看            │
│  └── RangeMatrix 13×13 范围查看器                            │
│                                                             │
│  部署                                                        │
│  ├── PC 端: PyTorch YOLO 推理                                │
│  └── 香橙派 RK3588: RKNN NPU 加速（INT8 量化）              │
└─────────────────────────────────────────────────────────────┘
```

### 香橙派 RK3588 部署

系统支持部署在香橙派 5 Plus 开发板上，通过 HDMI IN 采集 PC 显卡输出的多桌画面，使用 RKNN NPU 进行 INT8 量化推理，实现低延迟实时处理：

```
PC 显卡 HDMI OUT ──HDMI线──> 香橙派 HDMI IN
                                      │
                                      ▼
                              FastAPI 服务
                              (采集 + RKNN 推理)
                                      │
                                      ▼
                              浏览器访问 http://板子IP:8000
```

RKNN 推理通过 `rknn_model.py` 封装，与 PyTorch YOLO 推理共享相同接口，`server.py` 启动时自动检测硬件环境选择推理后端。

### 完整项目结构

```
poker_detect/
├── server.py              # FastAPI 主服务（HDMI 采集 + 推理 + 前端）
├── main.py                # 命令行推理入口
├── position.py            # D 按钮 → 位置识别
├── strategy.py            # GTO 策略查询（PostgreSQL）
├── config.py              # 全局配置
├── rknn_model.py          # RKNN NPU 推理封装
│
├── models/
│   ├── hands_detect.pt    # 手牌识别模型（52 类）
│   └── dealer.pt          # D 按钮检测模型（1 类）
│
├── rknn_models/
│   ├── hands_detect.rknn  # RKNN 量化模型（NPU 用）
│   └── dealer.rknn
│
├── range_viewer/
│   ├── backend/           # FastAPI 范围表服务
│   └── frontend/          # Vue 3 范围矩阵可视化
│
├── Kimi_Agent_6人桌现金局翻前范围/
│   ├── 6max_preflop_ranges_100bb.json   # GTO 数据
│   └── 6max_preflop_ranges_100bb.md     # 完整策略文档
│
├── dataset/               # YOLOv8 训练数据
├── tools/                 # ONNX 导出 + RKNN 转换
└── docs/                  # RK3588 部署文档
```

## 改进方向

- **翻后策略**：当前只支持翻前决策，后续可加入翻后（Flop/Turn/River）的策略建议
- **牌型判断**：在识别出牌面后，自动判断当前牌型（一对、顺子、同花等）
- **胜率估算**：结合蒙特卡洛模拟，基于当前手牌和公共牌估算胜率
- **对手建模**：根据对手的历史行为数据调整策略，从 GTO 向剥削性策略过渡
