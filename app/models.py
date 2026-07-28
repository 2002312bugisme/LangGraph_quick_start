"""
=============================================
数据模型层 · models.py
=============================================

【职责】
  本模块相当于 Java 三层架构中的 "Entity / DTO" 层，
  定义项目中所有的数据结构、状态类型和请求/响应模型。

【为什么需要】
  1. 明确的数据结构规范，减少 "魔术字典" 带来的隐式依赖
  2. 利用类型注解和 Pydantic 做运行时校验，提前发现数据问题
  3. 为 LangGraph 的状态（State）提供类型安全的定义

【对应关系】
  Java 三层架构 -> 本项目的对应
  - Entity / POJO / DTO    -> app/models.py
  - 数据库 Schema 定义      -> State TypedDict + Pydantic Model
"""

from typing import Annotated

from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from pydantic import BaseModel


# ===================================================================
# LangGraph 状态定义
# ===================================================================
# 在 LangGraph 中，State（状态）是贯穿整个图执行流程的数据载体。
# 每个节点（Node）读取当前 State，处理后返回 State 的更新。
# 这里的 add_messages 是一个 reducer 函数，它定义了当多个节点
# 同时更新 messages 字段时，新消息追加到已有列表末尾，而非覆盖。

class AgentState(TypedDict):
    """
    Agent 运行状态。

    这是 LangGraph 图中的"数据总线"，所有节点共享此状态。
    类似于 Java 中的 ServletRequest 或 上下文对象。

    Attributes:
        messages: 对话消息列表。使用 add_messages reducer 确保
                  每次更新是追加而非覆盖，保留完整的对话历史。
    """
    messages: Annotated[list, add_messages]


# ===================================================================
# 结构化输出模型
# ===================================================================
# 使用 Pydantic 模型定义输出格式，LangGraph 会根据此模型
# 自动引导 LLM 生成符合格式的 JSON 响应。
# 这类似于 Java 中定义 DTO（Data Transfer Object）。

class WeatherResponse(BaseModel):
    """
    天气查询的结构化响应格式。

    通过 response_format 参数传入 create_react_agent，
    让 LLM 输出符合此结构的 JSON，而非自由文本。

    优势：
    - 输出格式可控，便于下游程序解析
    - Pydantic 自动做字段校验
    - 配合 FastAPI 可直接作为 API 响应模型
    """
    conditions: str
    """天气状况描述，例如 "Sunny, 25°C" """
