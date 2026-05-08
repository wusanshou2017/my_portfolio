# LangChain Streaming 完整知识点总结

> 来源: `f:\workspace\my_portfolio\practice\langchain_streaming`（官方教程）
> 对应的脚本: `practice/chapter4/langchain_streaming_demo.py`

---

## 一、为什么需要 Streaming

LLM 生成完整响应需要数秒到十几秒，远超用户可感知的 ~200ms 阈值。Streaming 通过逐步显示输出来提升用户体验。

**核心收益：**
- 用户立即看到进展，减少等待焦虑
- 感知性能提升（总时间不变，但体感更快）
- Agent 场景下可以展示中间步骤和工具调用过程

---

## 二、三种核心 Stream Mode

| Mode | 含义 | 产生时机 | chunk 是什么 |
|---|---|---|---|
| `updates` | Agent 每步状态更新 | **每步执行完后** | 该步骤完整的 `AIMessage` / `ToolMessage` |
| `messages` | LLM token 流 | **LLM 生成过程中** | `(AIMessageChunk, metadata)` 元组 |
| `custom` | 自定义更新 | **工具执行过程中** | 任意 Python 对象（`writer()` 推送的内容） |

### 1. Agent Progress (`stream_mode="updates"`)

```python
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
    stream_mode="updates",
    version="v2",
):
    if chunk["type"] == "updates":
        for step, data in chunk["data"].items():
            print(f"step: {step}")
            print(f"content: {data['messages'][-1].content_blocks}")
```

典型流程（tool calling 场景）：
```
step: model    → AIMessage（包含 tool_call 请求）
step: tools    → ToolMessage（工具执行结果）
step: model    → AIMessage（最终回复）
```

### 2. LLM Tokens (`stream_mode="messages"`)

```python
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
    stream_mode="messages",
    version="v2",
):
    if chunk["type"] == "messages":
        token, metadata = chunk["data"]
        print(f"node: {metadata['langgraph_node']}")
        print(f"content: {token.content_blocks}")
```

可以看到 tool call 参数的**逐片段生成过程**：
```
tool_call_chunk: args = ''
tool_call_chunk: args = '{"'
tool_call_chunk: args = 'city'
tool_call_chunk: args = '":"'
tool_call_chunk: args = 'San'
tool_call_chunk: args = ' Francisco'
tool_call_chunk: args = '"}'
```

### 3. Custom Updates (`stream_mode="custom"`)

工具内部主动推送进度：

```python
from langgraph.config import get_stream_writer

def get_weather(city: str) -> str:
    writer = get_stream_writer()
    writer(f"Looking up data for city: {city}")
    writer(f"Acquired data for city: {city}")
    return f"It's always sunny in {city}!"

# 接收端
for chunk in agent.stream(..., stream_mode="custom", version="v2"):
    if chunk["type"] == "custom":
        print(chunk["data"])
```

**注意：** 工具加了 `get_stream_writer()` 后，不能在 Agent 外部单独调用。

---

## 三、多模式同时使用

```python
for chunk in agent.stream(
    {"messages": [...]},
    stream_mode=["updates", "custom"],  # 传列表
    version="v2",
):
    print(chunk["type"])  # "updates" 或 "custom"
    print(chunk["data"])
```

---

## 四、v2 Streaming Format（所有代码示例都在用）

`version="v2"` 是文档中所有示例的统一写法，推荐使用。

### v1 vs v2 对比

| | v1（旧，默认） | v2（新，推荐） |
|---|---|---|
| chunk 格式 | `(mode, data)` 元组 | `{"type": mode, "data": data}` dict |
| 访问方式 | `for mode, chunk in agent.stream(...)` | `for chunk in agent.stream(...)` |
| 需要 LangGraph | 任意版本 | >= 1.1 |

v2 格式下每个 chunk 都是一个 `StreamPart` dict：

```python
chunk["type"]  # "updates" | "messages" | "custom"
chunk["ns"]    # 命名空间（不常用）
chunk["data"]  # payload
```

