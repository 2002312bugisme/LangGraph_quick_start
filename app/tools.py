"""
=============================================
工具层 · tools.py
=============================================

【职责】
  本模块相当于 Java 三层架构中的 "DAO / 数据访问层"，
  定义 Agent 可以调用的外部工具（函数）。

【为什么需要】
  1. 将 Agent 的业务逻辑与具体的工具实现解耦
  2. 新增工具只需在此模块添加函数，无需修改 Agent 构建代码
  3. 每个工具都有清晰的签名和文档，LLM 据此决定何时调用

【对应关系】
  Java 三层架构 -> 本项目的对应
  - DAO (Data Access Object)  -> app/tools.py
  - Repository / Mapper       -> 每个 @tool 函数
  - 外部 API 调用             -> get_weather 等工具函数

【工具函数的要求】
  - 每个工具必须是普通的 Python 函数
  - 必须有类型注解（LLM 通过类型推断参数格式）
  - 必须有清晰的 docstring（LLM 通过 docstring 理解工具用途）
  - 返回可序列化的数据类型（str, dict, list 等）
"""


def get_weather(city: str) -> str:
    """
    获取指定城市的天气信息。

    这是快速入门中最简单的示例工具，直接返回固定文本。
    在实际项目中，此函数应调用真实的天气 API（如 OpenWeatherMap）。

    Args:
        city: 城市名称，例如 "上海"、"San Francisco"

    Returns:
        包含天气信息的字符串描述。

    注意：
        LLM 会根据函数签名和 docstring 自动决定何时调用此工具。
        因此 docstring 必须清晰描述工具的用途和参数含义。
    """
    # 这里是一个模拟实现，不依赖外部 API
    # 在真实项目中，此处应为 HTTP 调用或其他 I/O 操作
    return f"☀️ It's always sunny in {city}!"


# ===================================================================
# 工具注册表（可选扩展）
# ===================================================================
# 如果工具较多，可以在此处统一管理工具列表，
# 方便在构建 Agent 时一次性传入。

TOOL_REGISTRY = {
    "get_weather": get_weather,
}

# 预编译的工具列表，供 agent_builder 直接使用
DEFAULT_TOOLS = [get_weather]
