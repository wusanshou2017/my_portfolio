---
title: RT-DETRv4 vs YOLOv8 — 行人检测模型对比实验
date: 2026-06-25
tags: [目标检测, RT-DETRv4, YOLOv8, DINOv3, 蒸馏, 深度学习]
description: 在自建行人检测数据集上对比 RT-DETRv4-L（DINOv3 蒸馏）与 YOLOv8s 的训练过程、收敛速度与最终精度，深入分析 DETR 系列的 two-stage 训练策略。
---

## 实验背景

目标检测领域近年出现两个明显趋势：

- **YOLO 系**（YOLOv5/v8/v11）—— anchor-free 单阶段检测器，速度快、生态成熟，但需要 NMS 后处理
- **DETR 系**（DETR / Deformable DETR / RT-DETR / D-FINE）—— 端到端集合预测，**无需 NMS**，传统上推理慢

2025 年 10 月的 **RT-DETRv4**（arXiv:2510.25257）通过引入 **DINOv3 视觉基础模型蒸馏**，在不增加推理开销的前提下进一步提升了精度。本次实验在自建行人数据集上，对 **YOLOv8s** 和 **RT-DETRv4-L（启用 DINOv3 蒸馏）** 进行端到端对比。

## 实验设置

为了让对比公平，两个模型使用 **相同的 train/val 划分**、**相同的输入尺寸 640×640**，指标统一为 mAP@0.5 / mAP@0.5:0.95 / mAP@0.75。

### YOLOv8s 配置

| 项目 | 值 |
|---|---|
| 任务 | 行人检测（单类 `person`） |
| 输入尺寸 | 640 × 640 |
| 数据格式 | YOLO txt + `data.yaml` |
| 训练轮数 | **399 epochs** |
| 范式 | Anchor-free + NMS |
| 训练技巧 | Mosaic、MixUp、EMA、Cosine LR |

### RT-DETRv4-L 配置

| 项目 | 值 |
|---|---|
| 任务 | 行人检测（单类 `person`） |
| 输入尺寸 | 640 × 640 |
| 数据格式 | COCO JSON（由 YOLO 自动转换） |
| 训练轮数 | **57 epochs** |
| 范式 | 端到端，无 NMS |
| Backbone | HGNetv2 (B4) |
| 特殊技巧 | DINOv3 ViT-B/16 **特征蒸馏** |

## 核心结果对比

### 主要精度指标

| 指标 | YOLOv8s | RT-DETRv4-L | 差值 |
| :--- | :---: | :---: | :---: |
| 训练 epoch 数 | 399 | **57** | -86% |
| **mAP@0.5** | 95.24% | **98.82%** | **+3.58%** |
| **mAP@0.5:0.95** | 82.80% | 82.50% | -0.29% |
| **mAP@0.75**（严格 IoU） | — | **91.42%** | — |

### 训练损失对比

| 损失项 | YOLOv8s | RT-DETRv4-L |
| :--- | :---: | :---: |
| box / bbox loss（L1） | 0.2814 | 0.0359 |
| cls / mal loss（分类） | 0.1846 | — |
| dfl / fgl loss（分布） | 0.8049 | — |
| giou loss（GIoU） | — | 0.0943 |
| total loss | 1.2709 | 17.7279 |

> 注：RT-DETRv4 的 total loss 是 6 种损失 × 多个分支加权求和（绝对值无意义，看趋势）。YOLOv8 的 total 是简单相加。

### 关键发现

**1. RT-DETRv4 收敛速度快 7 倍**

在 1/7 的训练 epoch 下，RT-DETRv4-L 反而取得了更高的 mAP@0.5。这得益于：

- DETR 的二分匹配避免了 NMS 训练时的正负样本歧义
- DINOv3 教师特征提供了稠密监督信号
- 多分支深度监督（decoder 中间层 + encoder + denoising）

**2. 高 IoU 阈值下 RT-DETRv4 完胜**

mAP@0.75（IoU=0.75）下 RT-DETRv4 达到 91.42%，说明检测框**贴合更紧、定位更准**。这是 D-FINE 风格的 corner 分布学习（`loss_fgl` + `loss_ddf`）带来的优势——把框回归视为分布预测，而非简单的 L1 距离。

**3. mAP@0.5:0.95 基本持平**

综合 AP（0.5:0.95）反而 YOLOv8s 略高 0.29%，主要因为 RT-DETRv4 在小目标 AP 上劣势（受 query 数量限制）。在中大目标上 RT-DETR 占优。

## Two-Stage 训练：为什么 loss 会突然下降？

### 现象

观察 RT-DETRv4-L 的训练 loss 曲线，会发现在 `stop_epoch`（L 模型默认 50，本次实验是 40）这个节点，**total loss 会出现一次非常明显的断崖式下降**。这不是 bug，而是 RT-DETRv4 沿用自 D-FINE 的 **Two-Stage 训练策略**。

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
Stage 1 末尾 (epoch 39):
  训练样本: Mosaic 拼接 + MixUp 混合 → 模型预测"扭曲"目标
  loss ≈ 30+ （看起来收敛缓慢）

         │
         │  ← epoch 40: 触发 stop_epoch
         ▼

Stage 2 第一个 epoch (epoch 40):
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
| epoch | 0 → stop_epoch（如 0-40） | stop_epoch → total_epochs（如 40-72） |
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

这意味着即使 Stage 2 训练崩溃或中断，你还能用 `best_stg1.pth` 兜底，工程上更稳健。

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

## 训练曲线分析

### Total Loss（关注 Stage 切换的断崖）

