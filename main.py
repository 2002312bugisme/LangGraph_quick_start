#!/usr/bin/env python3
"""
=============================================
LangGraph 快速入门 Demo · 主程序入口
=============================================

【职责】
  本文件相当于 Java 三层架构中的 "Controller / 表现层"，
  负责：
  1. 接收用户输入（命令行参数 / 终端输入）
  2. 调用 Service 层（agent_builder）构建 Agent
  3. 调用 Agent 处理用户消息
  4. 展示结果给用户

【用法】
  python main.py              → 运行交互式完整演示
  python main.py 1            → 仅运行步骤 1~4 中的某一步
  python main.py --step 1

【学习路径】
  步骤 1: 基础 Agent        → 演示最简单的 Agent 调用
  步骤 2: 自定义提示        → 演示 Prompt 如何影响 Agent 行为
  步骤 3: 带记忆的 Agent    → 演示多轮对话记忆
  步骤 4: 结构化输出        → 演示输出格式控制
"""

import sys
import json
import io

# -------------------------------------------------------------------
# 解决 Windows 控制台 GBK 编码无法显示 Emoji 的问题
# 将 stdout/stderr 的编码设为 UTF-8，使 Emoji 和中文正常输出
# -------------------------------------------------------------------
if sys.stdout.encoding and sys.stdout.encoding.upper() not in ("UTF-8", "UTF8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass  # 如果设置失败，忽略，最坏情况是 emoji 显示乱码

# 导入核心组件（依赖倒置：高层模块依赖抽象，不依赖细节）
from app.config import validate_config, DEEPSEEK_MODEL
from app.agent_builder import (
    build_basic_agent,
    build_agent_with_prompt,
    build_agent_with_memory,
    build_structured_agent,
)
from app.models import WeatherResponse


# ===================================================================
# 辅助函数
# ===================================================================

def print_separator(title: str = ""):
    """打印分隔线，美化输出"""
    width = 60
    print("\n" + "=" * width)
    if title:
        print(f"  {title}")
        print("=" * width)


def print_messages(response: dict):
    """打印 Agent 响应的最后一条消息"""
    last_message = response["messages"][-1]
    print(f"\n🤖 Agent: {last_message.content}\n")


# ===================================================================
# 步骤演示函数
# 每个步骤独立完整，展示一个特定的功能点
# ===================================================================

def step1_basic_agent():
    """
    【步骤 1】基础 Agent 演示

    创建最简单的 Agent，调用一次，观察基础行为。
    这个 Agent 没有记忆，每次调用都是独立的。

    学习要点：
    - create_react_agent 的基本用法
    - invoke() 的输入/输出格式
    - Agent 如何自动调用工具
    """
    print_separator("步骤 1：基础 Agent — 最简单的 Agent 调用")

    # 1. 构建 Agent
    print("📦 正在构建基础 Agent...")
    agent = build_basic_agent()
    print("✅ Agent 构建完成！")

    # 2. 准备用户消息
    #    输入格式：{"messages": [{"role": "user", "content": "..."}]}
    #    这是 LangGraph 统一的消息格式，与 OpenAI API 格式一致
    user_message = "what is the weather in San Francisco?"
    print(f"\n👤 用户: {user_message}")

    # 3. 调用 Agent
    #    invoke() 是同步调用，会等待 Agent 执行完毕
    #    stream() 可以逐 token 流式输出（更高效）
    response = agent.invoke(
        {"messages": [{"role": "user", "content": user_message}]}
    )

    # 4. 输出结果
    #    response["messages"] 包含完整的对话历史
    #    最后一条通常是 AI 的回复
    print_messages(response)
    return response


def step2_with_prompt():
    """
    【步骤 2】自定义提示词演示

    通过 prompt 参数设置 System Message，控制 Agent 的语气和行为。
    提示工程（Prompt Engineering）是控制 LLM 行为最核心的手段。

    学习要点：
    - prompt 参数的本质就是 System Message
    - 不同的 prompt 会让 Agent 产生截然不同的回复风格
    - prompt 在 Agent 构建时指定，运行时不可变
    """
    print_separator("步骤 2：自定义提示词 — 控制 Agent 的行为风格")

    # 1. 构建带提示的 Agent
    #     这个提示让 Agent 用中文、贴心的风格回答问题
    custom_prompt = (
        "你是一位专业的天气播报员。请遵循以下规则：\n"
        "1. 始终用中文回复\n"
        "2. 回复要简洁（不超过 3 句话）\n"
        "3. 在末尾加上一句温馨的出行建议\n"
        "4. 如果用户没有明确指定城市，主动询问"
    )

    print(f"📝 自定义提示:\n{custom_prompt}\n")
    agent = build_agent_with_prompt(prompt=custom_prompt)
    print("✅ 带提示的 Agent 构建完成！")

    # 2. 测试不同风格的输入
    user_message = "what is the weather in Tokyo?"
    print(f"👤 用户: {user_message}")

    response = agent.invoke(
        {"messages": [{"role": "user", "content": user_message}]}
    )
    print_messages(response)
    return response


def step3_with_memory():
    """
    【步骤 3】带记忆的 Agent 演示

    使用 checkpointer 实现多轮对话记忆。
    同一个 thread_id 内的多次调用共享对话历史。

    学习要点：
    - MemorySaver 是 LangGraph 内置的内存检查点器
    - thread_id 是对话分组的唯一标识
    - 不同 thread_id 的数据完全隔离
    - 检查点机制不仅存储消息，还存储完整的 Agent 状态
    """
    print_separator("步骤 3：带记忆的 Agent — 多轮对话演示")

    # 1. 构建带记忆的 Agent
    agent = build_agent_with_memory()
    print("✅ 带记忆的 Agent 构建完成！")

    # 2. 定义对话 ID（thread_id）
    #    同一个 thread_id = 同一场对话
    #    不同的 thread_id = 不同的对话（互不干扰）
    thread_id = "demo-conversation-001"
    config = {"configurable": {"thread_id": thread_id}}

    print(f"🔖 会话 Thread ID: {thread_id}")
    print("─" * 50)

    # 3. 第一轮对话：自我介绍
    msg1 = "你好！我叫张三，是一名软件工程师。"
    print(f"\n👤 [第1轮] 用户: {msg1}")
    response1 = agent.invoke(
        {"messages": [{"role": "user", "content": msg1}]},
        config
    )
    print(f"🤖 [第1轮] Agent: {response1['messages'][-1].content}")

    # 4. 第二轮对话：考验记忆
    #    注意：我们只问了 "还记得我的名字吗？"，
    #    并没有再次告诉名字。如果 Agent 有记忆，它应该记得。
    msg2 = "还记得我的名字和职业吗？"
    print(f"\n👤 [第2轮] 用户: {msg2}")
    response2 = agent.invoke(
        {"messages": [{"role": "user", "content": msg2}]},
        config
    )
    print(f"🤖 [第2轮] Agent: {response2['messages'][-1].content}")

    # 5. 第三轮对话：用不同的 thread_id（无记忆）
    #    注意：我们换了一个新的 thread_id，Agent 应该不记得之前的对话
    config2 = {"configurable": {"thread_id": "another-conversation-002"}}
    msg3 = "还记得我叫什么吗？"
    print(f"\n👤 [第3轮 - 新会话] 用户: {msg3}")
    print("   (使用了不同的 thread_id，Agent 应该不记得)")
    response3 = agent.invoke(
        {"messages": [{"role": "user", "content": msg3}]},
        config2
    )
    print(f"🤖 [第3轮] Agent: {response3['messages'][-1].content}")

    print("\n📌 结论：同一个 thread_id 共享记忆，不同 thread_id 完全隔离。")
    return response2


def step4_structured_output():
    """
    【步骤 4】结构化输出演示

    通过 Prompt 引导 LLM 输出 JSON 格式的结构化数据。
    这对于需要程序化处理 Agent 输出的场景非常有用。

    ⚠ 说明：
      部分模型（如 DeepSeek）不支持 LangGraph 内置的 response_format 参数，
      因此这里采用"Prompt 引导 + 手动解析"的方式，兼容性更广。

    学习要点：
    - 通过 System Message 约束输出格式
    - 给出 Few-shot 示例能显著提高格式遵从度
    - 实际生产中可以结合 Pydantic 做数据校验
    """
    import json

    print_separator("步骤 4：结构化输出 — 让 Agent 输出 JSON 格式")

    # 1. 构建 Agent（使用 Prompt 引导方式）
    agent = build_structured_agent()
    print("📐 输出格式: JSON { city, conditions, temperature }")
    print("✅ 结构化 Agent 构建完成！")

    # 2. 调用 Agent
    user_message = "what is the weather in Beijing?"
    print(f"\n👤 用户: {user_message}")

    response = agent.invoke(
        {"messages": [{"role": "user", "content": user_message}]}
    )

    # 3. 获取原始文本回复
    raw_content = response["messages"][-1].content
    print(f"\n📝 Agent 原始回复:")
    print(f"   {raw_content}")

    # 4. 尝试从回复中提取 JSON
    #    通过简单启发式方法提取 JSON 部分
    print(f"\n📊 结构化解析结果:")
    try:
        # 查找 JSON 部分（可能被 markdown 代码块包裹，也可能直接输出）
        if "```json" in raw_content:
            json_str = raw_content.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_content:
            json_str = raw_content.split("```")[1].split("```")[0].strip()
        else:
            json_str = raw_content.strip()

        data = json.loads(json_str)
        print(f"   ✅ 成功解析为 JSON:")
        print(f"      {json.dumps(data, ensure_ascii=False, indent=6)}")

        # 演示程序化访问
        print(f"\n🔍 程序化访问字段:")
        print(f"   city       = '{data.get('city', 'N/A')}'")
        print(f"   conditions = '{data.get('conditions', 'N/A')}'")
        print(f"   temperature = '{data.get('temperature', 'N/A')}'")
    except (json.JSONDecodeError, IndexError) as e:
        print(f"   ⚠ 未能自动解析为 JSON（{e}）")
        print(f"   💡 提示：可以调整 Prompt 中的格式要求来改进")
    return response


# ===================================================================
# 主流程控制
# ===================================================================

def run_all_steps():
    """
    按顺序运行所有步骤，展示从简单到复杂的完整学习路径。
    每个步骤之间用分隔线隔开，并暂停等待用户确认。
    """
    steps = [
        ("步骤 1: 基础 Agent", step1_basic_agent),
        ("步骤 2: 自定义提示词", step2_with_prompt),
        ("步骤 3: 带记忆的 Agent", step3_with_memory),
        ("步骤 4: 结构化输出", step4_structured_output),
    ]

    for i, (name, func) in enumerate(steps, 1):
        print(f"\n")
        print("╔" + "═" * 58 + "╗")
        print(f"║  正在执行 [{i}/{len(steps)}] {name:<35} ║")
        print("╚" + "═" * 58 + "╝")
        func()

        if i < len(steps):
            input("\n⏎ 按回车键继续下一步...")

    print_separator("全部步骤执行完毕！🎉")
    print("你已完成了 LangGraph 快速入门的所有核心概念学习。")


def main():
    """
    主入口函数。

    支持的命令行参数：
      python main.py          - 运行全部步骤
      python main.py 1        - 仅运行步骤 1
      python main.py --step 2 - 仅运行步骤 2
    """
    # 1. 启动时验证配置
    if not validate_config():
        print("请先在 .env 文件中配置 DEEPSEEK_API_KEY")
        sys.exit(1)

    print("=" * 60)
    print("  LangGraph 快速入门 Demo")
    print(f"  模型: {DEEPSEEK_MODEL}")
    print("=" * 60)

    # 2. 解析命令行参数
    step_map = {
        "1": step1_basic_agent,
        "2": step2_with_prompt,
        "3": step3_with_memory,
        "4": step4_structured_output,
    }

    if len(sys.argv) > 1:
        # 指定了步骤
        arg = sys.argv[1]
        if arg in step_map:
            step_map[arg]()
        elif arg == "--step" and len(sys.argv) > 2:
            step = sys.argv[2]
            if step in step_map:
                step_map[step]()
            else:
                print(f"无效步骤: {step}，可用选项: 1, 2, 3, 4")
        else:
            print(f"无效参数: {arg}")
            print("用法: python main.py [1|2|3|4]")
    else:
        # 未指定参数，运行全部
        run_all_steps()


if __name__ == "__main__":
    main()
