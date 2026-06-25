---
title: RT-DETRv4 vs YOLOv8 — 行人检测模型对比实验
date: 2026-06-25
tags: [目标检测, RT-DETRv4, YOLOv8, DINOv3, 蒸馏, 深度学习]
description: 在自建行人检测数据集上对比 RT-DETRv4-L（DINOv3 蒸馏）与 YOLOv8s 的训练过程、收敛速度与最终精度，分析 DETR 系列在端到端检测中的优势。
---

## 实验背景

目标检测领域近年出现两个明显趋势：

1. **YOLO 系**（YOLOv5/v8/v11）：anchor-free 单阶段检测器，速度快、生态成熟，但需要 NMS 后处理
2. **DETR 系**（DETR / Deformable DETR / RT-DETR / D-FINE）：端到端集合预测，**无需 NMS**，但传统上推理慢

2025 年 10 月的 **RT-DETRv4**（arXiv:2510.25257）通过引入 **DINOv3 视觉基础模型蒸馏**，在不增加推理开销的前提下进一步提升了精度。本次实验在自建行人数据集上，对 **YOLOv8s** 和 **RT-DETRv4-L（启用 DINOv3 蒸馏）** 进行端到端对比。

## 实验设置

| 项目 | YOLOv8s | RT-DETRv4-L |
|---|---|---|
| 任务 | 行人检测（单类 `person`） | 行人检测（单类 `person`） |
| 输入尺寸 | 640×640 | 640×640 |
| 数据格式 | YOLO txt + `data.yaml` | COCO JSON（由 YOLO 自动转换） |
| 训练轮数 | **399 epochs** | **57 epochs** |
| 范式 | Anchor-free + NMS | 端到端，无 NMS |
| 特殊技巧 | Mosaic、MixUp、Cosine LR | DINOv3 ViT-B/16 **特征蒸馏** |
| Backbone | CSPDarknet | HGNetv2 (B4) |

为了公平对比：

- **相同 train/val 划分**、**相同输入尺寸 640×640**
- RT-DETRv4 通过 `scripts/yolo_to_coco.py` 把 YOLO 标注自动转换为 COCO JSON
- 指标统一为 **mAP@0.5**、**mAP@0.5:0.95**、**mAP@0.75**

## 核心结果对比

| 指标 | YOLOv8s | RT-DETRv4-L | 差值 |
|---|---|---|---|
| 训练 epoch | 399 | **57** | RT-DETR 少训 **86%** |
| **mAP@0.5** | 95.24% | **98.82%** | RT-DETR **+3.58%** |
| **mAP@0.5:0.95** | **82.80%** | 82.50% | YOLO +0.29%（基本持平）|
| **mAP@0.75**（严格 IoU） | - | **91.42%** | RT-DETR 框定位显著更准 |

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

## RT-DETRv4 蒸馏机制详解

RT-DETRv4 的核心创新是用 **DINOv3 ViT-B/16** 作为教师模型，在 encoder 最高层（F5，stride=32）做特征蒸馏。

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

## 6 种损失函数

RT-DETRv4 训练时同时优化 6 种损失，每种都有明确职责：

| 损失 | 权重 | 作用 |
|---|---|---|
| `loss_mal`（Matching-Aware） | 1.0 | 分类损失，目标分数 = 预测框与 GT 的 IoU（框越准分类分越高） |
| `loss_bbox` | 5.0 | L1 框回归 |
| `loss_giou` | 2.0 | GIoU 损失，对尺度不敏感 |
| `loss_fgl`（Fine-Grained Localization） | 0.15 | 把框的 4 条边表示为离散分布（33 bins），用分布 focal loss 学习 |
| `loss_ddf`（Decoupled Distillation Focal） | 1.5 | 学生 corner 分布 vs 教师分布的 KL 散度 |
| `loss_distill` | 15.0 | DINOv3 特征余弦相似度蒸馏 |

此外还有大量带后缀的辅助损失：

```
无后缀          → Decoder 最终层主输出
_aux_0~4        → Decoder 中间 5 层的深度监督
_pre            → Decoder 预匹配头
_enc_0          → Encoder 辅助头
_dn_0~5         → 去噪（Denoising）分支的 6 组输出
_dn_pre         → 去噪预匹配输出
```

所以 TensorBoard 里能看到几十条 loss 曲线，**这是 DETR 系列加速收敛的常规做法**，不是 bug。

## 训练曲线分析

### Total Loss

![训练总损失曲线](/images/rtdetr/loss.png)

