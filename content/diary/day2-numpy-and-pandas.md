---
title: 学习日记第2天：NumPy 和 Pandas 入门
date: 2026-04-29
tags: [AI, Python, NumPy]
description: 学习了 NumPy 的数组操作和 Pandas 的数据处理基础，感觉 Python 做数据分析真的很方便。
---

## NumPy 学习

今天深入学习了 NumPy，发现它和 JavaScript 的数组操作思路很不一样：

```python
import numpy as np

arr = np.array([1, 2, 3, 4, 5])
print(arr.mean())  # 3.0
print(arr[arr > 2])  # [3, 4, 5]
```

## Pandas 数据处理

Pandas 的 DataFrame 操作非常直观，处理表格数据特别方便。加载 CSV、筛选、分组聚合，几行代码就搞定。

## 遇到的问题

- NumPy 的广播机制理解起来有点绕
- Pandas 的 `apply` 和 `map` 的区别需要记一下

## 明天的计划

- 学习 Matplotlib 数据可视化
- 用真实数据集做一个分析练习
