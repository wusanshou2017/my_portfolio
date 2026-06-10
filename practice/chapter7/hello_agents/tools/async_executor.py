"""
异步工具执行器
支持并发执行多个工具，提升工具调用的效率。
"""
import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from .registry import ToolRegistry


class AsyncToolExecutor:
    """
    异步工具执行器：支持并发执行多个工具调用。

    在实际场景中，Agent 可能需要同时调用多个独立的工具（如同时搜索和计算），
    串行执行会浪费时间。本执行器使用线程池实现并发调用。
    """

    def __init__(self, max_workers: int = 5):
        """
        Args:
            max_workers: 最大并发工作线程数
        """
        self.max_workers = max_workers

    def execute_parallel(
        self,
        registry: ToolRegistry,
        calls: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        并发执行多个工具调用。

        Args:
            registry: 工具注册表
            calls: 工具调用列表，每个元素为 {"tool_name": str, "input": str}

        Returns:
            执行结果列表，每个元素为 {"tool_name": str, "result": str, "success": bool}
        """
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务到线程池
            future_to_call = {}
            for call in calls:
                future = executor.submit(
                    registry.execute_tool,
                    call["tool_name"],
                    call["input"],
                )
                future_to_call[future] = call

            # 收集结果
            for future in as_completed(future_to_call):
                call = future_to_call[future]
                try:
                    result = future.result()
                    results.append({
                        "tool_name": call["tool_name"],
                        "result": result,
                        "success": True,
                    })
                except Exception as e:
                    results.append({
                        "tool_name": call["tool_name"],
                        "result": f"执行失败: {e}",
                        "success": False,
                    })

        return results

    def execute_sequential(
        self,
        registry: ToolRegistry,
        calls: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        顺序执行多个工具调用（与并行对比用）。

        Args:
            registry: 工具注册表
            calls: 工具调用列表

        Returns:
            执行结果列表
        """
        results = []
        for call in calls:
            try:
                result = registry.execute_tool(call["tool_name"], call["input"])
                results.append({
                    "tool_name": call["tool_name"],
                    "result": result,
                    "success": True,
                })
            except Exception as e:
                results.append({
                    "tool_name": call["tool_name"],
                    "result": f"执行失败: {e}",
                    "success": False,
                })
        return results
