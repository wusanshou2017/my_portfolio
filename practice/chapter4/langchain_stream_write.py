
import os
from typing import Any, Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, AIMessageChunk, AnyMessage, ToolMessage
from langchain_core.runnables import Runnable
from langgraph.config import get_stream_writer
from pydantic import BaseModel

load_dotenv()

# ============================================================
# 0. 基础配置 - 从环境变量加载
# ============================================================
API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL_ID = os.getenv("LLM_MODEL_ID")

if not all([API_KEY, BASE_URL, MODEL_ID]):
    raise ValueError("请在 .env 文件中设置 LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_ID")


# ============================================================
# 1. 定义工具函数
# ============================================================
@tool
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    writer = get_stream_writer()
    writer(f"查找城市天气: {city}")
    writer(f"获取城市天气: {city}")
    return f"It's always sunny in {city}!"


@tool
def get_population(city: str) -> str:
    """Get population for a given city."""
    writer = get_stream_writer()
    writer(f"查找人口规模: {city}")
    return f"{city} 有100万人左右."


# ============================================================
# 2. 创建 Agent (兼容 OpenAI 接口)
# ============================================================
def create_my_agent():
    llm = ChatOpenAI(
        model=MODEL_ID,
        api_key=API_KEY,
        base_url=BASE_URL,
        temperature=0,
    )
    agent = create_agent(
        model=llm,
        tools=[get_weather, get_population],
    )
    return agent

agent = create_my_agent()

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "SF的人口有多少，What is SF的天气?"}]},
    stream_mode=["updates", "custom"],
    version="v2",
):
    # v2: {"type": ..., "data": ...}
    # v1: (mode, data) tuple
    if isinstance(chunk, dict):
        print(f"stream_mode: {chunk['type']}")
        print(f"content: {chunk['data']}")
    else:
        mode, data = chunk
        print(f"stream_mode: {mode}")
        print(f"content: {data}")
    print("\n")