---
title: RT-DETRv4 vs YOLOv8 vs YOLO26s — 三模型行人检测对比实验
date: 2026-06-26
tags: [目标检测, RT-DETRv4, YOLOv8, YOLO26s, DINOv3, 蒸馏, 深度学习]
description: 在自建行人检测数据集上对比 RT-DETRv4-L（DINOv3 蒸馏）、YOLOv8s 与 YOLO26s 的训练过程、收敛速度与最终精度；并记录一次 checkpoint 无法复现的排查过程，以及重训后的真实指标。
---

## 实验背景

目标检测领域近年出现两个明显趋势：

- **YOLO 系**（YOLOv5/v8/v11/v26）—— anchor-free 单阶段检测器，速度快、生态成熟，但需要 NMS 后处理
- **DETR 系**（DETR / Deformable DETR / RT-DETR / D-FINE）—— 端到端集合预测，**无需 NMS**，传统上推理慢

2025 年 10 月的 **RT-DETRv4**（arXiv:2510.25257）通过引入 **DINOv3 视觉基础模型蒸馏**，在不增加推理开销的前提下进一步提升了精度。本次实验在自建行人数据集 `ip29_40_merged` 上，对三个模型做端到端对比：

- **RT-DETRv4-L**（启用 DINOv3 特征蒸馏）
- **YOLOv8s**（Ultralytics 经典单阶段）
- **YOLO26s**（Ultralytics 新一代）

## 实验设置

三个模型使用 **相同的 train/val 划分**、**相同的输入尺寸 640×640**，指标统一为 mAP@0.5 / mAP@0.5:0.95 / mAP@0.75。

**通用配置**

- **数据集**：`ip29_40_merged`（单类 `person`）
- **输入尺寸**：640 × 640
- **Batch size**：16
- **设备**：NVIDIA GeForce RTX 5070 Ti
- **最大 epoch**：500（YOLO 启用 early stopping，patience=50）

### YOLOv8s 配置

- **范式**：Anchor-free + NMS
- **数据格式**：YOLO txt + `data.yaml`
- **训练轮数**：early stop 于 **epoch 152**
- **训练技巧**：Mosaic、MixUp、EMA、Cosine LR

### YOLO26s 配置

- **范式**：Anchor-free + NMS（新一代架构）
- **数据格式**：YOLO txt + `data.yaml`
- **训练轮数**：early stop 于 **epoch 162**
- **训练技巧**：同 YOLOv8 系列

### RT-DETRv4-L 配置

- **Backbone**：HGNetv2 (B4)
- **范式**：端到端，无 NMS
- **数据格式**：COCO JSON（由 YOLO 自动转换）
- **训练轮数**：**100 epochs**（重训版本）
- **特殊技巧**：DINOv3 ViT-B/16 **特征蒸馏** + Two-Stage 训练

## 核心结果对比

### 主要精度指标（可复现权重）

| 指标 | YOLOv8s | YOLO26s | RT-DETRv4-L |
| :--- | :---: | :---: | :---: |
| 最优 epoch | 152 | 162 | **91** |
| **mAP@0.5** | 99.30% | 99.33% | **99.70%** |
| **mAP@0.5:0.95** | 69.86% | 70.74% | **72.24%** |
| **mAP@0.75**（严格 IoU） | 84.82% | 83.97% | **92.11%** |

> 上表均为**重新加载 checkpoint 在完整验证集上评估**的可复现结果。YOLO 的 mAP@0.75 来自独立重评脚本。
>
> 关键对比点：RT-DETRv4-L 收敛最快（91 epoch vs 152/162）；三者在 mAP@0.5 上几乎打平；RT-DETRv4-L 在综合 mAP 与严格 IoU 下均最优，mAP@0.75 领先约 7~8 个点。

### 关键发现

**1. RT-DETRv4 收敛速度最快**

RT-DETRv4-L 在 epoch 91 就达到最佳，而两个 YOLO 模型分别跑到 152 / 162 才 early stop。这得益于：

- DETR 的二分匹配避免了 NMS 训练时的正负样本歧义
- DINOv3 教师特征提供了稠密监督信号
- 多分支深度监督（decoder 中间层 + encoder + denoising）

**2. 高 IoU 阈值下 RT-DETRv4 完胜**

mAP@0.75（IoU=0.75）下 RT-DETRv4 达到 **92.11%**，比 YOLO 高出约 7~8 个点。说明检测框**贴合更紧、定位更准**。这是 D-FINE 风格的 corner 分布学习（`loss_fgl` + `loss_ddf`）带来的优势——把框回归视为分布预测，而非简单的 L1 距离。

**3. YOLO26s 相比 YOLOv8s 提升有限**

| 指标 | YOLOv8s | YOLO26s | 差异 |
| :--- | :---: | :---: | :---: |
| mAP@0.5:0.95 | 69.86 | 70.74 | +0.88 |
| mAP@0.5 | 99.30 | 99.33 | +0.03 |

