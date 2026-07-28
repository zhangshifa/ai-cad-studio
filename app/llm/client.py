"""LLM 客户端：同时支持 OpenAI 兼容协议与 Anthropic 原生协议。

内部统一使用 OpenAI 消息格式，Anthropic 协议在发送前转换。
"""
import json

import requests


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(self, provider_type: str, base_url: str, api_key: str,
                 model: str, temperature: float = 0.3, timeout: int = 120):
        self.provider_type = provider_type  # "openai" | "anthropic"
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    # ------------------------------------------------------------------
    def chat(self, messages: list, tools: list | None = None) -> dict:
        """发送对话请求。

        返回统一结构：
        {"content": str, "tool_calls": [{"id","name","arguments":dict}]}
        """
        if not self.base_url:
            raise LLMError("未配置 Base URL，请在设置中填写。")
        if self.provider_type == "anthropic":
            return self._chat_anthropic(messages, tools)
        return self._chat_openai(messages, tools)

    def test_connection(self) -> str:
        """测试连通性，返回模型回复文本。"""
        resp = self.chat([{"role": "user", "content": "你好，请回复“连接成功”。"}])
        return resp.get("content") or "(空回复)"

    # ---------------- OpenAI 兼容 ----------------
    def _chat_openai(self, messages, tools):
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        if tools:
            payload["tools"] = tools
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        except requests.RequestException as e:
            raise LLMError(f"网络请求失败: {e}") from e
        if r.status_code != 200:
            raise LLMError(f"API 错误 {r.status_code}: {r.text[:500]}")
        data = r.json()
        try:
            msg = data["choices"][0]["message"]
        except (KeyError, IndexError) as e:
            raise LLMError(f"响应格式异常: {json.dumps(data)[:300]}") from e

        tool_calls = []
        for tc in msg.get("tool_calls") or []:
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            tool_calls.append({
                "id": tc.get("id", ""),
                "name": tc["function"]["name"],
                "arguments": args,
            })
        return {"content": msg.get("content") or "", "tool_calls": tool_calls,
                "assistant_message": msg}

    # ---------------- Anthropic ----------------
    def _chat_anthropic(self, messages, tools):
        url = f"{self.base_url}/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        system_text, conv = self._to_anthropic_messages(messages)
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": self.temperature,
            "messages": conv,
        }
        if system_text:
            payload["system"] = system_text
        if tools:
            payload["tools"] = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"].get("description", ""),
                    "input_schema": t["function"].get("parameters", {"type": "object"}),
                }
                for t in tools
            ]
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        except requests.RequestException as e:
            raise LLMError(f"网络请求失败: {e}") from e
        if r.status_code != 200:
            raise LLMError(f"API 错误 {r.status_code}: {r.text[:500]}")
        data = r.json()

        content_text = ""
        tool_calls = []
        for block in data.get("content", []):
            if block.get("type") == "text":
                content_text += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append({
                    "id": block.get("id", ""),
                    "name": block.get("name", ""),
                    "arguments": block.get("input", {}) or {},
                })
        # 构造 OpenAI 风格的 assistant 消息以便统一存储
        assistant_message = {"role": "assistant", "content": content_text}
        if tool_calls:
            assistant_message["tool_calls"] = [
                {"id": tc["id"], "type": "function",
                 "function": {"name": tc["name"],
                              "arguments": json.dumps(tc["arguments"], ensure_ascii=False)}}
                for tc in tool_calls
            ]
        return {"content": content_text, "tool_calls": tool_calls,
                "assistant_message": assistant_message}

    @staticmethod
    def _to_anthropic_messages(messages):
        """OpenAI 消息格式 -> Anthropic 格式"""
        system_parts = []
        conv = []
        for m in messages:
            role = m.get("role")
            if role == "system":
                system_parts.append(m.get("content", ""))
            elif role == "user":
                conv.append({"role": "user", "content": m.get("content", "")})
            elif role == "assistant":
                blocks = []
                if m.get("content"):
                    blocks.append({"type": "text", "text": m["content"]})
                for tc in m.get("tool_calls") or []:
                    try:
                        args = json.loads(tc["function"].get("arguments") or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    blocks.append({
                        "type": "tool_use",
                        "id": tc.get("id", ""),
                        "name": tc["function"]["name"],
                        "input": args,
                    })
                conv.append({"role": "assistant", "content": blocks or ""})
            elif role == "tool":
                conv.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": m.get("tool_call_id", ""),
                        "content": str(m.get("content", "")),
                    }],
                })
        return "\n".join(p for p in system_parts if p), conv
