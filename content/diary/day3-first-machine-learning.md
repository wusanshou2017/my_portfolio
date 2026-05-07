---
title: 学习日记第3天：第一个机器学习模型
date: 2026-04-30
tags: [AI, 机器学习, Scikit-learn]
description: 用 Scikit-learn 训练了第一个机器学习模型，一个简单的线性回归，成就感满满！
---

## 第一个 ML 模型

今天用 Scikit-learn 训练了一个线性回归模型，预测房价：

```python
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model = LinearRegression()
model.fit(X_train, y_train)
score = model.score(X_test, y_test)
print(f"模型准确率: {score:.2f}")
```

## 心得

虽然只是最基础的模型，但看到代码跑出结果的那一刻真的很兴奋！从数据预处理到模型训练再到评估，完整走了一遍 ML 流程。

## 明天的计划

- 学习逻辑回归和分类问题
- 了解模型评估指标（准确率、精确率、召回率）
- 试着用 Kaggle 上的数据集练手