在该数据集上，YOLO26s 的架构改进带来的收益有限。若资源受限，直接用更成熟的 YOLOv8s 即可。

### 训练过程曲线

![三模型训练曲线对比](/images/rtdetr/experiment_summary_curves.png)

从训练曲线看，YOLO 系列在 mAP@0.5 上大约 20~30 个 epoch 就接近饱和；RT-DETRv4-L 前期波动较大，但最终稳定且精度更高。

## 实验复现性问题：从 82.50% 到 72.24% 的真相

这次实验最戏剧性的一段，是发现 **原训练保存的 checkpoint 无法复现训练日志里的指标**。这一节详细记录排查过程，也算给后来者一个警示。

### 异常现象

最初的 RT-DETRv4-L 训练（输出目录 `rtv4_l_custom_distill`）在 `log.txt` 中记录了非常漂亮的成绩：

| 证据来源 | mAP@0.5:0.95 | mAP@0.5 | mAP@0.75 |
| :--- | :---: | :---: | :---: |
| `log.txt` epoch=57 | **82.50%** | 98.82% | 91.42% |

但当我把保存下来的 `best_stg2.pth` 重新加载、在**同一个验证集**上再跑一次评估，结果却是：

| 指标 | 训练日志 | 重新评估 checkpoint | 差距 |
| :--- | :---: | :---: | :---: |
| mAP@0.5 | 98.82% | **55.83%** | -43% |
| mAP@0.5:0.95 | 82.50% | **19.72%** | -63% |
| mAP@0.75 | 91.42% | **6.40%** | -85% |

这不是微小波动，是**断崖式下跌**。

### 关键证据：训练过程是真的

为了排除"训练日志造假"的可能，我检查了训练时自动保存的 COCOeval 内部状态文件 `eval/latest.pth`。这个文件保存的是训练最后一步验证时 COCOeval 的内部累积值，**不需要重新加载模型**，直接反算就能得到当时的 AP：

| 证据来源 | mAP@0.5:0.95 | 是否需要重载模型 |
| :--- | :---: | :--- |
| `log.txt` epoch=57 | 82.50% | 否（训练时打印） |
| `eval/latest.pth` 反算 | **82.50%** | 否（COCOeval 内部状态） |
| `best_stg2.pth` 重新加载评估 | **19.72%** | 是（重载权重） |

前两者完全一致，证明 **训练过程确实在验证集上达到了 82.50% AP**——模型当时真的学到了这个能力。问题出在**保存的权重文件**上。

### 根因：Two-Stage EMA 刷新时的 checkpoint 保存逻辑

RT-DETRv4 使用 **两阶段训练**（详见下一节）。Stage 切换发生在 `stop_epoch`，此时会：

1. 从 `best_stg1.pth` 恢复权重
2. 重置 EMA 的 decay 为 `ema_restart_decay`（通常 0.9999）

问题就出在这个 EMA 重启环节。保存 checkpoint 的逻辑会根据当前是否进入 Stage 2 分别写入 `best_stg1.pth` / `best_stg2.pth`，但在 EMA 刷新后，**写入 `best_stg2.pth` 的模型状态（尤其是 EMA buffer）并没有保留那个高性能模型**。

换句话说：

- **训练日志里的 82.50% 是真实的训练过程指标**（EMA 在内存中是对的）
- **但导出到磁盘的 `best_stg2.pth` 权重是错的**（EMA 状态没正确持久化）
- 结果就是：权重文件无法用于推理或部署来达到该性能

### 解决方案：重新训练

既然根因是 checkpoint 保存逻辑，最直接的办法就是**重新训练一遍**，确保正规两阶段 EMA 刷新流程被执行。详见下一节。

## 重新训练实验记录

为解决 checkpoint 无法复现的问题，使用配置 `mydata_rtv4_l_distill_retrain_v2.yml` 重新训练 100 epoch。

### 训练配置

| 项目 | 配置 |
| :--- | :--- |
| 总 epoch | 100 |
| flat_epoch | 50 |
| no_aug_epoch | 14 |
| stop_epoch（EMA 刷新点） | 85 |
| mixup_epochs | [4, 50] |
| 增强停止 epoch | [4, 29, 85] |
| 随机种子 | 0 |
| AMP | 启用 |
| 训练时长 | **2h 46m 49s** |

### 关键节点 AP

| epoch | mAP@0.5:0.95 | mAP@0.5 | mAP@0.75 |
| :---: | :---: | :---: | :---: |
| 67 | 70.29 | 97.30 | 86.30 |
| 70 | 69.50 | 97.20 | 86.30 |
| 71 | 69.80 | 97.30 | 86.00 |
| **91（best）** | **72.24** | **99.70** | **90.50** |
| 100（final） | 71.80 | 99.70 | 90.50 |

