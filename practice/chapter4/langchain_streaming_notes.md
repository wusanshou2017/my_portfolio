# LangChain Streaming 知识点总结

> 来源: https://docs.langchain.com/oss/python/langchain/streaming

## 一、为什么需要 Streaming

LLM 生成完整响应可能需要 **数秒到十几秒**，远超用户感知的 ~200ms 响应阈值。Streaming 通过逐步显示输出，显著提升用户体验。

**核心收益：**
- 用户立即看到进展，减少等待焦虑
- 感知性能提升（总时间不变，但体感更快）
- 可以展示中间步骤和状态（Agent 场景尤为重要）

---

## 二、LangChain Streaming 体系总览

LangChain 的流式系统围绕 **Agent** 构建，支持从不同维度获取实时反馈：

```
                    LangChain Streaming
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    Agent Progress    LLM Tokens     Custom Updates
    (每步状态更新)    (逐token输出)   (工具自定义进度)
          │                │                │
    stream_mode=     stream_mode=     stream_mode=
     "updates"        "messages"        "custom"
```

---

## 三、三种核心 Stream Mode

### 3.1 `stream_mode="updates"` — Agent 进度流

**用途：** 获取 Agent 每一步执行后的状态更新。

**典型流程（以 tool calling 为例）：**
```
步骤1: model  → AIMessage（包含 tool_call 请求）
步骤2: tools  → ToolMessage（工具执行结果）
步骤3: model  → AIMessage（最终回复）
```

**代码模式：**
```python
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "..."}]},
    stream_mode="updates",
):
    for step, data in chunk.items():
        last_msg = data["messages"][-1]
        # step: "model" 或 "tools"
        # last_msg: AIMessage 或 ToolMessage
```

**关键点：**
- 每个 chunk 对应 Agent 的一个执行步骤
- chunk 是 `dict`，key 是节点名（`model`、`tools`）
- 通过 `data["messages"][-1]` 获取该步骤的最新消息

---

### 3.2 `stream_mode="messages"` — LLM Token 流

**用途：** 逐 token 流式输出 LLM 的响应，包括工具调用参数的生成过程。

**代码模式：**
```python
for token, metadata in agent.stream(
    {"messages": [{"role": "user", "content": "..."}]},
    stream_mode="messages",
):
    # token: AIMessageChunk（包含一个 token 的内容）
    # metadata: dict，包含 langgraph_node、ls_provider 等信息
```

**关键点：**
- 每个 token 是一个 `(AIMessageChunk, metadata)` 元组
- `metadata["langgraph_node"]` 告诉你这个 token 来自哪个节点
- 不仅流式输出最终文本，还能看到 **tool call 参数的逐片段生成过程**

**AIMessageChunk 中的 content_blocks 类型：**

| type | 含义 | 示例 |
|---|---|---|
| `text` | 普通文本 token | `{"type": "text", "text": "Hello"}` |
| `tool_call` | 完整的工具调用（首个 chunk） | `{"type": "tool_call", "name": "get_weather", "args": {...}}` |
| `tool_call_chunk` | 工具调用参数的片段 | `{"type": "tool_call_chunk", "args": '{"city'}` |
| `reasoning` | 模型推理/思考内容 | `{"type": "reasoning", "reasoning": "让我想想..."}` |

---

### 3.3 `stream_mode="custom"` — 自定义更新流

**用途：** 工具函数内部主动推送进度信息给外部。

**代码模式：**
```python
from langgraph.config import get_stream_writer

def my_tool(query: str) -> str:
    writer = get_stream_writer()
    writer("正在查询数据库...")       # 实时推送
    result = query_database(query)
    writer(f"已获取 {len(result)} 条记录")  # 实时推送
    return result

# 接收端
for chunk in agent.stream(..., stream_mode="custom"):
    print(chunk)  # "正在查询数据库..." / "已获取 10 条记录"
```

**关键点：**
- `get_stream_writer()` 只能在 LangGraph 执行上下文中使用
- 工具加了 `get_stream_writer()` 后，不能在 Agent 外部单独调用
- 适合推送"已获取 10/100 条记录"这类进度信息

---

## 四、组合模式

### 4.1 多模式同时使用

`stream_mode` 支持传入列表，同时使用多种模式：

```python
for chunk in agent.stream(
    {"messages": [...]},
    stream_mode=["updates", "custom"],
):
    # chunk 是 (stream_mode, data) 元组
    # stream_mode: "updates" 或 "custom"
```

**常见组合：**

| 组合 | 用途 |
|---|---|
| `["messages", "updates"]` | 同时获取 token 流和完成后的解析结果 |
| `["updates", "custom"]` | 同时获取 Agent 步骤状态和工具自定义进度 |
| `["messages", "updates", "custom"]` | 全部都要 |

### 4.2 Streaming Tool Calls（重点）

这是最实用的组合模式，同时拿到：
1. **`messages`**：tool call JSON 的逐片段生成过程
2. **`updates`**：完成解析后的 `tool_calls` 和 `ToolMessage` 结果

```python
for chunk in agent.stream(
    {"messages": [input_message]},
    stream_mode=["messages", "updates"],
):
    if chunk["type"] == "messages":
        token, metadata = chunk["data"]
        # token.text           → 文本 token
        # token.tool_call_chunks → 工具调用参数片段
    elif chunk["type"] == "updates":
        for source, update in chunk["data"].items():
            if source == "model":
                # update["messages"][-1].tool_calls → 完整的解析后工具调用
            if source == "tools":
                # update["messages"][-1] → 工具执行结果
```

