"""
=============================================
业务逻辑层 · agent_builder.py
=============================================

【职责】
  本模块相当于 Java 三层架构中的 "Service / 业务逻辑层"，
  负责构建、配置和编译 LangGraph Agent。

【为什么需要】
  1. 将 Agent 的创建逻辑集中管理，避免在入口文件中写大量配置代码
  2. 提供多种构建方法（工厂模式），按需组装不同能力的 Agent
  3. 隔离 LangGraph 框架的细节，上层只需调用 build_xxx() 即可

【对应关系】
  Java 三层架构 -> 本项目的对应
  - Service 层     -> app/agent_builder.py
  - 工厂模式       -> build_basic_agent() / build_agent_with_memory()
  - 依赖注入       -> 通过函数参数传入 tools、model 等依赖
"""

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from app.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEFAULT_TEMPERATURE,
)
from app.tools import DEFAULT_TOOLS


# ===================================================================
# 1. LLM 初始化（工厂方法）
# ===================================================================
# 将 LLM 的创建封装成函数，好处：
#   - 一处修改模型参数，所有 Agent 生效
#   - 方便切换模型（只需改这里，不用改业务代码）
#   - 可扩展：未来支持多个模型实例时，只需增加新的工厂方法

def create_default_llm(temperature: float = DEFAULT_TEMPERATURE) -> ChatOpenAI:
    """
    创建默认的 LLM 实例（DeepSeek Chat）。

    使用 ChatOpenAI 类连接 DeepSeek 的兼容 API。
    LangChain 的 ChatOpenAI 原生支持 OpenAI 格式的 API，
    而 DeepSeek 提供了完全兼容的接口，因此可以无缝使用。

    Args:
        temperature: 温度参数，控制输出的随机性。
                     默认 0.0 使输出更确定。

    Returns:
        配置好的 ChatOpenAI 实例
    """
    return ChatOpenAI(
        model=DEEPSEEK_MODEL,
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        temperature=temperature,
    )


def create_json_llm(temperature: float = DEFAULT_TEMPERATURE) -> ChatOpenAI:
    """
    创建启用了 DeepSeek JSON Output 功能的 LLM 实例。

    DeepSeek 原生支持 response_format={'type': 'json_object'} 参数，
    可以确保模型输出始终是合法的 JSON 字符串。
    这是 DeepSeek 官方推荐的结构化输出方式。

    与 LangGraph 的 response_format 参数的区别：
    ┌────────────────────┬────────────────────────────────┬──────────────────────────────┐
    │                    │ DeepSeek JSON Output           │ LangGraph response_format    │
    ├────────────────────┼────────────────────────────────┼──────────────────────────────┤
    │ 参数位置             │ LLM 层 model_kwargs            │ Agent 层参数                 │
    │ 实现原理             │ API 层面保证输出合法 JSON       │ 额外调用一次 LLM 做格式化     │
    │ 模型支持             │ DeepSeek 全系列                │ 需模型支持 json_schema       │
    │ 与工具调用兼容        │ 兼容（不影响 tool_calls）       │ 兼容                         │
    │ 额外开销             │ 无                             │ 多一次 LLM 调用              │
    └────────────────────┴────────────────────────────────┴──────────────────────────────┘

    Args:
        temperature: 温度参数。

    Returns:
        启用了 JSON Output 的 ChatOpenAI 实例
    """
    return ChatOpenAI(
        model=DEEPSEEK_MODEL,
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        temperature=temperature,
        # DeepSeek JSON Output：通过 model_kwargs 传递 API 原生参数
        # 参数格式：{"response_format": {"type": "json_object"}}
        # 作用：确保模型每次回复的内容都是合法的 JSON 字符串
        # 注意：使用此功能时，prompt 中必须包含 "json" 字样和格式示例
        model_kwargs={"response_format": {"type": "json_object"}},
    )


# ===================================================================
# 2. Agent 构建器（工厂方法集合）
# ===================================================================
# 以下每个 build_xxx 方法对应快速入门中的一个步骤，
# 步骤之间是递增的：后面的步骤在前面的基础上增加新功能。
#
# create_react_agent 是 LangGraph 提供的预构建 Agent 创建函数，
# 它封装了 StateGraph 的创建、节点连接、条件路由等底层逻辑，
# 让开发者可以一行代码创建功能完善的 Agent。


def build_basic_agent():
    """
    [步骤 2] 创建基础 Agent。

    这是最简单的 Agent 形式：
    - 一个 LLM + 一组工具
    - 无记忆（每次对话都是独立的）
    - 无自定义提示（使用 LLM 默认行为）
    - 无结构化输出

    Returns:
        CompiledGraph: 可调用的编译后图对象
    """
    llm = create_default_llm()

    # create_react_agent 是 LangGraph 的 "快速通道" API：
    # - 自动创建 StateGraph
    # - 自动添加 chatbot 节点 和 tool 节点
    # - 自动配置条件路由（有 tool call 就走 tool，否则直接回复）
    # - 返回编译好的 CompiledGraph，可直接 invoke/stream
    agent = create_react_agent(
        model=llm,
        tools=DEFAULT_TOOLS,
    )
    return agent