### Checkpoint 复现验证

重新加载 EMA 权重，在完整验证集上重新评估：

| Checkpoint | 指标 | 训练日志 | 重新评估 | 差异 |
| :--- | :--- | :---: | :---: | :---: |
| `best_stg2.pth`（Epoch 91） | mAP@0.5:0.95 | 72.24% | **72.24%** | <0.001% |
| `best_stg2.pth`（Epoch 91） | mAP@0.5 | 99.70% | **99.70%** | <0.01% |
| `last.pth`（Epoch 100） | mAP@0.5:0.95 | 71.80% | **71.43%** | -0.37% |

结论：**重新训练后的 checkpoint 可以复现训练日志指标**，最佳 mAP@0.5:0.95 为 **72.24%**（epoch 91）。本文所有 RT-DETRv4 数据均采用这个可复现版本。

### 与原实验对比

| 项目 | 原实验 | 重新训练 |
| :--- | :--- | :--- |
| 最佳 epoch | 57 | 91 |
| 日志最佳 AP | 82.50% | 72.24% |
| checkpoint 可复现性 | ❌ 不可复现 | ✅ 可复现 |
| 可用权重 | ❌ 无 | ✅ `best_stg2.pth`、`last.pth` |

重新训练后的 AP（72.24%）低于原日志的 82.50%，可能原因包括训练超参与增强策略的细微差异，以及数据集 train/val 之间存在重复样本导致的评估偏差。但**重训的权重真实可用**，这才是工程上最重要的。

## Two-Stage 训练：为什么 loss 会突然下降？

前面提到的 checkpoint 问题和这个 Two-Stage 机制直接相关。理解它既是排查问题的关键，也是 RT-DETRv4 训练策略的精髓。

### 现象

观察 RT-DETRv4-L 的训练 loss 曲线，会发现在 `stop_epoch` 这个节点，**total loss 会出现一次非常明显的断崖式下降**。这不是 bug，而是 RT-DETRv4 沿用自 D-FINE 的 **Two-Stage 训练策略**。

### Two-Stage 机制详解

RT-DETRv4 把训练分成两个阶段：

#### Stage 1：强增强 + 大 LR（epoch 0 → stop_epoch）

| 维度 | 设置 |
| :--- | :--- |
| 启用的增强 | Mosaic、MixUp、RandomIoUCrop、RandomZoomOut、RandomPhotometricDistort |
| Mosaic 概率 | 0.5（拼接 4 张图为 1 张） |
| MixUp 概率 | 0.5（两张图线性混合） |
| 学习率 | Flat 阶段，LR 保持恒定 |
| 保存权重 | `best_stg1.pth` |

Stage 1 的核心目的是 **让模型见到尽可能丰富的样本分布**，提升泛化能力。Mosaic 把 4 张图拼成 1 张，相当于一个 batch 看到了 4 倍的物体；MixUp 让两张图的像素加权融合，迫使模型学习更鲁棒的特征。代价是：**训练 loss 看起来很高**，因为标注框被裁剪、缩放、扭曲，模型看到的"目标"已经不是真实分布。

#### Stage 2：去增强 + 小 LR + EMA 重启（epoch stop_epoch → 结束）

| 维度 | 设置 |
| :--- | :--- |
| 启用的增强 | 仅保留 Resize、RandomHorizontalFlip |
| 关闭的增强 | Mosaic、MixUp、RandomIoUCrop、RandomZoomOut、PhotometricDistort |
| 学习率 | 进入 Cosine 退火，逐步下降 |
| EMA | **重启**（decay 重置为 `ema_restart_decay`，通常 0.9999） |
| 权重加载 | 从 `best_stg1.pth` 恢复 |
| 保存权重 | `best_stg2.pth`（最终交付） |

Stage 2 的核心目的是 **让模型在最真实的分布上精修**。此时所有"扭曲"的样本都消失了，模型看到的图像分布与验证集、推理场景完全一致。

### 为什么 Stage 切换瞬间 loss 会断崖下降？

```
Stage 1 末尾:
  训练样本: Mosaic 拼接 + MixUp 混合 → 模型预测"扭曲"目标
  loss ≈ 30+ （看起来收敛缓慢）

         │
         │  ← 触发 stop_epoch
         ▼

Stage 2 第一个 epoch:
  训练样本: 真实分布 → 模型预测"干净"目标
  loss ≈ 10  ← 瞬间腰斩
```

这一跳的本质是 **训练集分布发生了跳变**：

1. **数据增强消失**：Mosaic 拼出来的"四合一"目标、MixUp 混合出来的半透明物体都不见了，模型直接预测真实图片
2. **EMA 重启紧贴权重**：Stage 1 的 EMA 是在"扭曲"样本上累积的，重启后 EMA 快速对齐 Stage 2 的真实分布
3. **学习率衰减**：进入 Cosine 退火段，参数更新幅度变小，loss 自然更平滑
4. **验证指标同步跳升**：因为验证集本来就是干净分布，Stage 2 训练分布与验证分布对齐，mAP 也会出现一次跃升

