from typing import Optional, List, Dict, Callable, Any
from .base import BaseTool


class ToolRegistry:

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, tool: BaseTool) -> None:
        if not hasattr(tool, "name") or not hasattr(tool, "description") or not hasattr(tool, "run"):
            raise TypeError("工具必须实现 name, description 和 run 接口")
        self._tools[tool.name] = {
            "description": tool.description,
            "func": tool.run,
            "tool": tool,
        }

    def register_function(self, name: str, *args, **kwargs) -> None:
        if len(args) == 2 and callable(args[1]) and not kwargs:
            description, func = args[0], args[1]
        elif len(args) == 2 and callable(args[0]) and not kwargs:
            func, description = args[0], args[1]
        elif "func" in kwargs and "description" in kwargs:
            name = name
            description = kwargs["description"]
            func = kwargs["func"]
        elif len(args) == 1 and callable(args[0]):
            func = args[0]
            description = kwargs.get("description", "")
        else:
            raise ValueError("register_function 参数格式不正确，支持: (name, desc, func) 或 (name, desc=..., func=...)")

        self._tools[name] = {
            "description": description,
            "func": func,
        }

    def unregister(self, name: str) -> bool:
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get_tool(self, name: str):
        info = self._tools.get(name)
        if info:
            return info.get("tool", info.get("func"))
        return None

    def execute_tool(self, name: str, tool_input: str) -> str:
        info = self._tools.get(name)
        if not info:
            return f"错误：未找到工具 '{name}'"
        func = info["func"]
        try:
            if isinstance(tool_input, dict):
                return func(tool_input)
            return func(tool_input)
        except Exception as e:
            return f"工具 '{name}' 执行失败: {e}"

    def get_tools_description(self) -> str:
        if not self._tools:
            return "暂无可用工具"
        return "\n".join(
            f"- {name}: {info['description']}"
            for name, info in self._tools.items()
        )

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())