### 4.3 聚合 Chunks 获取完整消息

当完成的消息不在 state 中时，可以在流式循环中手动聚合：

```python
full_message = None
for chunk in agent.stream(..., stream_mode=["messages", "updates"]):
    if chunk["type"] == "messages":
        token, metadata = chunk["data"]
        full_message = token if full_message is None else full_message + token
        if token.chunk_position == "last":  # 消息结束标志
            if full_message.tool_calls:
                print(full_message.tool_calls)  # 完整的解析后工具调用
            full_message = None
```

**关键 API：**
- `full_message + token` — AIMessageChunk 支持加法累积
- `token.chunk_position == "last"` — 判断当前消息是否结束

---

## 五、高级主题

### 5.1 Streaming Thinking / Reasoning Tokens

流式输出模型的思考/推理过程（如 DeepSeek-R1、Claude 等）：

```python
for token, metadata in agent.stream(..., stream_mode="messages"):
    content_blocks = token.content_blocks
    reasoning = [b for b in content_blocks if b["type"] == "reasoning"]
    text = [b for b in content_blocks if b["type"] == "text"]
```

**LangChain 的统一抽象：**
- Anthropic 的 `thinking` blocks → 统一为 `type="reasoning"`
- OpenAI 的 `reasoning` summaries → 统一为 `type="reasoning"`
- 开发者只需过滤 `type == "reasoning"`，不用关心底层模型差异

### 5.2 Disable Streaming

```python
model = ChatOpenAI(model="gpt-5.4", streaming=False)
```

**适用场景：**
- 多 Agent 系统中控制哪些 Agent 流式输出
- 混合支持和不支持流式的模型
- 部署到 LangSmith 时不希望某些模型输出流式到客户端

### 5.3 v2 Streaming Format

```python
for chunk in agent.stream(..., stream_mode=["updates", "custom"], version="v2"):
    chunk["type"]  # "updates" 或 "custom"（不再需要 tuple 解包）
    chunk["data"]  # payload
```

**v1 vs v2 对比：**

| 特性 | v1（默认） | v2 |
|---|---|---|
| chunk 格式 | `(mode, data)` 元组 | `{"type": mode, "data": data}` dict |
| 访问方式 | `for mode, chunk in agent.stream(...)` | `for chunk in agent.stream(...)` |
| 需要 LangGraph | 任意版本 | >= 1.1 |

### 5.4 Human-in-the-Loop

工具调用前暂停等待人工审批：

```
核心流程:
1. 配置 HumanInTheLoopMiddleware(interrupt_on={"tool_name": True})
2. 配置 checkpointer 保存状态
3. stream 循环中收集 source == "__interrupt__" 的事件
4. 人工决策: {"type": "approve"} 或 {"type": "edit", "edited_action": {...}}
5. 用 Command(resume=decisions) 恢复执行
```

### 5.5 Streaming from Sub-agents

多 Agent 场景下区分 token 来源：

```python
# 创建时设置 name
agent = create_agent(model=llm, tools=[...], name="weather_agent")

# 流式时通过 metadata 区分
for chunk in agent.stream(..., subgraphs=True):
    agent_name = metadata.get("lc_agent_name")  # "weather_agent" 或 "supervisor"
```

---

## 六、与 OpenAI SDK 的对比

| 特性 | OpenAI SDK | LangChain Streaming |
|---|---|---|
| 流式单位 | `chunk.choices[0].delta.content` | `AIMessageChunk.content` |
| 只能流式 token | ✅ 仅此一种 | ❌ 还有 updates、custom 等 |
| 工具调用进度 | 需要手动处理 `function_call` | 自动解析为 `tool_call_chunks` |
| Agent 中间步骤 | 需要自己实现 | `stream_mode="updates"` 内置 |
| 工具内推送进度 | 需要自己实现 | `get_stream_writer()` 内置 |
| 多 Agent 区分 | 需要自己实现 | `lc_agent_name` 内置 |

**一句话总结：OpenAI SDK 只管"模型输出 token"，LangChain Streaming 管"整个 Agent 链路的实时状态"。**

---

## 七、API 速查表

```python
# 基础 Agent 流式
agent.stream(input, stream_mode="updates")     # 每步状态
agent.stream(input, stream_mode="messages")    # 逐 token
agent.stream(input, stream_mode="custom")      # 自定义更新

# 多模式
agent.stream(input, stream_mode=["messages", "updates"])

# v2 格式
agent.stream(input, stream_mode=["updates"], version="v2")

# 异步版本
async for chunk in agent.astream(input, stream_mode="updates"):
    ...

# 基础 LLM 流式（非 Agent）
llm.stream("你的问题")      # 逐 token
llm.invoke("你的问题")      # 非流式，等待完整响应
llm = ChatOpenAI(streaming=False)  # 禁用流式

# 工具内推送进度
from langgraph.config import get_stream_writer
writer = get_stream_writer()
writer("任意数据")

# 消息累积
full = chunk1 + chunk2 + chunk3  # AIMessageChunk 支持加法
token.chunk_position == "last"   # 判断消息结束
```
