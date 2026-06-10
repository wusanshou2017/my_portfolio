"""
HelloAgents 异常体系
统一管理框架内所有异常，便于上层捕获和处理。
"""


class HelloAgentsError(Exception):
    """HelloAgents 框架基础异常"""
    pass


class LLMError(HelloAgentsError):
    """LLM 调用相关异常"""

    def __init__(self, message: str = "LLM 调用失败", provider: str = None, model: str = None):
        self.provider = provider
        self.model = model
        if provider and model:
            message = f"[{provider}/{model}] {message}"
        elif provider:
            message = f"[{provider}] {message}"
        super().__init__(message)


class LLMConnectionError(LLMError):
    """LLM 连接异常"""
    pass


class LLMResponseError(LLMError):
    """LLM 响应解析异常"""
    pass


class LLMTimeoutError(LLMError):
    """LLM 调用超时异常"""
    pass


class ToolError(HelloAgentsError):
    """工具相关异常"""

    def __init__(self, message: str = "工具执行失败", tool_name: str = None):
        self.tool_name = tool_name
        if tool_name:
            message = f"[{tool_name}] {message}"
        super().__init__(message)


class ToolNotFoundError(ToolError):
    """工具未找到异常"""
    pass


class ToolRegistrationError(ToolError):
    """工具注册异常"""
    pass


class ToolExecutionError(ToolError):
    """工具执行异常"""
    pass


class AgentError(HelloAgentsError):
    """Agent 相关异常"""

    def __init__(self, message: str = "Agent 运行失败", agent_name: str = None):
        self.agent_name = agent_name
        if agent_name:
            message = f"[{agent_name}] {message}"
        super().__init__(message)


class AgentMaxStepsError(AgentError):
    """Agent 超过最大步数异常"""
    pass


class AgentConfigError(HelloAgentsError):
    """Agent 配置异常"""
    pass
