"""
MemoryTool - 记忆工具
通过 BaseTool 的 run() 接口提供统一的记忆操作。
支持 actions: add, search, summary, stats, update, remove, forget, consolidate, clear_all
"""
from typing import Dict, Any, Optional, List
from ..base import BaseTool
from ...memory.config import MemoryConfig
from ...memory.item import MemoryItem
from ...memory.manager import MemoryManager


class MemoryTool(BaseTool):
    """记忆工具：统一的记忆操作接口"""

    def __init__(
        self,
        user_id: str = "default_user",
        memory_types: Optional[List[str]] = None,
        memory_config: Optional[MemoryConfig] = None,
    ):
        self.user_id = user_id
        self.memory_types = memory_types or ["working", "episodic", "semantic", "perceptual"]
        self.memory_config = memory_config or MemoryConfig()
        self.memory_manager = MemoryManager(user_id, self.memory_config)

    @property
    def name(self) -> str:
        return "memory"

    @property
    def description(self) -> str:
        return "记忆管理工具，支持记忆的添加、搜索、整合、遗忘等操作"

    def run(self, params) -> str:
        """
        统一的执行接口。

        params 可以是:
        - dict: {"action": "add", "content": "...", ...}
        - str: 快捷操作，如 "stats"
        """
        if isinstance(params, str):
            params = {"action": params}

        action = params.get("action", "stats")
        return self._dispatch(action, params)

    def _dispatch(self, action: str, params: Dict[str, Any]) -> str:
        """分派到具体的操作方法"""
        handler = {
            "add": self._action_add,
            "search": self._action_search,
            "summary": self._action_summary,
            "stats": self._action_stats,
            "update": self._action_update,
            "remove": self._action_remove,
            "forget": self._action_forget,
            "consolidate": self._action_consolidate,
            "clear_all": self._action_clear_all,
        }.get(action)

        if not handler:
            return f"错误：不支持的操作 '{action}'。支持: {', '.join(self._dispatch.__dict__)}"

        try:
            return handler(params)
        except Exception as e:
            return f"错误：{e}"

    def _action_add(self, params: Dict[str, Any]) -> str:
        """添加记忆"""
        content = params.get("content", "")
        memory_type = params.get("memory_type", "working")
        importance = float(params.get("importance", 0.5))

        # 提取 metadata（排除已知字段）
        known_keys = {"action", "content", "memory_type", "importance", "query", "limit",
                      "min_importance", "strategy", "threshold", "from_type", "to_type",
                      "importance_threshold", "memory_id"}
        metadata = {k: v for k, v in params.items() if k not in known_keys}

        item = self.memory_manager.add_memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            metadata=metadata,
        )
        return f"✅ 已添加 [{memory_type}] 记忆 (id={item.memory_id}, importance={importance})"

    def _action_search(self, params: Dict[str, Any]) -> str:
        """搜索记忆"""
        query = params.get("query", "")
        memory_type = params.get("memory_type")
        min_importance = float(params.get("min_importance", 0.0))
        limit = int(params.get("limit", 5))

        results = self.memory_manager.search(
            query=query,
            memory_type=memory_type,
            min_importance=min_importance,
            limit=limit,
        )

        if not results:
            return "未找到匹配的记忆。"

        lines = []
        for i, item in enumerate(results, 1):
            meta_str = ""
            if item.metadata:
                meta_str = f" | meta: {item.metadata}"
            lines.append(
                f"{i}. [{item.memory_type}] (importance={item.importance:.2f}) "
                f"{item.content[:100]}{meta_str}"
            )
        return "\n".join(lines)

    def _action_summary(self, params: Dict[str, Any]) -> str:
        """记忆摘要"""
        limit = int(params.get("limit", 5))
        memory_type = params.get("memory_type")

        results = self.memory_manager.search(query="", memory_type=memory_type, limit=limit)

        if not results:
            return "暂无记忆。"

        lines = ["📋 记忆摘要:"]
        for i, item in enumerate(results, 1):
            lines.append(f"  {i}. [{item.memory_type}] {item.content[:80]}")
        return "\n".join(lines)

    def _action_stats(self, params: Dict[str, Any]) -> str:
        """统计信息"""
        stats = self.memory_manager.get_stats()
        lines = [f"📊 记忆统计 (用户: {self.user_id}):"]
        for mt, info in stats.items():
            if mt == "total":
                lines.append(f"  总计: {info} 条记忆")
            else:
                lines.append(
                    f"  {mt}: {info['count']} 条 (平均重要性: {info['avg_importance']:.2f})"
                )
        return "\n".join(lines)

    def _action_update(self, params: Dict[str, Any]) -> str:
        """更新记忆"""
        memory_id = params.get("memory_id")
        if not memory_id:
            return "错误：需要指定 memory_id"

        for mt, items in self.memory_manager.memories.items():
            if memory_id in items:
                item = items[memory_id]
                if "content" in params:
                    item.content = params["content"]
                if "importance" in params:
                    item.importance = float(params["importance"])
                item.updated_at = __import__("datetime").datetime.now()
                return f"✅ 已更新记忆 {memory_id}"

        return f"错误：未找到记忆 {memory_id}"

    def _action_remove(self, params: Dict[str, Any]) -> str:
        """删除记忆"""
        memory_id = params.get("memory_id")
        if not memory_id:
            return "错误：需要指定 memory_id"

        for mt, items in self.memory_manager.memories.items():
            if memory_id in items:
                del items[memory_id]
                return f"✅ 已删除记忆 {memory_id}"

        return f"错误：未找到记忆 {memory_id}"

    def _action_forget(self, params: Dict[str, Any]) -> str:
        """遗忘/清理记忆"""
        strategy = params.get("strategy", "importance_based")
        threshold = float(params.get("threshold", 0.3))
        memory_type = params.get("memory_type")

        deleted = self.memory_manager.forget(
            strategy=strategy,
            threshold=threshold,
            memory_type=memory_type,
        )
        return f"🧹 已遗忘 {deleted} 条记忆 (策略: {strategy}, 阈值: {threshold})"

    def _action_consolidate(self, params: Dict[str, Any]) -> str:
        """记忆整合"""
        from_type = params.get("from_type", "working")
        to_type = params.get("to_type", "episodic")
        threshold = float(params.get("importance_threshold", 0.6))

        count = self.memory_manager.consolidate(
            from_type=from_type,
            to_type=to_type,
            importance_threshold=threshold,
        )
        return f"🔄 已整合 {count} 条记忆 ({from_type} → {to_type}, 阈值: {threshold})"

    def _action_clear_all(self, params: Dict[str, Any]) -> str:
        """清空所有记忆"""
        self.memory_manager.clear()
        return "✅ 已清空所有记忆"