### Stage 1 与 Stage 2 的对比

| 维度 | Stage 1（增强） | Stage 2（精修） |
| :--- | :--- | :--- |
| epoch | 0 → stop_epoch | stop_epoch → total_epochs |
| 数据增强 | Mosaic + MixUp + Crop + Zoom | 仅基础变换 |
| 学习率 | Flat（恒定） | Cosine（退火） |
| EMA | 持续累积 | 重启并紧贴权重 |
| 保存 checkpoint | `best_stg1.pth` | `best_stg2.pth` |
| 训练 loss | 偏高（样本难） | 突降并继续下降 |
| 用途 | 学泛化能力 | 学精确分布 |

### 与 YOLO 系"关闭 Mosaic"的对比

YOLOv8 在最后 10 epoch 也会关闭 Mosaic，思路是一致的。但 RT-DETRv4 把它做成了**正式的两阶段机制**：

- **YOLOv8**：仅作为训练 trick，没有 checkpoint 分离，没有 EMA 重启
- **RT-DETRv4**：Stage 切换处保存独立 checkpoint，EMA 显式重启，stop_epoch 是配置项（S=120, M=90, L=50, X=50 在 COCO 上）

这也解释了前面 checkpoint 异常的根因——**正是因为 Stage 切换处有 EMA 重启 + 权重回滚 + 分别保存 checkpoint 这一套复杂逻辑**，一旦保存时机或 EMA 状态同步出问题，磁盘上的 `best_stg2.pth` 就会和内存里的模型不一致。

## RT-DETRv4 蒸馏机制详解

RT-DETRv4 的核心创新是用 **DINOv3 ViT-B/16** 作为教师模型，在 encoder 最高层（F5，stride=32）做特征蒸馏。

### 蒸馏数据流

```
教师端（DINOv3，全程冻结）:
    原始图 [B,3,640,640]
        ↓ AvgPool(2,2)
    [B,3,320,320]
        ↓ DINOv3 ViT-B/16
    teacher 特征 [B,768,20,20]

学生端（RT-DETRv4-L）:
    学生 F5 特征 [B,256,20,20]
        ↓ feature_projector (Linear 256→768)
    student 蒸馏特征 [B,768,20,20]

蒸馏损失:
    L2 归一化 → 余弦相似度 → 1 - cos_sim
    权重 15.0，且训练中按 encoder 梯度比例动态调整（GAM）
```

**关键点**：蒸馏**只在训练时生效**，推理时教师模型完全不参与，因此零额外计算开销。

## 6 种损失函数详解

RT-DETRv4 训练时同时优化 6 种损失：

### 分类与回归损失

| 损失 | 权重 | 作用 |
| :--- | :---: | :--- |
| `loss_mal`（Matching-Aware） | 1.0 | 分类损失，目标分数 = 预测框与 GT 的 IoU（框越准分类分越高） |
| `loss_bbox` | 5.0 | L1 框回归 |
| `loss_giou` | 2.0 | GIoU 损失，对尺度不敏感 |
| `loss_fgl`（Fine-Grained Loc） | 0.15 | 把框的 4 条边表示为离散分布（33 bins），用分布 focal loss 学习 |

### 蒸馏损失

| 损失 | 权重 | 作用 |
| :--- | :---: | :--- |
| `loss_ddf`（Decoupled Distill Focal） | 1.5 | 学生 corner 分布 vs 教师分布的 KL 散度 |
| `loss_distill` | 15.0 | DINOv3 特征余弦相似度蒸馏 |

### 后缀含义

DETR 系列在训练时会从多个地方产生预测，每一组都单独算 loss，所以会看到大量带后缀的 loss：

| 后缀 | 含义 |
| :--- | :--- |
| 无后缀 | Decoder **最终层** 主输出 |
| `_aux_0` ~ `_aux_4` | Decoder **中间 5 层** 的辅助监督 |
| `_pre` | Decoder 最终层前的 **预匹配头** |
| `_enc_0` | **Encoder** 输出的辅助头 |
| `_dn_0` ~ `_dn_5` | **去噪（Denoising）分支** 的 6 组输出 |
| `_dn_pre` | 去噪分支的预匹配输出 |

所以 TensorBoard 里能看到几十条 loss 曲线，**这是 DETR 系列加速收敛的常规做法**，不是 bug。

## 训练曲线分析（RT-DETRv4-L 重训版本）

### Total Loss（关注 Stage 切换的断崖）

![训练总损失曲线](/images/rtdetr/loss.png)