![训练总损失曲线](/images/rtdetr/loss.png)

总损失在前几个 epoch 快速下降，**在 epoch 40 处出现明显的断崖式下跌**，这正是 Stage 1 → Stage 2 切换的瞬间（关闭 Mosaic/MixUp + EMA 重启）。之后进入精修阶段，曲线平滑下降到 17.7 左右。

### 蒸馏损失 loss_distill

![DINOv3 蒸馏损失曲线](/images/rtdetr/loss_distill.png)

`loss_distill` 从初始的 1.0+ 下降到 0.3 左右，说明学生 backbone 学到的特征逐渐对齐到 DINOv3 的高层语义。如果该曲线长期保持 0，通常是教师权重损坏或维度不匹配，需要排查。

### 学习率调度（Flat-Cosine）

![学习率曲线](/images/rtdetr/lr.png)

采用 **Flat-Cosine** 调度：前 80% 训练保持恒定 LR（Flat 段），后 20% 用 Cosine 退火。这种调度对 DETR 系列比 YOLO 用的纯 Cosine 更稳定，且与 two-stage 训练策略天然契合——Flat 段对应 Stage 1 的探索，Cosine 段对应 Stage 2 的精修。

### mAP@0.5:0.95 曲线

![mAP@0.5:0.95 曲线](/images/rtdetr/ap.png)

### mAP@0.5 曲线

![mAP@0.5 曲线](/images/rtdetr/ap50.png)

mAP@0.5 在 30 epoch 左右就达到 95%+，**Stage 2 切换处也会出现一次跃升**（验证集本来就是干净分布），最终稳定在 98.82%。

## 训练过程总览

### 完整训练过程（多指标）

![完整训练过程](/images/rtdetr/training_process.png)

将训练前几个 epoch 的关键指标放在了一起：总损失、蒸馏损失、学习率、验证 mAP。

### 最终结果

![最终对比结果](/images/rtdetr/final_results.png)

最新一个 epoch 的 COCO 验证指标柱状图。

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

## 完整实验框架

为了让对比可复现，整个项目提供了完整的脚本链：

### 项目结构

```
redetr_model/
├── scripts/
│   ├── yolo_to_coco.py                # YOLO → COCO + 自动生成 RT-DETR 配置
│   ├── train_yolov8.py                # YOLOv8 训练/验证
│   ├── compare_yolov8_rtdetr.py       # 训练曲线对比绘图
│   ├── compare.py                     # 最终指标汇总 + 柱状图
│   ├── generate_comparison_report.py  # 自动生成对比报告
│   ├── setup_dinov3.py                # 下载 DINOv3 教师权重
│   └── plot_tensorboard.py            # TensorBoard 日志可视化
├── docs/
│   ├── rtdetrv4_losses.md             # 损失函数详解
│   ├── comparison_report_yolov8s_vs_rtdetrv4_l.md  # 最终对比报告
│   └── assets/tensorboard/            # 训练曲线图
├── RT-DETRv4/                         # 官方代码（已 clone）
│   ├── configs/custom/                # 自动生成的训练配置
│   └── figures/rtv4_ap_latency.png
├── deploy/model_compare_service/      # 推理对比服务
└── inference_rtdetr_val_samples.py    # 验证集抽样可视化
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
python train.py -c configs/custom/mydata_rtv4_l_distill.yml \
       --use-amp --seed=0 -t ../pretrain/rtdetrv4_l.pth

# 4. 训练 YOLOv8s（对照）
python ../scripts/train_yolov8.py --data ../data.yaml --model yolov8s.pt

# 5. 生成对比报告
python ../scripts/generate_comparison_report.py
python ../scripts/compare_yolov8_rtdetr.py \
       --yolo runs/detect/.../results.csv \
       --rtdetr RT-DETRv4/outputs/rtv4_l_custom_distill/log.txt \
       --out outputs/comparison.png
```

## 结论与思考

### 适合选 RT-DETRv4 的场景

- **需要高定位精度**：高 IoU 阈值下的 mAP 重要（如自动驾驶、医学影像）
- **厌恶 NMS 调参**：DETR 端到端，无 score 阈值与 IoU 阈值的耦合
- **小数据集 + 教师模型可用**：DINOv3 蒸馏在小数据上加速收敛明显
- **训练资源充裕**：DETR 训练比 YOLO 重，但本次实验反而 epoch 更少

### 适合选 YOLOv8 的场景

- **极度重视推理速度**：边缘设备、移动端
- **小目标检测为主**：query 数量限制让 RT-DETR 在小目标上略弱
- **生态成熟度**：部署链路、量化工具、社区案例 YOLO 更完善

### 实战启示

这次实验最让我意外的是 **57 epoch vs 399 epoch** 的对比。传统印象里 DETR 训练慢、收敛慢，但 RT-DETRv4 通过 **DINOv3 蒸馏 + Two-Stage 训练策略**，把这个偏见打破了：

- **收敛 epoch 数减少 86%**
- **mAP@0.5 反而提升 3.58%**
- **mAP@0.75 高达 91.42%**（高 IoU 下定位显著更准）

其中 Two-Stage 策略的断崖式 loss 下降是非常有意思的工程细节：**通过显式切换训练分布**，让模型先在"扭曲"样本上学泛化能力，再回到真实分布上精修，比 YOLOv8 简单的"关闭 Mosaic"更彻底、更可控。

如果你还在用 YOLOv8 做小数据集检测，强烈建议跑一次 RT-DETRv4 的对照实验，可能有意外的收获。