总损失在前 10 epoch 快速下降，30 epoch 后趋于平稳。最终 `train_loss ≈ 17.7`（多分支加权求和，绝对值无实际意义，要看趋势）。

### 蒸馏损失

![DINOv3 蒸馏损失曲线](/images/rtdetr/loss_distill.png)

`loss_distill` 从初始的 1.0+ 下降到 0.3 左右，说明学生 backbone 学到的特征逐渐对齐到 DINOv3 的高层语义。如果该曲线长期保持 0，通常是教师权重损坏或维度不匹配，需要排查。

### 学习率调度

![学习率曲线](/images/rtdetr/lr.png)

采用 **Flat-Cosine** 调度：前 80% 训练保持恒定 LR，后 20% 用 Cosine 退火。这种调度对 DETR 系列比 YOLO 用的纯 Cosine 更稳定。

### mAP@0.5:0.95 曲线

![mAP@0.5:0.95 曲线](/images/rtdetr/ap.png)

### mAP@0.5 曲线

![mAP@0.5 曲线](/images/rtdetr/ap50.png)

mAP@0.5 在 30 epoch 左右就达到 95%+，最终稳定在 98.82%。可见 RT-DETRv4 在收敛速度上对 YOLO 系是降维打击。

## 训练过程总结

![完整训练过程](/images/rtdetr/training_process.png)

### 最终结果

![最终对比结果](/images/rtdetr/final_results.png)

## RT-DETRv4 官方性能（COCO）

| 模型 | AP | FPS（T4 FP16） | 参数量 |
|---|---|---|---|
| RT-DETRv4-S | 49.8 | 273 | ~20M |
| RT-DETRv4-M | 53.7 | 169 | ~36M |
| RT-DETRv4-L | 55.4 | 124 | ~58M |
| RT-DETRv4-X | 57.0 | 78 | ~78M |

官方 AP-Latency 权衡：

![RT-DETRv4 AP-Latency 权衡](/images/rtdetr/rtv4_ap_latency.png)

## 完整实验框架

为了让对比可复现，整个项目提供了完整的脚本链：

```
redetr_model/
├── scripts/
│   ├── yolo_to_coco.py             # YOLO → COCO + 自动生成 RT-DETR 配置
│   ├── train_yolov8.py             # YOLOv8 训练/验证
│   ├── compare_yolov8_rtdetr.py    # 训练曲线对比绘图
│   ├── compare.py                  # 最终指标汇总 + 柱状图
│   ├── generate_comparison_report.py  # 自动生成对比报告
│   ├── setup_dinov3.py             # 下载 DINOv3 教师权重
│   └── plot_tensorboard.py         # TensorBoard 日志可视化
├── docs/
│   ├── rtdetrv4_losses.md          # 损失函数详解
│   ├── comparison_report_yolov8s_vs_rtdetrv4_l.md  # 最终对比报告
│   └── assets/tensorboard/         # 训练曲线图
├── RT-DETRv4/                      # 官方代码（已 clone）
│   ├── configs/custom/             # 自动生成的训练配置
│   └── figures/rtv4_ap_latency.png
├── deploy/model_compare_service/   # 推理对比服务
└── inference_rtdetr_val_samples.py # 验证集抽样可视化
```

一键复现实验流程：

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

- **需要高定位精度**（高 IoU 阈值下的 mAP 重要，如自动驾驶、医学影像）
- **厌恶 NMS 调参**（DETR 端到端，无 score 阈值与 IoU 阈值的耦合）
- **小数据集 + 教师模型可用**（DINOv3 蒸馏在小数据上加速收敛明显）
- **训练资源充裕**（DETR 训练比 YOLO 重，但本次实验反而 epoch 更少）

### 适合选 YOLOv8 的场景

- **极度重视推理速度**（边缘设备、移动端）
- **小目标检测为主**（query 数量限制让 RT-DETR 在小目标上略弱）
- **生态成熟度**（部署链路、量化工具、社区案例 YOLO 更完善）

### 实战启示

这次实验最让我意外的是 **57 epoch vs 399 epoch** 的对比。传统印象里 DETR 训练慢、收敛慢，但 RT-DETRv4 + DINOv3 蒸馏把这个偏见打破了——**收敛 epoch 数减少 86%，mAP@0.5 反而提升 3.58%**。

如果你还在用 YOLOv8 做小数据集检测，强烈建议跑一次 RT-DETRv4 的对照实验，可能有意外的收获。
