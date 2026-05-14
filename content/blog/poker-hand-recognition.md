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

## 运行方式

```bash
cd project/poker_detect

python test_infer.py          # 默认置信度 0.25
python test_infer.py 0.5      # 自定义置信度阈值
```

脚本会依次推理 `1.png` 到 `13.png`，并将结果保存为 `*_result.jpg`。

## 项目结构

```
poker_detect/
├── best.pt            # YOLOv8 训练好的模型权重
├── test_infer.py      # 推理脚本（含聚类和分组逻辑）
├── 1.png ~ 13.png     # 测试用输入图片
└── *_result.jpg       # 推理结果输出
```

## 改进方向

- **视频流实时检测**：当前只处理静态图片，可接入摄像头或屏幕截图流实现实时识别
- **牌型判断**：在识别出牌面后，可进一步判断当前牌型（一对、顺子、同花等）
- **胜率估算**：结合蒙特卡洛模拟，基于当前手牌和公共牌估算胜率
- **多平台适配**：当前聚类参数基于特定牌桌布局，可加入自适应参数调整以适配不同平台
