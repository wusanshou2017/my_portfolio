"""
记忆管理器
统一管理四种类型的记忆：working / episodic / semantic / perceptual
提供添加、搜索、删除、整合、遗忘等操作。
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from .config import MemoryConfig
from .item import MemoryItem


class MemoryManager:
    """
    记忆管理器：组合模式，内部按类型分组管理记忆。
    """

    SUPPORTED_TYPES = {"working", "episodic", "semantic", "perceptual"}

    def __init__(self, user_id: str, config: Optional[MemoryConfig] = None):
        self.user_id = user_id
        self.config = config or MemoryConfig()
        # 各类型的记忆存储，key 为 memory_id
        self.memories: Dict[str, Dict[str, MemoryItem]] = {
            t: {} for t in self.SUPPORTED_TYPES
        }
        # 用户选择的记忆类型（只管理这些）
        self.memory_types: Dict[str, 'MemoryTypeStore'] = {}

    def add_memory(
        self,
        content: str,
        memory_type: str,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem:
        """添加一条记忆"""
        if memory_type not in self.SUPPORTED_TYPES:
            raise ValueError(f"不支持的记忆类型: {memory_type}")

        item = MemoryItem(
            content=content,
            memory_type=memory_type,
            importance=importance,
            user_id=self.user_id,
            metadata=metadata or {},
        )
        self.memories[memory_type][item.memory_id] = item

        # 工作记忆容量管理：超出容量时淘汰低重要性记忆
        if memory_type == "working":
            self._enforce_capacity(memory_type, self.config.working_memory_capacity)

        return item

    def search(
        self,
        query: str = "",
        memory_type: Optional[str] = None,
        min_importance: float = 0.0,
        limit: int = 5,
    ) -> List[MemoryItem]:
        """
        搜索记忆。
        使用简单的关键词匹配 + 重要性/时间衰减排序。
        """
        results: List[MemoryItem] = []
        types_to_search = [memory_type] if memory_type else list(self.SUPPORTED_TYPES)

        for mt in types_to_search:
            for item in self.memories.get(mt, {}).values():
                # 重要性过滤
                if item.importance < min_importance:
                    continue
                # 关键词匹配（空 query 返回全部）
                if query:
                    query_lower = query.lower()
                    if query_lower not in item.content.lower():
                        # 同时检查 metadata 的字符串值
                        meta_match = any(
                            query_lower in str(v).lower()
                            for v in item.metadata.values()
                        )
                        if not meta_match:
                            continue

                # 计算综合得分（重要性 + 时间衰减）
                score = self._compute_score(item)
                results.append((score, item))

        # 按得分降序排列
        results.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in results[:limit]]

    def forget(
        self,
        strategy: str = "importance_based",
        threshold: float = 0.3,
        memory_type: Optional[str] = None,
    ) -> int:
        """遗忘/清理记忆，返回删除数量"""
        types = [memory_type] if memory_type else list(self.SUPPORTED_TYPES)
        deleted = 0

        for mt in types:
            to_delete = []
            for mid, item in self.memories.get(mt, {}).items():
                if strategy == "importance_based":
                    if item.importance <= threshold:
                        to_delete.append(mid)
                elif strategy == "ttl":
                    ttl_minutes = {
                        "working": self.config.working_memory_ttl_minutes,
                    }.get(mt, 1440)
                    if datetime.now() - item.created_at > timedelta(minutes=ttl_minutes):
                        to_delete.append(mid)

            for mid in to_delete:
                del self.memories[mt][mid]
                deleted += 1

        return deleted

    def consolidate(
        self,
        from_type: str,
        to_type: str,
        importance_threshold: float = 0.6,
    ) -> int:
        """
        记忆整合：将 from_type 中达到阈值的记忆复制到 to_type。
        返回整合数量。
        """
        if from_type not in self.SUPPORTED_TYPES or to_type not in self.SUPPORTED_TYPES:
            raise ValueError(f"不支持的记忆类型")

        consolidated = 0
        for mid, item in list(self.memories.get(from_type, {}).items()):
            if item.importance >= importance_threshold:
                # 创建新记忆（整合后提升重要性）
                new_item = self.add_memory(
                    content=item.content,
                    memory_type=to_type,
                    importance=min(item.importance * 1.1, 1.0),
                    metadata={
                        **item.metadata,
                        "consolidated_from": from_type,
                        "consolidated_at": datetime.now().isoformat(),
                        "original_id": item.memory_id,
                    },
                )
                consolidated += 1

        return consolidated

    def get_stats(self) -> Dict[str, Any]:
        """返回各类型记忆的统计"""
        stats = {}
        for mt in self.SUPPORTED_TYPES:
            items = list(self.memories.get(mt, {}).values())
            stats[mt] = {
                "count": len(items),
                "avg_importance": (
                    sum(i.importance for i in items) / len(items) if items else 0
                ),
            }
        total = sum(s["count"] for s in stats.values())
        stats["total"] = total
        return stats

    def clear(self, memory_type: Optional[str] = None):
        """清空记忆"""
        if memory_type:
            self.memories[memory_type].clear()
        else:
            for mt in self.SUPPORTED_TYPES:
                self.memories[mt].clear()

    def _enforce_capacity(self, memory_type: str, capacity: int):
        """超出容量时淘汰低重要性记忆"""
        items = list(self.memories[memory_type].values())
        if len(items) <= capacity:
            return
        # 按重要性排序，淘汰低重要性
        items.sort(key=lambda x: (x.importance, x.created_at))
        for item in items[:-capacity]:
            del self.memories[memory_type][item.memory_id]

    def _compute_score(self, item: MemoryItem) -> float:
        """计算记忆的综合得分"""
        # 时间衰减：距离现在越远得分越低
        age_hours = (datetime.now() - item.created_at).total_seconds() / 3600
        time_factor = 1.0 / (1.0 + self.config.time_decay_factor * age_hours)
        return item.importance * time_factor