---

## 五、Streaming Tool Calls （最常用的组合模式）

同时使用 `messages` + `updates`，拿到两个维度的数据：

```python
from typing import Any
from langchain.messages import AIMessage, AIMessageChunk, AnyMessage, ToolMessage

def _render_message_chunk(token: AIMessageChunk) -> None:
    if token.text:
        print(token.text, end="|")
    if token.tool_call_chunks:
        print(token.tool_call_chunks)

def _render_completed_message(message: AnyMessage) -> None:
    if isinstance(message, AIMessage) and message.tool_calls:
        print(f"Tool calls: {message.tool_calls}")
    if isinstance(message, ToolMessage):
        print(f"Tool response: {message.content_blocks}")

for chunk in agent.stream(
    {"messages": [input_message]},
    stream_mode=["messages", "updates"],
    version="v2",
):
    if chunk["type"] == "messages":
        token, metadata = chunk["data"]
        if isinstance(token, AIMessageChunk):
            _render_message_chunk(token)
    elif chunk["type"] == "updates":
        for source, update in chunk["data"].items():
            if source in ("model", "tools"):
                _render_completed_message(update["messages"][-1])
```

输出流程：
```
[messages] 流式:  tool_call_chunk: args = '{"city": "Boston"}'
[messages] 流式:  tool_call_chunk: args = '{"city": "Boston"}'
...
[updates]  完成:  Tool calls: [{'name': 'get_weather', 'args': {'city': 'Boston'}}]
[updates]  完成:  Tool response: "It's always sunny in Boston!"
[messages] 流式:  The weather in Boston is sunny!
```

---

## 六、Accessing Completed Messages（两种方式）

### 方式 A：通过 `updates` 模式（推荐，当消息在 state 中）

直接在 `updates` 中拿到完成后的消息：
```python
update["messages"][-1]  # 完整的 AIMessage 或 ToolMessage
```

### 方式 B：聚合 chunks（当消息不在 state 中）

```python
full_message = None
for chunk in agent.stream(..., stream_mode=["messages", "updates"], version="v2"):
    if chunk["type"] == "messages":
        token, metadata = chunk["data"]
        if isinstance(token, AIMessageChunk):
            full_message = token if full_message is None else full_message + token
            if token.chunk_position == "last":
                if full_message.tool_calls:
                    print(f"Tool calls: {full_message.tool_calls}")
                full_message = None
```

**关键 API：**
- `full_message + token` — AIMessageChunk 支持加法累积
- `token.chunk_position == "last"` — 判断当前消息是否结束

---

## 七、Streaming Thinking / Reasoning Tokens

过滤 `content_blocks` 中 `type == "reasoning"` 的块：

```python
for token, metadata in agent.stream(..., stream_mode="messages"):
    if not isinstance(token, AIMessageChunk):
        continue
    reasoning = [b for b in token.content_blocks if b["type"] == "reasoning"]
    text = [b for b in token.content_blocks if b["type"] == "text"]
    if reasoning:
        print(f"[thinking] {reasoning[0]['reasoning']}", end="")
    if text:
        print(text[0]["text"], end="")
```

**LangChain 的统一抽象：**
- Anthropic 的 `thinking` blocks → 统一为 `type="reasoning"`
- OpenAI 的 `reasoning` summaries → 统一为 `type="reasoning"`
- 开发者只需过滤 `type == "reasoning"`，不用关心底层模型差异

---

## 八、Streaming with Human-in-the-Loop

工具调用前暂停等待人工审批：