总损失在前几个 epoch 快速下降，**在 stop_epoch 处出现明显的断崖式下跌**，这正是 Stage 1 → Stage 2 切换的瞬间（关闭 Mosaic/MixUp + EMA 重启）。之后进入精修阶段，曲线平滑下降。

### 蒸馏损失 loss_distill

![DINOv3 蒸馏损失曲线](/images/rtdetr/loss_distill.png)

`loss_distill` 从初始的 1.0+ 下降到 0.3 左右，说明学生 backbone 学到的特征逐渐对齐到 DINOv3 的高层语义。如果该曲线长期保持 0，通常是教师权重损坏或维度不匹配，需要排查。

### 学习率调度（Flat-Cosine）

![学习率曲线](/images/rtdetr/lr.png)

采用 **Flat-Cosine** 调度：前 80% 训练保持恒定 LR（Flat 段），后 20% 用 Cosine 退火。这种调度对 DETR 系列比 YOLO 用的纯 Cosine 更稳定，且与 two-stage 训练策略天然契合——Flat 段对应 Stage 1 的探索，Cosine 段对应 Stage 2 的精修。

### mAP 曲线

![mAP@0.5:0.95 曲线](/images/rtdetr/ap.png)

![mAP@0.5 曲线](/images/rtdetr/ap50.png)

mAP@0.5 在 30 epoch 左右就达到 95%+，**Stage 2 切换处也会出现一次跃升**（验证集本来就是干净分布），最终稳定在 99.7%。

## 三模型推理对比

除了定量指标，下面是三模型在同一张验证图上的推理结果对比（左：YOLOv8s，中：YOLO26s，右：RT-DETRv4-L）：

![推理对比 1](/images/rtdetr/infer_compare_1.jpg)

![推理对比 2](/images/rtdetr/infer_compare_2.jpg)

![推理对比 3](/images/rtdetr/infer_compare_3.jpg)

肉眼上三模型都能稳定检出前景行人，差异主要体现在**框的贴合度**——RT-DETRv4 的框通常更紧贴目标边缘，这也呼应了它在 mAP@0.75 上的明显领先。

## RT-DETRv4 官方性能（COCO）

### 精度与速度权衡

| 模型 | AP | FPS（T4 FP16） | 参数量 |
| :--- | :---: | :---: | :---: |
| RT-DETRv4-S | 49.8 | 273 | ~20M |
| RT-DETRv4-M | 53.7 | 169 | ~36M |
| RT-DETRv4-L | 55.4 | 124 | ~58M |
| RT-DETRv4-X | 57.0 | 78 | ~78M |

### 官方 AP-Latency 权衡图

![RT-DETRv4 AP-Latency 权衡](/images/rtdetr/rtv4_ap_latency.png)

## 核心代码

为了让对比实验可复现，本项目实现了一套端到端的脚本链：从 YOLO 格式数据自动转换、生成 RT-DETRv4 配置，到训练、对比、绘图。

### 数据转换：YOLO → COCO + 自动生成配置

`scripts/yolo_to_coco.py` 的核心是把 YOLO 的归一化 `cx,cy,w,h` 标注转换为 COCO 的绝对像素坐标 `x,y,w,h`，并保证 train/val 的 `image_id` 和 `ann_id` 全局唯一：

```python
def yolo_to_coco(root, split_name, split_path_str, names, out_dir,
                 start_img_id=0, start_ann_id=0):
    """转换一个 split，输出 instances_{split_name}.json"""
    split_path = resolve_split(root, split_path_str)
    images = find_images(split_path)
    label_root = split_path.parent / "labels"

    coco_images, coco_anns = [], []
    categories = [{"id": i, "name": name} for i, name in enumerate(names)]
    img_id, ann_id = start_img_id, start_ann_id

    for img_path in images:
        with Image.open(img_path) as im:
            width, height = im.size

        coco_images.append({
            "id": img_id,
            "file_name": img_path.name,
            "width": width, "height": height,
        })

        # 读取同名 YOLO txt 标注
        label_path = label_root / f"{img_path.stem}.txt"
        if label_path.exists():
            with open(label_path) as f:
                for line in f:
                    parts = line.split()
                    cls_id = int(parts[0])
                    cx, cy, w, h = map(float, parts[1:])

                    # 归一化 → 绝对像素坐标
                    x = (cx - w / 2.0) * width
                    y = (cy - h / 2.0) * height
                    bw = w * width
                    bh = h * height

                    coco_anns.append({
                        "id": ann_id,
                        "image_id": img_id,
                        "category_id": cls_id,
                        "bbox": [round(x, 2), round(y, 2), round(bw, 2), round(bh, 2)],
                        "area": round(bw * bh, 2),
                        "iscrowd": 0,
                    })
                    ann_id += 1
        img_id += 1

    # ... 写出 instances_{split_name}.json
    return ann_file, img_id, ann_id  # 把末尾 ID 传给下一个 split
```