def build_agent_with_prompt(prompt: str = None):
    """
    [步骤 4] 创建带自定义提示的 Agent。

    通过 prompt 参数注入 System Message，引导 LLM 的行为模式。
    提示（Prompt）是控制 Agent 行为的"无形之手"。

    Args:
        prompt: 自定义系统提示文本。
                如果为 None，使用默认的天气助手提示。

    Returns:
        CompiledGraph: 可调用的编译后图对象
    """
    llm = create_default_llm()

    if prompt is None:
        prompt = "你是一个贴心的天气助手。请用友好的语气回答天气问题，并给出出行建议。"

    agent = create_react_agent(
        model=llm,
        tools=DEFAULT_TOOLS,
        # prompt 参数可以是：
        # - 字符串：作为 System Message 自动添加
        # - 消息列表：更复杂的提示结构
        # - 可调用对象：在运行时动态生成提示（高级用法）
        prompt=prompt,
    )
    return agent


def build_agent_with_memory():
    """
    [步骤 5] 创建带记忆的 Agent（支持多轮对话）。

    通过 checkpointer 实现对话历史的持久化：
    - 每次调用 Agent 后，状态自动保存到检查点
    - 下次用相同的 thread_id 调用时，自动恢复之前的对话
    - 不同 thread_id 之间的对话完全隔离

    Returns:
        CompiledGraph: 编译后的图对象，需在 invoke 时传入 config
    """
    llm = create_default_llm()

    # MemorySaver 是 LangGraph 内置的内存检查点保存器
    # 生产环境中应替换为 SqliteSaver / PostgresSaver 等持久化方案
    checkpointer = MemorySaver()

    agent = create_react_agent(
        model=llm,
        tools=DEFAULT_TOOLS,
        checkpointer=checkpointer,
    )
    return agent


def build_structured_agent():
    """
    [步骤 6] 创建支持结构化输出的 Agent。

    通过精心设计的 System Prompt 引导 LLM 输出 JSON 格式的结构化数据。
    这种方式兼容所有模型，不依赖特定的 API 参数。

    ⚠ 关于 DeepSeek JSON Output 的说明：
      DeepSeek 官方支持 response_format={'type': 'json_object'} 参数来确保输出合法 JSON。
      但在 LangChain 的 ChatOpenAI 封装中，启用此参数后会触发 openai 库的 strict 工具校验，
      要求所有工具函数标记 strict=True，否则会报错。因此本项目采用更通用的 Prompt 引导方案。
      有关 DeepSeek JSON Output 的详细说明和纯 API 示例，请参见配套笔记中的相关章节。

    结构化输出的两种常见实现方式：
    ┌──────────────────────┬──────────────────────────────┬──────────────────────────────┐
    │ 方案                 │ 原理                         │ 适用场景                     │
    ├──────────────────────┼──────────────────────────────┼──────────────────────────────┤
    │ Prompt 引导（本项目）│ System Prompt 中要求 JSON     │ 兼容所有模型，无额外依赖     │
    │ 原生 JSON Output     │ API 参数强制输出合法 JSON     │ 模型原生支持，格式更可靠     │
    └──────────────────────┴──────────────────────────────┴──────────────────────────────┘

    Returns:
        CompiledGraph: 可调用的编译后图对象
    """
    llm = create_default_llm()

    # 结构化输出提示：在 System Message 中明确要求 JSON 格式
    # 关键技巧：给出具体的输出示例（Few-shot），LLM 更容易遵循
    structured_prompt = (
        "你是一个天气数据服务。请严格按以下 JSON 格式返回结果，不要包含任何其他文字：\n"
        '{"city": "城市名", "conditions": "天气状况描述", "temperature": "温度描述"}'
    )

    agent = create_react_agent(
        model=llm,
        tools=DEFAULT_TOOLS,
        prompt=structured_prompt,
    )
    return agent


# ===================================================================
# 3. 高层封装：一站式构建（可选）
# ===================================================================
# 如果需要更复杂的组合，可以在此处提供更高级的构建方法。

def build_advanced_agent(prompt: str = None, use_memory: bool = True,
                         response_format=None):
    """
    灵活的 Agent 构建方法，按需组合各项能力。

    这是**门面模式（Facade）**的应用：
    隐藏底层复杂的组装逻辑，提供简洁的统一接口。

    Args:
        prompt: 自定义提示
        use_memory: 是否启用记忆
        response_format: 结构化输出模型

    Returns:
        CompiledGraph: 编译后的图对象
    """
    llm = create_default_llm()
    checkpointer = MemorySaver() if use_memory else None

    agent = create_react_agent(
        model=llm,
        tools=DEFAULT_TOOLS,
        prompt=prompt,
        checkpointer=checkpointer,
        response_format=response_format,
    )
    return agent