```python
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, Interrupt

checkpointer = InMemorySaver()
agent = create_agent(
    "openai:gpt-5.4",
    tools=[get_weather],
    middleware=[HumanInTheLoopMiddleware(interrupt_on={"get_weather": True})],
    checkpointer=checkpointer,
)

# 第一轮：流式输出 + 收集 __interrupt__ 事件
interrupts = []
for chunk in agent.stream(..., stream_mode=["messages", "updates"], version="v2"):
    if chunk["type"] == "updates":
        for source, update in chunk["data"].items():
            if source == "__interrupt__":
                interrupts.extend(update)
                # 展示需要审批的工具调用
                print(update[0].value["action_requests"][0]["description"])

# 人工决策（approve / edit / deny）
decisions = {interrupt.id: {"decisions": [{"type": "approve"}]}}

# 第二轮：用 Command 恢复执行
for chunk in agent.stream(
    Command(resume=decisions), config=config,
    stream_mode=["messages", "updates"], version="v2",
):
    # 流式循环不变
    ...
```

---

## 九、Streaming from Sub-agents

多 Agent 场景下通过 `lc_agent_name` 区分 token 来源：

```python
# 创建时设置 name
weather_agent = create_agent(model=..., tools=[get_weather], name="weather_agent")
supervisor = create_agent(model=..., tools=[call_weather_agent], name="supervisor")

# 流式时 subgraphs=True + lc_agent_name
current_agent = None
for chunk in agent.stream(..., stream_mode=["messages", "updates"],
                          subgraphs=True, version="v2"):
    if chunk["type"] == "messages":
        token, metadata = chunk["data"]
        if agent_name := metadata.get("lc_agent_name"):
            if agent_name != current_agent:
                print(f"🤖 {agent_name}: ")
                current_agent = agent_name
```

---

## 十、Guardrail Middleware（同时用三种模式）

```python
for chunk in agent.stream(..., stream_mode=["messages", "updates", "custom"], version="v2"):
    if chunk["type"] == "messages":     # 流式 token
        token, metadata = chunk["data"]
    elif chunk["type"] == "updates":    # 完成后的消息
        ...
    elif chunk["type"] == "custom":     # guardrail 中间件推送的安全评估结果
        print(f"Tool calls: {chunk['data'].tool_calls}")
```

三种模式同时使用，各自提供不同维度的数据，互不冲突。

---

## 十一、Disable Streaming

```python
model = ChatOpenAI(model="gpt-5.4", streaming=False)
# 或对于不支持 streaming 参数的模型：
model = SomeModel(disable_streaming=True)  # 通过基类提供
```

---

## 十二、API 速查表

```python
# === 基本流式 ===
agent.stream(input, stream_mode="updates", version="v2")
agent.stream(input, stream_mode="messages", version="v2")
agent.stream(input, stream_mode="custom", version="v2")

# === 多模式 ===
agent.stream(input, stream_mode=["messages", "updates"], version="v2")
agent.stream(input, stream_mode=["messages", "updates", "custom"], version="v2")

# === 子 Agent ===
agent.stream(input, subgraphs=True, version="v2")

# === Human-in-the-Loop ===
agent.stream(Command(resume=decisions), config=config, version="v2")

# === 工具内推送进度 ===
from langgraph.config import get_stream_writer
writer = get_stream_writer()
writer(任意数据)

# === 消息累积 ===
full = chunk1 + chunk2 + chunk3          # AIMessageChunk 支持加法
token.chunk_position == "last"           # 判断消息结束

# === 禁用流式 ===
ChatOpenAI(streaming=False)
ChatModel(disable_streaming=True)

# === 基础 LLM 流式（非 Agent） ===
llm.stream("你的问题")
llm.invoke("你的问题")
async for chunk in llm.astream("你的问题")
```

---

## 十三、知识点关系图

```
                        LangChain Streaming
                               │
            ┌──────────────────┼─────────────────────┐
            │                  │                     │
        三种模式           v2 统一格式          高级功能
            │                  │                     │
   ┌────────┴────────┐   version="v2"       ┌────────┴────────┐
   │        │        │   StreamPart dict     │        │        │
 updates  messages  custom              thinking  human   sub-
 (每步状态) (逐token) (自定义)             tokens   -in-loop agents
                                              │
                                        guardrail middleware
                                        (三种模式同时用)
```