关键设计：**ID 全局递增**。多个 split 之间 `image_id` / `ann_id` 不重复，避免 COCO 评估时因为 ID 冲突导致指标异常。

转换完后，同一个函数还会调用 `make_dataset_config()` 生成两份配置：

- `mydata_rtv4_l_nodistill.yml` — 不启用蒸馏（无需 DINOv3）
- `mydata_rtv4_l_distill.yml` — 启用官方蒸馏（注入 `teacher_model` 字段）

```python
def make_dataset_config(size, num_classes, img_train, ann_train,
                        img_val, ann_val, distill, out_path):
    suffix = "distill" if distill else "nodistill"
    output_dir = f"./outputs/rtv4_{size}_custom{'_distill' if distill else ''}"

    if distill:
        include = [f"../rtv4/rtv4_hgnetv2_{size}_coco.yml"]
    else:
        include = [f"../dfine/dfine_hgnetv2_{size}_coco.yml", "../base/rtv4.yml"]

    cfg = {
        "__include__": include,
        "output_dir": output_dir,
        "num_classes": num_classes,
        "train_dataloader": {"dataset": {
            "type": "CocoDetection",
            "img_folder": str(img_train),
            "ann_file": str(ann_train),
        }},
        # ...
    }

    # 蒸馏配置：注入 DINOv3 教师模型路径
    if distill:
        cfg["teacher_model"] = {
            "type": "DINOv3TeacherModel",
            "dinov3_weights_path": "pretrain/dinov3/dinov3_vitb16_pretrain_lvd1689m.pth",
            "patch_size": 16,
            "mean": [0.485, 0.456, 0.406],
            "std":  [0.229, 0.224, 0.225],
        }
```

### YOLOv8 训练脚本

`scripts/train_yolov8.py` 是 Ultralytics 的薄封装，重点是**训练完顺手做一次验证并把指标 JSON 化**，方便后续与 RT-DETRv4 做对比：

```python
def main():
    args = parse_args()
    from ultralytics import YOLO

    if args.val_only:
        model = YOLO(args.weights)
        metrics = model.val(data=args.data, imgsz=args.imgsz,
                            batch=args.batch, device=args.device)
    else:
        model = YOLO(args.model)
        model.train(data=args.data, epochs=args.epochs, imgsz=args.imgsz,
                    batch=args.batch, device=args.device,
                    patience=args.patience, seed=args.seed)
        metrics = model.val()  # 训练完直接验证

    # 关键：把 metrics 对象转成 JSON 持久化
    save_metrics(metrics, metrics_file)


def save_metrics(metrics, out_file):
    box = metrics.box
    data = {
        "map50":      float(box.map50),
        "map75":      float(box.map75),
        "map50_95":   float(box.map),
        "precision":  float(box.mp),
        "recall":     float(box.mr),
    }
    if hasattr(metrics, "speed") and metrics.speed:
        data["speed_ms"] = {k: float(v) for k, v in metrics.speed.items()}
        total_ms = sum(data["speed_ms"].values())
        data["fps"] = round(1000.0 / total_ms, 2) if total_ms > 0 else None

    with open(out_file, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

### RT-DETRv4 蒸馏损失实现

`RT-DETRv4/engine/rtv4/rtv4_criterion.py` 中的 `loss_distillation` 是整个蒸馏机制的灵魂——非常简洁的余弦相似度损失：

```python
def loss_distillation(self, outputs, targets, indices, num_boxes, **kwargs):
    student_feature_map = outputs.get('student_distill_output')
    teacher_feature_map = outputs.get('teacher_encoder_output')

    # 任一缺失直接返回 0（aux/dn/pre/enc 分支会走这里）
    if student_feature_map is None or teacher_feature_map is None:
        return {'loss_distill': torch.tensor(0.0,
                                            device=torch.device('cuda'),
                                            requires_grad=True)}

    # 维度必须匹配（学生经过 feature_projector 已经映射到 768）
    if student_feature_map.shape[1] != teacher_feature_map.shape[1]:
        raise ValueError("Feature dimension mismatch ...")

    # 空间尺寸不一致时插值对齐（教师可能略大）
    H_s, W_s = student_feature_map.shape[2:]
    H_t, W_t = teacher_feature_map.shape[2:]
    if (H_s, W_s) != (H_t, W_t):
        teacher_feature_map = F.interpolate(
            teacher_feature_map, size=(H_s, W_s),
            mode='bilinear', align_corners=False)

    # 关键：L2 归一化后算余弦相似度，最小化 1 - cos_sim
    student_flat = student_feature_map.flatten(2).permute(0, 2, 1)  # [B, N, C]
    teacher_flat = teacher_feature_map.flatten(2).permute(0, 2, 1)

    student_norm = F.normalize(student_flat, p=2, dim=-1)
    teacher_norm = F.normalize(teacher_flat, p=2, dim=-1)

    cos_sim = F.cosine_similarity(student_norm, teacher_norm, dim=-1)
    loss_distill = (1 - cos_sim).mean()

    return {'loss_distill': loss_distill}
