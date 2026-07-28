"""
=============================================
配置层 · config.py
=============================================

【职责】
  本模块相当于 Java 三层架构中的 "配置管理" 层，
  负责从环境变量读取配置参数，集中管理所有可调参数。

【为什么需要】
  1. 将 API 密钥、模型名、URL 等敏感/可变信息从业务代码中抽离
  2. 一处修改，全局生效
  3. 方便切换不同环境（开发/测试/生产）

【对应关系】
  Java 三层架构 -> 本项目的对应
  - application.yml / application.properties -> app/config.py
"""

import os
from dotenv import load_dotenv

# -------------------------------------------------------------------
# 加载 .env 文件中的环境变量（不会覆盖系统已存在的环境变量）
# -------------------------------------------------------------------
load_dotenv()


# ===================================================================
# 核心配置常量
# ===================================================================

# DeepSeek API 配置
# DeepSeek 提供完全兼容 OpenAI 格式的 API，因此使用 ChatOpenAI 客户端访问
DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
"""DeepSeek API 密钥，从环境变量读取"""

DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
"""DeepSeek API 基础地址"""

DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
"""使用的 DeepSeek 模型名称（可选：deepseek-v4-flash / deepseek-v4-pro）"""

# ===================================================================
# 模型参数配置
# ===================================================================

DEFAULT_TEMPERATURE: float = 0.0
"""
模型温度参数 (0.0 ~ 2.0)
- 0.0: 输出最确定、最保守
- 1.0: 输出较有创造性
- 2.0: 输出最具随机性
"""

DEFAULT_MAX_TOKENS: int = 2048
"""每次生成的最大 token 数"""


def validate_config() -> bool:
    """
    验证配置是否完整有效。

    在程序启动时调用此函数，可以及早发现配置问题，
    避免运行时才报错（Fail-Fast 原则）。

    Returns:
        True 表示配置有效，False 表示缺少必要配置
    """
    if not DEEPSEEK_API_KEY:
        print("⚠ 错误：未设置 DEEPSEEK_API_KEY")
        print("  请在 .env 文件中配置或设置环境变量")
        return False
    return True
