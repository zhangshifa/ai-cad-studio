"""配置模块：加载与保存用户配置（AI 接口地址、模型、密钥等）。

安全说明：
- 配置文件 config.json 已被 .gitignore 排除，不会进入版本库。
- 优先级：环境变量 DEEPSEEK_API_KEY > config.json。
"""


import json
import os


# 项目根目录（本文件位于 ai_cad/ 下，向上一级即为根）
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(_ROOT, "config.json")

# 默认配置
DEFAULT_CONFIG = {
    "api_key": "",                       # API 密钥（也可通过环境变量提供）
    "base_url": "https://api.deepseek.com",  # 兼容 OpenAI 的接口地址
    "model": "deepseek-chat",            # 模型名
    "timeout": 120,                      # 请求超时（秒）
    "max_tokens": 2000,                  # 最大生成长度
}


def load_config():
    """加载配置：默认值 + 文件覆盖 + 环境变量覆盖。"""
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            # 文件损坏时退回默认，避免崩溃
            pass
    # 环境变量优先级最高，避免把密钥写进文件也能生效
    env_key = os.environ.get("DEEPSEEK_API_KEY")
    if env_key:
        cfg["api_key"] = env_key
    return cfg


def save_config(cfg):
    """保存用户配置到 config.json（仅保存用户可配置项）。"""
    allow = ("api_key", "base_url", "model", "timeout", "max_tokens")
    to_save = {k: cfg[k] for k in allow if k in cfg}
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(to_save, f, ensure_ascii=False, indent=2)
