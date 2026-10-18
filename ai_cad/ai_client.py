"""AI 客户端：调用兼容 OpenAI 的对话接口（默认 DeepSeek）。

设计要点：
- 不依赖第三方 HTTP 库，使用标准库 urllib。
- 接口地址与模型可在配置中替换（例如指向本地或第三方兼容服务）。
- 仅使用环境变量或配置文件中的密钥，不内置任何密钥。
"""


import json
import urllib.error
import urllib.request


def chat(user_prompt: str, system_prompt: str, config: dict) -> str:
    """向大模型发起一次对话，返回模型文本。

    :param user_prompt: 用户的自然语言建模描述
    :param system_prompt: 系统提示词（约束输出为 cadquery 代码）
    :param config: 配置字典（含 api_key / base_url / model / timeout / max_tokens）
    :return: 模型返回的文本内容
    """
    api_key = config.get("api_key")
    if not api_key:
        raise RuntimeError(
            "未配置 API Key：请在界面“设置”中填写，或设置环境变量 DEEPSEEK_API_KEY。"
        )

    base_url = (config.get("base_url") or "https://api.deepseek.com").rstrip("/")
    model = config.get("model") or "deepseek-chat"
    timeout = int(config.get("timeout") or 120)
    max_tokens = int(config.get("max_tokens") or 2000)

    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,   # 偏低温度，保证代码稳定
        "max_tokens": max_tokens,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")
        raise RuntimeError(f"AI 接口返回错误 {e.code}：{detail[:300]}")
    except Exception as e:  # 网络/超时等
        raise RuntimeError(f"AI 接口请求失败：{e}")

    try:
        return result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"AI 返回格式异常：{e}")
