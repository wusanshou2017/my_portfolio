"""
记忆配置模块
定义记忆系统的各项配置参数。
"""
from dataclasses import dataclass, field


@dataclass
class MemoryConfig:
    """记忆系统全局配置"""

    # 工作记忆配置
    working_memory_capacity: int = 50
    working_memory_ttl_minutes: int = 60

    # 情景记忆配置
    episodic_memory_capacity: int = 200

    # 语义记忆配置
    semantic_memory_capacity: int = 200

    # 感知记忆配置
    perceptual_memory_capacity: int = 100

    # 重要性衰减因子（越大衰减越快）
    importance_decay_factor: float = 0.1

    # 时间衰减因子
    time_decay_factor: float = 0.05
