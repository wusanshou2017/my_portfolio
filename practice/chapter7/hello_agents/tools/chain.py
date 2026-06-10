"""
工具链管理系统
支持将多个工具串联成链，按顺序或并行执行。
"""
from typing import List, Dict, Any, Optional, Callable
from .registry import ToolRegistry


class ToolChain:
    """
    工具链：将多个工具按顺序串联执行，前一个工具的输出可以作为后一个工具的输入。
    """

    def __init__(self, name: str = "default_chain"):
        self.name = name
        self._steps: List[Dict[str, Any]] = []

    def add_step(self, tool_name: str, input_mapping: Optional[Dict[str, str]] = None) -> 'ToolChain':
        """
        添加一个执行步骤到工具链。

        Args:
            tool_name: 工具名称
            input_mapping: 输入映射，指定如何将上一步的输出映射到当前工具的参数。
                          例如 {"expression": "result"} 表示将上一步输出中的 result 字段
                          作为当前工具的 expression 参数。
        """
        self._steps.append({
            "tool_name": tool_name,
            "input_mapping": input_mapping or {},
        })
        return self

    def execute(self, registry: ToolRegistry, initial_input: str) -> List[str]:
        """
        按顺序执行工具链中的所有步骤。

        Args:
            registry: 工具注册表
            initial_input: 初始输入（传给第一个工具）

        Returns:
            每一步的输出结果列表
        """
        results = []
        current_input = initial_input

        for i, step in enumerate(self._steps):
            tool_name = step["tool_name"]
            result = registry.execute_tool(tool_name, current_input)
            results.append(result)
            # 下一步的输入就是当前步骤的输出
            current_input = result

        return results

    @property
    def steps(self) -> List[str]:
        """返回工具链中的工具名列表"""
        return [step["tool_name"] for step in self._steps]

    @property
    def length(self) -> int:
        return len(self._steps)

    def __len__(self) -> int:
        return self.length

    def __repr__(self) -> str:
        chain = " -> ".join(self.steps) if self.steps else "(empty)"
        return f"ToolChain(name={self.name!r}, steps=[{chain}])"