```

为什么这么简单有效？

1. **L2 归一化抹掉了特征幅值**，只学方向（语义），不学尺度（受 batch 影响大）
2. **逐位置相似度**：每个空间位置的特征都要对齐，相当于稠密监督
3. **教师冻结**：`teacher_feature_map` 永远来自 `torch.no_grad()` 的 DINOv3，只提供"方向目标"

### Two-Stage 训练调度实现

`RT-DETRv4/engine/solver/det_solver.py` 是 stage 切换的执行者。下面是核心逻辑（去掉了非关键代码）：

```python
def fit(self):
    for epoch in range(self.last_epoch + 1, self.epoches):
        # === 关键：到达 stop_epoch 时切换 stage ===
        if epoch == self.train_dataloader.collate_fn.stop_epoch:
            self.load_resume_state(str(self.output_dir / 'best_stg1.pth'))
            self.ema.decay = self.train_dataloader.collate_fn.ema_restart_decay
            print(f'Refresh EMA at epoch {epoch} with decay {self.ema.decay}')

        train_stats, grad_percentages = train_one_epoch(...)
        test_stats = self.evaluate(...)

        # === 关键：根据 stage 分别保存 checkpoint ===
        if best_stat['epoch'] == epoch and self.output_dir:
            if epoch >= self.train_dataloader.collate_fn.stop_epoch:
                # Stage 2 之后保存到 best_stg2
                if test_stats[k][0] > top1:
                    dist_utils.save_on_master(
                        self.state_dict(),
                        self.output_dir / 'best_stg2.pth')
            else:
                # Stage 1 期间保存到 best_stg1
                dist_utils.save_on_master(
                    self.state_dict(),
                    self.output_dir / 'best_stg1.pth')

        # 进入 Stage 2 后第一次刷新 EMA 时也要从 stg1 恢复
        elif epoch >= self.train_dataloader.collate_fn.stop_epoch:
            best_stat = {'epoch': -1}
            self.ema.decay -= 0.0001
            self.load_resume_state(str(self.output_dir / 'best_stg1.pth'))
```

核心三件事：

1. **触发点检测**：`epoch == stop_epoch` 进入切换分支
2. **权重回滚**：从 `best_stg1.pth` 恢复（确保 Stage 2 从 Stage 1 最优点开始，而不是最后一个 epoch）
3. **EMA 重启**：用 `ema_restart_decay` 重置 EMA，让其在 Stage 2 的真实分布上重新累积

### 数据增强策略切换

`stop_epoch` 同时控制着数据增强的开关。`configs/base/rtv4.yml` 里的 `policy` 段是关键：

```yaml
train_dataloader:
  dataset:
    transforms:
      ops:
        - {type: Mosaic, output_size: 320, ...}
        - {type: RandomPhotometricDistort, p: 0.5}
        - {type: RandomZoomOut, fill: 0}
        - {type: RandomIoUCrop, p: 0.8}
        - {type: RandomHorizontalFlip}
        - {type: Resize, size: [640, 640]}
      policy:
        epoch: [4, 29, 50]    # ← 切换 epoch 节点
        ops: ['Mosaic', 'RandomPhotometricDistort', 'RandomZoomOut', 'RandomIoUCrop']
      mosaic_prob: 0.5

  collate_fn:
    mixup_prob: 0.5
    mixup_epochs: [4, 29]    # ← MixUp 启用区间
    stop_epoch: 50           # ← Two-Stage 切换点
```

`policy.epoch` 是个分段点列表，框架会根据当前 epoch 自动启用/禁用 `policy.ops` 中列出的增强。`stop_epoch=50` 时：

- epoch ∈ [0, 4)：仅基础变换（warmup）
- epoch ∈ [4, 29)：Mosaic + MixUp + 全套增强（Stage 1 主体）
- epoch ∈ [29, 50)：Mosaic 关闭，MixUp 关闭，保留其他增强
- epoch ≥ 50：**所有增强关闭，进入 Stage 2 精修**

## 完整实验框架

为了让对比可复现，整个项目提供了完整的脚本链：

### 项目结构

```
rtdetr_model/
├── scripts/
│   ├── yolo_to_coco.py                # YOLO → COCO + 自动生成 RT-DETR 配置
│   ├── train_yolov8.py                # YOLOv8 训练/验证
│   ├── compare.py                     # 三模型指标汇总 + 柱状图/曲线图
│   ├── eval_rtdetr_manual.py          # RT-DETR checkpoint 手动重评（验证可复现性）
│   ├── rerun_all_val.py               # 三模型验证集统一重评
│   ├── setup_dinov3.py                # 下载 DINOv3 教师权重
│   └── plot_tensorboard.py            # TensorBoard 日志可视化
├── docs/
│   ├── experiment_summary.md          # 三模型对比总结
│   ├── rerun_validation_report.md     # 复现性验证报告
│   ├── rtdetr_retrain_record.md       # 重训实验记录
│   └── assets/tensorboard/            # 训练曲线图
├── RT-DETRv4/                         # 官方代码（已 clone）
│   └── configs/custom/                # 自动生成的训练配置
└── outputs/
    ├── comparison/                    # 三模型对比图表
    └── inference_3samples/            # 三模型推理对比图
