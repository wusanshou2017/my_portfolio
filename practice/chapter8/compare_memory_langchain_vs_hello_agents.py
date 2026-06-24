#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory 机制对比验证：hello-agents MemoryManager vs LangGraph Store
在同一脚本中分别演示两套记忆系统的核心操作。
"""

import sys
import os
import time

# ============================================================
# Part 1: hello-agents 记忆系统
# ============================================================

def demo_hello_agents_memory():
    """演示 hello-agents 的四类记忆系统"""
    print("=" * 70)
    print("Part 1: hello-agents MemoryManager")
    print("=" * 70)

    # 确保能导入本地 hello_agents
    chapter7_path = os.path.join(os.path.dirname(__file__), "..", "chapter7")
    sys.path.insert(0, os.path.abspath(chapter7_path))

    from hello_agents.tools.builtin.memory import MemoryTool

    # 1. 初始化
    memory = MemoryTool(
        user_id="compare_user",
        memory_types=["working", "episodic", "semantic", "perceptual"]
    )
    print("\n[初始化] MemoryTool 创建完成，支持四类记忆\n")

    # 2. 添加记忆 — 四种类型
    print("--- 添加记忆 ---")
    print(memory.run({
        "action": "add", "content": "用户叫张三", "memory_type": "working", "importance": 0.8
    }))
    print(memory.run({
        "action": "add", "content": "用户正在学习记忆系统对比", "memory_type": "working", "importance": 0.7
    }))
    print(memory.run({
        "action": "add", "content": "2026年开始学习 AI Agent", "memory_type": "episodic", "importance": 0.9,
        "event_type": "milestone"
    }))
    print(memory.run({
        "action": "add", "content": "Python是最流行的AI编程语言", "memory_type": "semantic", "importance": 0.9,
        "concept": "python", "domain": "programming"
    }))
    print(memory.run({
        "action": "add", "content": "看了记忆系统的架构图", "memory_type": "perceptual", "importance": 0.4,
        "modality": "image"
    }))

    # 3. 搜索记忆 — 关键词匹配 + 重要性排序
    print("\n--- 搜索记忆: '用户' ---")
    print(memory.run({"action": "search", "query": "用户", "limit": 3}))

    print("\n--- 搜索记忆: 'Python' (min_importance=0.8) ---")
    print(memory.run({"action": "search", "query": "Python", "min_importance": 0.8, "limit": 3}))

    # 4. 统计
    print("\n--- 记忆统计 ---")
    print(memory.run({"action": "stats"}))

    # 5. 遗忘 — 基于重要性
    print("\n--- 遗忘 (threshold=0.5) ---")
    print(memory.run({"action": "forget", "strategy": "importance_based", "threshold": 0.5}))

    print("\n--- 遗忘后统计 ---")
    print(memory.run({"action": "stats"}))

    # 6. 记忆整合 — working → episodic
    print("\n--- 记忆整合 (working → episodic, threshold=0.6) ---")
    print(memory.run({
        "action": "consolidate", "from_type": "working", "to_type": "episodic",
        "importance_threshold": 0.6
    }))

    print("\n--- 整合后统计 ---")
    print(memory.run({"action": "stats"}))

    print("\n" + "=" * 70)
    print("hello-agents 特点: 四类记忆 | 主动遗忘 | 记忆整合 | 认知科学模型")
    print("=" * 70)

    return memory


# ============================================================
# Part 2: LangGraph Store 记忆系统
# ============================================================

def demo_langgraph_store():
    """演示 LangGraph 的 Store + Checkpointer 两层记忆"""
    print("\n")
    print("=" * 70)
    print("Part 2: LangGraph Store + Checkpointer (LangChain 1.x)")
    print("=" * 70)

    from langgraph.store.memory import InMemoryStore
    from langgraph.checkpoint.memory import MemorySaver

    # 1. 初始化 Store（长期记忆）+ Checkpointer（短期状态）
    store = InMemoryStore()
    checkpointer = MemorySaver()

    print("\n[初始化] InMemoryStore + MemorySaver 创建完成\n")

    # 2. 存储记忆 — 任意 JSON 结构，按 namespace 分区
    print("--- 存储记忆 (Store.put) ---")
    store.put(
        namespace=("user_123", "profile"),
        key="name",
        value={"text": "用户叫张三", "importance": 0.8}
    )
    print("  ✓ 存入 ('user_123', 'profile') / 'name' = 用户叫张三")

    store.put(
        namespace=("user_123", "learning"),
        key="current_topic",
        value={"text": "正在学习记忆系统对比", "importance": 0.7}
    )
    print("  ✓ 存入 ('user_123', 'learning') / 'current_topic'")

    store.put(
        namespace=("user_123", "milestones"),
        key="2026_start",
        value={"text": "2026年开始学习 AI Agent", "importance": 0.9}
    )
    print("  ✓ 存入 ('user_123', 'milestones') / '2026_start'")

    store.put(
        namespace=("user_123", "knowledge"),
        key="python",
        value={"text": "Python是最流行的AI编程语言", "importance": 0.9}
    )
    print("  ✓ 存入 ('user_123', 'knowledge') / 'python'")

    # 3. 读取记忆
    print("\n--- 读取记忆 (Store.get) ---")
    item = store.get(("user_123", "profile"), "name")
    print(f"  ('user_123', 'profile') / 'name' → {item.value}")

    # 4. 搜索记忆 — 按 namespace 搜索
    print("\n--- 搜索记忆 (Store.search by namespace) ---")
    items = store.search(("user_123", "knowledge"))
    for item in items:
        print(f"  [{item.key}] {item.value['text']}")

    # 5. 列出所有 namespace 的记忆
    print("\n--- 全部记忆 (Store.search all namespaces) ---")
    for ns in ["profile", "learning", "milestones", "knowledge"]:
        items = store.search(("user_123", ns))
        for item in items:
            print(f"  ({ns}) [{item.key}] {item.value['text']}")

    # 6. 删除记忆 — 手动管理，无自动遗忘
    print("\n--- 删除记忆 (Store.delete) ---")
    store.delete(("user_123", "learning"), "current_topic")
    print("  ✓ 删除 ('user_123', 'learning') / 'current_topic'")
    remaining = store.search(("user_123", "learning"))
    print(f"  删除后 learning 命名空间剩余: {len(remaining)} 条")

    # 7. 带向量索引的 Store（如果可用）
    print("\n--- 尝试带向量索引的 Store ---")
    try:
        from langchain_openai import OpenAIEmbeddings
        # 创建带嵌入索引的 Store
        vector_store = InMemoryStore(
            index={
                "embed": OpenAIEmbeddings(),
                "fields": ["text"],
            }
        )
        vector_store.put(
            namespace=("user_123", "memories"),
            key="m1",
            value={"text": "用户精通 Python 和 LangChain", "importance": 0.9}
        )
        vector_store.put(
            namespace=("user_123", "memories"),
            key="m2",
            value={"text": "用户住在上海", "importance": 0.6}
        )
        # 语义搜索
        results = vector_store.search(
            namespace=("user_123", "memories"),
            query="编程技能",
            limit=2
        )
        print("  语义搜索 '编程技能' 结果:")
        for r in results:
            print(f"    [{r.key}] score={r.score:.4f} {r.value['text']}")
        print("  ✓ 向量索引 Store 工作正常")
    except Exception as e:
        print(f"  ⚠ 向量索引 Store 不可用: {e}")
        print("  （需要配置 OpenAI API Key 或本地嵌入模型）")

    # 8. Checkpointer — 短期状态快照
    print("\n--- Checkpointer 状态快照 ---")
    print("  Checkpointer 用于保存 Agent 执行状态，支持断点恢复")
    print("  （需要配合 LangGraph 编译使用，这里只展示概念）")

    print("\n" + "=" * 70)
    print("LangGraph 特点: 两层架构 | namespace 分区 | 向量检索 | 无自动遗忘")
    print("=" * 70)

    return store


# ============================================================
# Part 3: 核心差异对比表
# ============================================================

def print_comparison_table():
    """打印对比表"""
    print("\n")
    print("=" * 70)
    print("Part 3: 核心差异对比")
    print("=" * 70)

    comparisons = [
        ("设计理念",          "认知科学模型（4种记忆类型）",        "工程实用（短期快照+长期存储）"),
        ("记忆分类",          "working/episodic/semantic/perceptual", "Checkpointer(短期) + Store(长期)"),
        ("数据模型",          "MemoryItem (固定字段+importance)",   "任意 JSON (按 namespace 组织)"),
        ("检索方式",          "关键词匹配 (我们的) / 向量+图 (源码)",  "向量语义检索 (Store index)"),
        ("遗忘机制",          "importance_based / time_based",      "无内置遗忘，手动 delete"),
        ("记忆整合",          "working→episodic (importance×1.1)",  "无对应概念"),
        ("跨会话",            "按 user_id 隔离",                     "namespace 天然跨会话"),
        ("持久化",            "内存 (我们的) / Qdrant+Neo4j (源码)",  "InMemory / SQLite / Postgres"),
        ("重要性评分",        "内置 importance 字段 (0.0~1.0)",      "无内置，用户自定义"),
        ("时间衰减",          "score = importance × time_decay",     "无内置"),
        ("实体关系",          "源码版有 Neo4j 图检索",               "无"),
        ("Agent 集成",        "作为 Tool，Agent 主动调用",            "Checkpointer 自动 + Store 手动"),
        ("外部依赖",          "零依赖 (我们的) / 重依赖 (源码)",      "langchain + langgraph"),
    ]

    print(f"\n{'维度':<20} {'hello-agents':<35} {'LangChain 1.x':<35}")
    print("-" * 90)
    for dim, ha, lc in comparisons:
        print(f"{dim:<20} {ha:<35} {lc:<35}")


# ============================================================
# Main
# ============================================================

def main():
    print("🧠 Memory 机制对比验证")
    print("hello-agents MemoryManager vs LangGraph Store")
    print("=" * 70)

    try:
        # Part 1: hello-agents
        demo_hello_agents_memory()
    except Exception as e:
        print(f"\n❌ hello-agents 演示失败: {e}")
        import traceback
        traceback.print_exc()

    try:
        # Part 2: LangGraph Store
        demo_langgraph_store()
    except Exception as e:
        print(f"\n❌ LangGraph Store 演示失败: {e}")
        import traceback
        traceback.print_exc()

    # Part 3: 对比表
    print_comparison_table()

    print("\n\n✅ 对比验证完成！")


if __name__ == "__main__":
    main()
