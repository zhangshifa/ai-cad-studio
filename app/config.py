"""配置管理：API Key、模型、软件路径等，存储于 %USERPROFILE%/.ai-cad-studio/config.json"""
import json
import os
from pathlib import Path

CONFIG_DIR = Path(os.path.expanduser("~")) / ".ai-cad-studio"
CONFIG_FILE = CONFIG_DIR / "config.json"

# 内置 AI 提供商预设（均可在设置中修改 Base URL / 模型）
PROVIDERS = {
    "OpenAI": {
        "type": "openai",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "o3-mini"],
    },
    "DeepSeek": {
        "type": "openai",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"],
    },
    "Moonshot Kimi": {
        "type": "openai",
        "base_url": "https://api.moonshot.cn/v1",
        "models": ["kimi-k2-0711-preview", "moonshot-v1-8k", "moonshot-v1-32k"],
    },
    "智谱 GLM": {
        "type": "openai",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4-plus", "glm-4-air", "glm-4-flash"],
    },
    "Anthropic Claude": {
        "type": "anthropic",
        "base_url": "https://api.anthropic.com",
        "models": ["claude-sonnet-4-20250514", "claude-3-7-sonnet-20250219", "claude-3-5-haiku-20241022"],
    },
    "Ollama (本地)": {
        "type": "openai",
        "base_url": "http://localhost:11434/v1",
        "models": ["llama3.1", "qwen2.5", "qwen2.5-coder"],
    },
    "自定义 (OpenAI 兼容)": {
        "type": "openai",
        "base_url": "",
        "models": [],
    },
}

DEFAULT_CONFIG = {
    "provider": "DeepSeek",
    "model": "deepseek-chat",
    "api_keys": {},          # {provider_name: api_key}
    "base_urls": {},         # 覆盖默认 base_url
    "temperature": 0.3,
    "max_agent_rounds": 10,
    "software": {
        "blender_path": "",       # blender.exe
        "freecad_path": "",       # FreeCADCmd.exe
        "slicer_path": "",        # prusa-slicer-console.exe 或 CuraEngine.exe
        "slicer_profile": "",     # 切片配置文件 (.ini / .def.json)
        "output_dir": "",         # 生成文件输出目录，默认 ~/ai-cad-studio-output
    },
    "printer": {
        "octoprint_url": "http://localhost:5000",
        "octoprint_api_key": "",
        "serial_port": "COM3",
        "baud_rate": 115200,
    },
}


class Config:
    """单例配置对象"""

    def __init__(self):
        self.data = {}
        self.load()

    def load(self):
        self.data = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
        if CONFIG_FILE.exists():
            try:
                saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                self._merge(self.data, saved)
            except Exception:
                pass

    @staticmethod
    def _merge(base, other):
        for k, v in other.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                Config._merge(base[k], v)
            else:
                base[k] = v

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ---- 便捷访问 ----
    @property
    def provider(self):
        return self.data.get("provider", "DeepSeek")

    @property
    def provider_info(self):
        return PROVIDERS.get(self.provider, PROVIDERS["自定义 (OpenAI 兼容)"])

    @property
    def api_key(self):
        return self.data.get("api_keys", {}).get(self.provider, "")

    @property
    def base_url(self):
        override = self.data.get("base_urls", {}).get(self.provider, "")
        return override or self.provider_info["base_url"]

    @property
    def model(self):
        return self.data.get("model", "")

    @property
    def output_dir(self):
        d = self.data["software"].get("output_dir") or str(
            Path(os.path.expanduser("~")) / "ai-cad-studio-output"
        )
        Path(d).mkdir(parents=True, exist_ok=True)
        return d


config = Config()