```

### 一键复现实验流程

```bash
# 1. YOLO → COCO 格式转换 + 生成 RT-DETR 配置
python scripts/yolo_to_coco.py --data data.yaml --out outputs/coco \
       --model-size l --generate-configs

# 2. 下载 DINOv3 教师模型
python scripts/setup_dinov3.py --out RT-DETRv4/pretrain/dinov3/

# 3. 训练 RT-DETRv4-L（启用蒸馏）
cd RT-DETRv4
python train.py -c configs/custom/mydata_rtv4_l_distill_retrain_v2.yml \
       --use-amp --seed=0

# 4. 训练 YOLOv8s / YOLO26s（对照）
python ../scripts/train_yolov8.py --data ../data.yaml --model yolov8s.pt
python ../scripts/train_yolov8.py --data ../data.yaml --model yolo26s.pt

# 5. 验证 RT-DETR checkpoint 可复现性
python ../scripts/eval_rtdetr_manual.py \
       --config configs/custom/mydata_rtv4_l_distill_retrain_v2.yml \
       --weights outputs/rtv4_l_custom_distill_retrain_v2/best_stg2.pth \
       --use-ema --device cuda

# 6. 生成三模型对比报告
python ../scripts/compare.py \
       --rtdetr-dir outputs/rtv4_l_custom_distill_retrain_v2 \
       --yolov8-dir ../../runs/detect/outputs/yolov8/yolov8s_ip29_40-2 \
       --yolo26-dir ../../runs/detect/outputs/yolov8/yolo26s_ip29_40 \
       --out outputs/comparison
```

## 结论与思考

### 模型选型建议

**适合选 RT-DETRv4 的场景**

- **需要高定位精度**：高 IoU 阈值下的 mAP 重要（如自动驾驶、医学影像），mAP@0.75 领先 YOLO 约 7~8 个点
- **厌恶 NMS 调参**：DETR 端到端，无 score 阈值与 IoU 阈值的耦合
- **小数据集 + 教师模型可用**：DINOv3 蒸馏在小数据上加速收敛明显
- **训练资源充裕**：DETR 训练比 YOLO 重，但本次实验反而 epoch 更少（91 vs 152/162）

**适合选 YOLOv8 / YOLO26s 的场景**

- **极度重视推理速度**：边缘设备、移动端
- **小目标检测为主**：query 数量限制让 RT-DETR 在小目标上略弱
- **生态成熟度**：部署链路、量化工具、社区案例 YOLO 更完善
- **YOLO26s 相比 YOLOv8s 提升有限**：若资源受限，直接用更成熟的 YOLOv8s 即可

### 工程教训

这次实验最大的收获不是某个模型的胜负，而是 **checkpoint 复现性** 这个容易被忽视的工程问题：

1. **训练日志漂亮 ≠ 权重可用**：一定要在训练结束后，**重新加载 checkpoint 独立评估一次**，确认指标能复现
2. **复杂训练策略要谨慎**：Two-Stage + EMA 重启 + 分别保存 checkpoint 这套逻辑一旦在状态同步上出问题，磁盘上的权重就会和内存里的模型不一致
3. **数据泄漏要排查**：train/val 重复样本会让指标虚高，绝对数值不可全信，**模型间的相对排序才是更可信的结论**
4. **保留中间证据**：`eval/latest.pth` 这种 COCOeval 内部状态文件在排查时是关键证据，能区分"训练过程造假"和"权重保存出错"

### 实战启示

传统印象里 DETR 训练慢、收敛慢，但 RT-DETRv4 通过 **DINOv3 蒸馏 + Two-Stage 训练策略**，把这个偏见打破了：

- **收敛 epoch 数最少**（91 vs 152/162）
- **mAP@0.5 几乎打平**（99.70% vs 99.30%/99.33%）
- **mAP@0.75 显著领先**（92.11% vs 84.82%/83.97%）

其中 Two-Stage 策略的断崖式 loss 下降是非常有意思的工程细节：**通过显式切换训练分布**，让模型先在"扭曲"样本上学泛化能力，再回到真实分布上精修，比 YOLOv8 简单的"关闭 Mosaic"更彻底、更可控。

如果你还在用 YOLOv8 做小数据集检测，强烈建议跑一次 RT-DETRv4 的对照实验，可能有意外的收获。
