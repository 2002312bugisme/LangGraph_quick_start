# LangGraph 快速入门指南

> 本文档是 `langgraph_demo/` 项目的配套学习笔记。
> 目标：从零开始理解 LangGraph Agent 的构建原理、项目架构和每一步的必要性。

---

## 目录

1. [项目概览与目录结构](#1-项目概览与目录结构)
2. [三层架构设计理念](#2-三层架构设计理念)
3. [快速入门六步骤详解](#3-快速入门六步骤详解)
4. [运行项目](#4-运行项目)
5. [常见问题与扩展建议](#5-常见问题与扩展建议)

---

## 1. 项目概览与目录结构

### 1.1 项目目录树

```
langgraph_demo/                   # 项目根目录
├── .env                          # 环境变量（API 密钥等敏感信息）
├── .gitignore                    # Git 忽略规则
├── requirements.txt              # Python 依赖清单
├── main.py                       # 【表现层】程序入口
├── quickstart_guide.md           # 本文档：配套学习笔记
└── app/                          # 应用核心（三层架构）
    ├── __init__.py               # Python 包标识
    ├── config.py                 # 【配置层】环境变量与参数管理
    ├── models.py                 # 【数据模型层】State 与 DTO 定义
    ├── tools.py                  # 【数据访问层】外部工具/函数定义
    └── agent_builder.py          # 【业务逻辑层】Agent 构建与编排
```

### 1.2 每个文件/文件夹的意义

| 文件/文件夹 | 职责 | 类比 Java 项目 |
|-------------|------|----------------|
| `.env` | 存储 API 密钥等环境变量，不提交到 Git | `application-secret.yml` |
| `requirements.txt` | 声明 Python 依赖及其版本 | `pom.xml` / `build.gradle` |
| `main.py` | 程序入口，处理用户交互，调度各步骤 | `Controller` 层 |
| `app/` | 核心业务代码包 | `service/` + `dao/` + `model/` |
| `app/__init__.py` | 标识 `app/` 为 Python 包 | 包声明 |
| `app/config.py` | 集中管理所有配置参数 | `@ConfigurationProperties` |
| `app/models.py` | 定义数据结构和状态类型 | `Entity` / `DTO` |
| `app/tools.py` | 定义 Agent 可调用的工具函数 | `DAO` / `Repository` |
| `app/agent_builder.py` | 构建和编译 LangGraph Agent | `Service` 层 |

---

## 2. 三层架构设计理念

### 2.1 为什么要分层？

一个没有架构的 Python 脚本，所有代码堆在同一个文件中，就像把 Controller、Service、DAO 全写在一个 Java 类里 —— 刚开始觉得方便，但一旦需求变多，就会陷入"改一处动全身"的困境。

分层架构的核心原则：**每一层各司其职，层与层之间通过明确的接口通信**。

### 2.2 我们的三层架构

```
┌─────────────────────────────────────────────────────────┐
│                   表 现 层 (Presentation)                │
│                     main.py                              │
│  职责：处理用户交互、命令行参数解析、结果展示              │
│  类比：Java Controller / Spring MVC @RestController      │
└───────────────────────┬─────────────────────────────────┘
                        │ 调用
                        ▼
┌─────────────────────────────────────────────────────────┐
│                 业 务 逻 辑 层 (Business Logic)          │
│                 agent_builder.py                         │
│  职责：构建 Agent、编排图节点、管理生命周期                │
│  类比：Java Service / @Service                           │
│  核心：create_react_agent / StateGraph 组装              │
└───────────────────────┬─────────────────────────────────┘
          ┌─────────────┼─────────────┐
          │             │             │
          ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   配置层      │ │   数据模型层  │ │   数据访问层  │
│  config.py   │ │  models.py   │ │   tools.py   │
│  读取 .env   │ │ State/TypedDict│ │  工具函数    │
│  类比:       │ │ Pydantic模型 │ │  类比: DAO   │
│  application │ │ 类比: Entity │ │  类比:       │
│  .yml        │ │ / DTO       │ │  Repository  │
└──────────────┘ └──────────────┘ └──────────────┘
```

### 2.3 各层的详细说明

#### 表现层（main.py）

- **职责**：命令行参数解析、步骤调度、用户输入输出
- **设计要点**：
  - 不包含任何 Agent 构建逻辑
  - 只调用 Service 层提供的方法
  - 结果展示与业务逻辑分离
- **类比 Java**：`@RestController` + `@RequestMapping`

#### 业务逻辑层（agent_builder.py）

- **职责**：Agent 的构建、配置、编译
- **设计要点**：
  - 提供多个 `build_xxx()` 工厂方法
  - 不直接处理用户交互
  - 依赖下层（配置/模型/工具）但不依赖上层（表现层）
- **类比 Java**：`@Service` + 工厂模式
- **关键代码**：`create_react_agent()` 是 LangGraph 提供的高阶 API，内部封装了 StateGraph 的创建、节点连接、条件路由等

#### 数据访问层（tools.py）

- **职责**：定义 Agent 可以调用的外部工具
- **设计要点**：
  - 每个工具是一个独立的纯函数
  - 有明确的类型注解和 docstring（LLM 通过 docstring 理解工具用途）
  - 新增工具只需在此文件添加函数
- **类比 Java**：`@Repository` / `DAO` 接口

#### 配置层（config.py）

- **职责**：集中管理所有外部配置
- **设计要点**：
  - 从 `.env` 文件读取配置
  - 提供配置校验函数（Fail-Fast）
  - 所有配置常量集中定义，一处修改全局生效
- **类比 Java**：`application.yml` + `@ConfigurationProperties`

#### 数据模型层（models.py）

- **职责**：定义状态类型、结构化输出模型
- **设计要点**：
  - `AgentState` 是 LangGraph 图中的数据总线
  - `WeatherResponse` 定义输出格式规范
  - 利用 Pydantic 做运行时数据校验
- **类比 Java**：`Entity` / `DTO` / `POJO`

---

## 3. 快速入门六步骤详解

### 步骤 1：安装依赖

```bash
pip install -r requirements.txt
```

**安装了什么：**

| 包名 | 作用 | 类比 Java |
|------|------|-----------|
| `langgraph` | LangGraph 核心框架，提供 StateGraph、预构建 Agent 等 | Spring Framework |
| `langchain-core` | LangChain 核心库，提供消息模型、工具接口等 | Spring Core |
| `langchain-openai` | OpenAI 兼容 API 客户端（用于调用 DeepSeek） | HTTP Client |
| `python-dotenv` | 从 `.env` 文件加载环境变量 | Spring Cloud Config |
| `pydantic` | 数据校验和序列化，定义结构化输出模型 | Jakarta Validation |

**为什么需要：**
没有这些依赖，我们就无法调用 LLM、无法构建 Agent、无法管理配置。它们是项目运行的基础。

---

### 步骤 2：创建基础 Agent

**核心代码**（对应 `app/agent_builder.py` 中的 `build_basic_agent()`）：

```python
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model=llm,
    tools=[get_weather],
)
```

**这段代码做了什么？**

`create_react_agent` 是 LangGraph 提供的 **预构建 Agent 工厂函数**。它在内部完成了以下工作：

1. **创建 `StateGraph`** —— 定义一个状态机
2. **添加 `chatbot` 节点** —— 节点内部调用 LLM，处理用户消息
3. **添加 `tools` 节点** —— 节点负责执行 LLM 请求的工具调用
4. **添加条件边** —— 如果 LLM 生成 `tool_calls`，路由到 tools 节点；否则直接回复用户
5. **编译图** —— 将图结构编译为可调用的 `CompiledGraph`

整个流程形成一个**循环**：

```
用户输入 → chatbot(LLM) → 需要工具？→ 是 → tools → chatbot(LLM) → ...
                         → 否 → 直接回复用户
```

**为什么需要这一步：**
这是 LangGraph Agent 的最小可行单元。没有它，我们只有孤立的 LLM 调用，没有"Agent 循环"（思考→行动→观察→思考...）的能力。

**类比 Java：**
就像 Spring Boot 的 `@SpringBootApplication` —— 一行注解背后做了大量的自动配置。

---

### 步骤 3：配置 LLM

**核心代码**（对应 `app/agent_builder.py` 中的 `create_default_llm()`）：

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key="sk-...",
    base_url="https://api.deepseek.com",
    temperature=0.0,
)
```

**关键参数说明：**

| 参数 | 作用 | 建议值 |
|------|------|--------|
| `temperature` | 控制输出随机性。0.0 最确定，1.0 有创造性 | Agent 场景用 0.0~0.3 |
| `model` | 使用的模型名称 | deepseek-v4-flash / gpt-4 等 |

**为什么 DeepSeek 可以用 `ChatOpenAI`？**
因为 DeepSeek 提供了**完全兼容 OpenAI 格式**的 API 接口，所以 LangChain 的 `ChatOpenAI` 客户端可以直接使用，只需修改 `base_url` 即可。

**为什么需要这一步：**
步骤 2 中的 `create_react_agent(model=...)` 接受任何符合 LangChain 标准的 LLM 实例。通过单独配置 LLM，我们可以精细控制模型参数（temperature、max_tokens 等），而不用修改 Agent 构建代码。

---

### 步骤 4：添加自定义提示（Prompt）

**核心代码**（对应 `build_agent_with_prompt()`）：

```python
agent = create_react_agent(
    model=llm,
    tools=[get_weather],
    prompt="你是一位专业的天气播报员，请用中文回复。"
)
```

**prompt 参数的本质：**
传给 `prompt` 的字符串会被自动作为 **System Message** 插入到对话的开头。System Message 是设定 LLM 行为的最核心手段。

**为什么需要这一步：**
没有自定义提示，LLM 的行为完全由训练数据决定，不可控。通过提示，我们可以：

- **设定角色**：让 Agent 扮演特定角色（天气播报员、客服、导师等）
- **约束行为**：规定回复的语言、长度、风格
- **设定规则**：规定 Agent 何时调用工具、如何处理特定情况
- **注入知识**：提供业务上下文和领域知识

**类比 Java：**
就像在 Spring 中通过 `@Value` 或 `application.yml` 注入配置 —— 把"变化的部分"从代码中抽离出来，让行为可配置。

---

### 步骤 5：添加记忆（Memory）

**核心代码**（对应 `build_agent_with_memory()`）：

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()

agent = create_react_agent(
    model=llm,
    tools=[get_weather],
    checkpointer=checkpointer,
)

# 调用时传入 thread_id
config = {"configurable": {"thread_id": "user-session-1"}}
agent.invoke({"messages": [...]}, config)
```

**记忆的工作原理：**

```
                 ┌──────────────────┐
                 │   Agent 调用 1    │
                 │  thread_id="1"   │──→ 状态自动保存到检查点
                 └──────────────────┘
                         │
                 ┌──────────────────┐
                 │   Agent 调用 2    │
                 │  thread_id="1"   │──→ 加载调用 1 的状态
                 │                  │    + 新的用户输入
                 └──────────────────┘
                         │
                 ┌──────────────────┐
                 │   Agent 调用 3    │
                 │  thread_id="2"   │──→ 全新的对话
                 │                  │    看不到 thread_id="1"
                 └──────────────────┘
```

**为什么需要这一步：**
没有记忆，Agent 每次调用都是"失忆"的。它无法记住用户之前说过什么，多轮对话无法进行。有了记忆：

- Agent 可以记住用户的名字、偏好、上下文
- 可以实现连贯的多轮对话
- 检查点机制不仅存消息，还存完整的 Agent 状态（包括中间变量）

**类比 Java：**
就像 Web 应用的 `HttpSession`——通过 sessionId（即 thread_id）在不同请求间共享用户状态。

---

### 步骤 6：配置结构化输出

**核心代码**（对应 `build_structured_agent()`）：

```python
# 方式一（推荐，兼容所有模型）：通过 Prompt 引导
structured_prompt = (
    "请严格按以下 JSON 格式返回结果：\n"
    '{"city": "城市名", "conditions": "天气状况", "temperature": "温度"}'
)

agent = create_react_agent(
    model=llm,
    tools=[get_weather],
    prompt=structured_prompt,
)

response = agent.invoke({"messages": [...]})
raw = response["messages"][-1].content
data = json.loads(raw)  # 解析 JSON
print(data["conditions"])  # 程序化访问
```

> **关于 `response_format` 参数**：LangGraph 内置的 `response_format` 参数（基于 Pydantic 模型）依赖于 LLM 提供商对 `response_format` 的原生支持。DeepSeek 目前**不**支持此参数。因此本项目采用"Prompt 引导"的替代方案，兼容所有模型。

**为什么需要这一步：**
在很多实际场景中，Agent 的回复需要被程序（而非人类）消费：

- 需要从回复中提取结构化的数据字段
- 需要将回复传递给下游 API 或数据库
- 需要确保回复格式稳定，不随模型版本变化

**类比 Java：**
就像 Controller 方法上标注 `@ResponseBody` —— 明确指定返回的数据格式，客户端可以按约定解析。

---

### 六步骤总览

| 步骤 | 核心概念 | 新增组件 | 解决什么问题 |
|------|----------|----------|-------------|
| 1. 安装依赖 | 环境准备 | `requirements.txt` | 没有任何依赖无法运行 |
| 2. 基础 Agent | `create_react_agent` | Agent + Tool | 让 LLM 具备"思考→行动→观察"循环 |
| 3. 配置 LLM | 模型参数 | temperature 等 | 精细控制模型行为 |
| 4. 自定义提示 | System Message | prompt 参数 | 设定 Agent 的角色和规则 |
| 5. 添加记忆 | Checkpointer | MemorySaver | 实现多轮对话，记住用户上下文 |
| 6. 结构化输出 | Prompt 引导 JSON | System Prompt + 格式示例 | 让输出格式可控、可解析 |

每个步骤都在前一步的基础上增加了**一个新的能力维度**，从最简单的 LLM 调用逐步演进为一个功能完备的 Agent 系统。

---

### 3.7 附录：关于 DeepSeek JSON Output 的深度解析

> 本节内容补充说明结构化输出在 DeepSeek 模型上的实现细节，
> 解释"为什么早期步骤4代码会报错"以及"如何正确使用 DeepSeek 的 JSON Output 功能"。

#### 3.7.1 报错复现：发生了什么？

当我们最初尝试使用 LangGraph 内置的 `response_format` 参数时（传入 Pydantic 模型）：

```python
from pydantic import BaseModel

class WeatherResponse(BaseModel):
    conditions: str

agent = create_react_agent(
    model=llm,
    tools=[get_weather],
    response_format=WeatherResponse,  # ← 这行导致了报错
)
```

运行后得到如下错误：

```
openai.BadRequestError: Error code: 400
{'error': {'message': 'This response_format type is unavailable now',
           'type': 'invalid_request_error', ...}}
```

#### 3.7.2 根本原因分析

| 层面 | 详情 |
|------|------|
| **直接原因** | DeepSeek API 返回 HTTP 400，提示 `response_format type` 不可用 |
| **技术原因** | LangGraph 的 `response_format` 参数内部调用 `model.with_structured_output()`，该方法向 API 发送 `response_format: {"type": "json_schema", "json_schema": {...}}`。**DeepSeek 不支持 `json_schema` 类型** |
| **深层原因** | DeepSeek 的 `response_format` 只支持 `{"type": "json_object"}` 格式（确保输出合法 JSON），不支持 OpenAI 的 JSON Schema 格式（定义具体字段结构） |

**LangGraph `response_format` 的调用链路：**

```
create_react_agent(response_format=WeatherResponse)
  → model.with_structured_output(WeatherResponse)
    → 向 API 发送 response_format={"type": "json_schema", "json_schema": {...}}
      → DeepSeek 不支持 → HTTP 400 ❌
```

#### 3.7.3 解决方案对比

我们评估了以下三种方案，最终选择了方案一：

| 方案 | 原理 | 优点 | 缺点 | 本项目选择 |
|------|------|------|------|:--------:|
| **① Prompt 引导** | System Prompt 中要求输出 JSON，给出格式示例 | 兼容所有模型，零依赖 | 依赖 Prompt 质量，偶有格式偏差 | ✅ **采用** |
| **② DeepSeek JSON Output** | `response_format={'type': 'json_object'}` API 参数 | 输出格式可靠 | 与 LangChain 工具 strict 校验冲突 | ⚠ 需配合纯 API 调用 |
| **③ LangGraph 原生参数** | 传入 Pydantic 模型 | 类型安全，自动校验 | 仅部分模型支持 | ❌ DeepSeek 不支持 |

#### 3.7.4 DeepSeek JSON Output 的正确打开方式

DeepSeek 官方推荐的 JSON Output 方式是通过 OpenAI 兼容 API 直接调用，**不通过 LangChain 封装**：

```python
from openai import OpenAI

client = OpenAI(
    api_key="<your api key>",
    base_url="https://api.deepseek.com",
)

response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {"role": "system", "content": "请以 JSON 格式输出天气信息。"},
        {"role": "user", "content": "北京的天气怎么样？"},
    ],
    response_format={"type": "json_object"},  # ← DeepSeek 原生支持
)

print(response.choices[0].message.content)
# 输出：{"city": "北京", "conditions": "晴朗", "temperature": "25°C"}
```

**关键注意事项：**

1. **Prompt 中必须包含 "json" 字样** — DeepSeek API 要求 prompt 中显式出现 "json" 关键字，否则可能不会触发 JSON 模式
2. **给出格式示例** — 提供 Few-shot 示例可以显著提高格式遵从度
3. **设置合理的 max_tokens** — 防止长 JSON 被截断
4. **处理空 content** — API 有概率返回空 content，需在代码中做防御性处理

#### 3.7.5 为什么本项目不直接使用 DeepSeek JSON Output？

当我们在 `create_json_llm()` 中通过 `model_kwargs` 启用 JSON Output 时，遇到了新的错误：

```
ValueError: `get_weather` is not strict.
Only `strict` function tools can be auto-parsed
```

**原因：** OpenAI Python 客户端在启用 `response_format` 后，会自动启用工具调用的 **strict 模式**（严格参数校验）。这要求所有工具函数必须声明为 strict，否则客户端拒绝调用。

**影响：** 在 LangGraph 的 `create_react_agent` 框架内，工具是通过 LangChain 的 Tool 对象传入的，无法简单地为工具标记 `strict=True`。

**结论：** 对于 LangGraph + DeepSeek 的组合：

| 使用场景 | 推荐方式 |
|----------|----------|
| 在 LangGraph Agent 内部 | **Prompt 引导**（方案①） |
| 直接 API 调用，不经过 Agent 框架 | **DeepSeek JSON Output**（方案②） |
| 使用 OpenAI / Anthropic 等模型 | **LangGraph 原生 `response_format`**（方案③） |

#### 3.7.6 代码变更记录

| 版本 | 变更 | 结果 |
|------|------|------|
| 初始实现 | 使用 `response_format=WeatherResponse`（Pydantic 模型） | ❌ HTTP 400 |
| 第一次修复 | 改用纯 Prompt 引导，无 API 参数 | ✅ 可工作，但格式偶有不稳 |
| 第二次尝试 | 启用 `model_kwargs={"response_format": {"type": "json_object"}}` | ❌ strict 工具校验冲突 |
| **最终方案** | 保留 Prompt 引导 + 笔记中附 DeepSeek JSON Output 示例 | ✅ **稳定可靠** |

---

## 4. 运行项目

### 4.1 前提条件

- Python 3.10+
- 已配置 API 密钥（已填入 `.env` 文件）

### 4.2 安装依赖

```bash
cd langgraph_demo
pip install -r requirements.txt
```

### 4.3 运行全部步骤

```bash
python main.py
```

程序会按顺序执行四个步骤，每步之间会暂停，按回车继续。

### 4.4 运行单个步骤

```bash
python main.py 1    # 仅运行步骤 1（基础 Agent）
python main.py 2    # 仅运行步骤 2（自定义提示）
python main.py 3    # 仅运行步骤 3（带记忆）
python main.py 4    # 仅运行步骤 4（结构化输出）
```

### 4.5 预期输出示例

**步骤 1（基础 Agent）：**
```
👤 用户: what is the weather in San Francisco?
🤖 Agent: ☀️ It's always sunny in San Francisco!
```

![](C:\Users\action_10\Desktop\ScreenShot_2026-07-28_110157_415.png)

**步骤 2（自定义提示）：**
![](C:\Users\action_10\Desktop\ScreenShot_2026-07-28_110215_406.png)

将用户输入进行修改，再执行：

```python
user_message = "what is the weather in Tokyo?"
# 修改为
user_message = "what is the weather ?"
```

![](C:\Users\action_10\Desktop\ScreenShot_2026-07-28_110240_114.png)

**步骤 3（带记忆的多轮对话）：**

```
👤 [第1轮] 用户: 你好！我叫张三，是一名软件工程师。
🤖 [第1轮] Agent: 你好，张三！很高兴认识你！作为一名软件工程师，...

👤 [第2轮] 用户: 还记得我的名字和职业吗？
🤖 [第2轮] Agent: 当然记得！你是张三，是一名软件工程师。...
```

![](C:\Users\action_10\Desktop\wechat_longscreenshot_2026-07-28_110313_369.png)

**步骤 4（结构化输出 JSON Output）：**

![](C:\Users\action_10\Desktop\wechat_longscreenshot_2026-07-28_110328_645.png)

---

## 5. 常见问题与扩展建议

### 5.1 常见问题

**Q: 为什么用 DeepSeek 而不是 OpenAI/Anthropic？**
A: DeepSeek 提供兼容 OpenAI 格式的 API，且在中国大陆可直接访问，无需特殊网络环境。使用 `ChatOpenAI` 客户端设置 `base_url` 即可调用。

**Q: 如何切换其他模型？**
A: 只需修改 `.env` 文件中的三个配置：
```env
DEEPSEEK_API_KEY=your_new_key
DEEPSEEK_BASE_URL=https://api.another-provider.com
DEEPSEEK_MODEL=model-name
```

**Q: `create_react_agent` 和 `StateGraph` 有什么区别？**
A: `create_react_agent` 是预构建的高级 API，适合标准场景；`StateGraph` 是底层 API，允许完全自定义图结构。本项目使用前者快速入门，进阶后可学习后者。

**Q: 记忆只能在内存中吗？**
A: 不。本项目使用 `MemorySaver`（内存存储）方便演示，生产环境应使用 `SqliteSaver`、`PostgresSaver` 或自定义检查点器实现持久化存储。

### 5.2 扩展建议

从一个快速入门项目到一个可投入生产的系统，以下是可以逐步添加的能力：

1. **更多工具**
   - 添加搜索工具（Tavily、Bing Search）
   - 添加数据库查询工具
   - 添加 API 调用工具

2. **更复杂的状态**
   - 在 `State` 中添加自定义字段（如用户名、会话元数据）
   - 使用自定义 reducer 处理状态更新

3. **人工在环（Human-in-the-Loop）**
   - 使用 `interrupt()` 在关键步骤暂停 Agent
   - 等待人工审批后再继续执行

4. **流式输出**
   - 使用 `stream()` 替代 `invoke()` 实现逐 token 输出
   - 提供更好的用户体验

5. **多 Agent 协作**
   - 多个 Specialist Agent 各司其职
   - Supervisor Agent 负责任务分发和结果汇总

6. **监控与可观测性**
   - 集成 LangSmith 跟踪调用链
   - 监控 token 消耗和响应延迟

### 5.3 安全提醒

- ⚠ API 密钥是敏感信息，**永远不要**提交到 Git 仓库
- ⚠ 本项目使用的 DeepSeek Key 已在对话中明文展示，建议使用后**立即在 DeepSeek 控制台重置**
- ⚠ 生产环境中应使用密钥管理服务（如 AWS Secrets Manager、Vault 等）

---

## 总结

通过本项目和配套笔记，我们完成了一个从零开始的 LangGraph Agent 学习之旅：

| 维度 | 从... | 到... |
|------|-------|-------|
| 项目结构 | 零散脚本 | 三层架构工程 |
| 代码组织 | 一个文件 | 配置/模型/工具/业务逻辑分离 |
| Agent 能力 | 简单 LLM 调用 | 工具调用 + 记忆 + 结构化输出 |
| 理解深度 | 只知道 create_react_agent | 知道每一步的原理和必要性 |

这不仅是一个 Demo，更是一个**可扩展的工程模板**。当你需要添加新功能时，遵循"在哪一层做什么事"的原则，代码自然保持清晰和可维护。
