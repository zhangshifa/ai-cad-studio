"""本地 Web 服务：提供操作界面与建模 API（标准库实现，零额外 Web 依赖）。

接口：
- GET  /                → 操作界面（web/index.html）
- GET  /api/config      → 返回当前配置（密钥做掩码，不回传明文）
- POST /api/config      → 保存配置（api_key / base_url / model 等）
- POST /api/generate    → 自然语言建模：{prompt} → {code, stl, step, used_demo}
"""


import base64
import json
import os
import re
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

from ai_cad import config as cfg_mod
from ai_cad import ai_client
from ai_cad import generator
from ai_cad import prompts
from ai_cad import examples


# 项目根与前端目录
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(ROOT, "web")


def extract_code(text: str) -> str:
    """从模型回复中提取首个 python 代码块；若没有代码块则原样返回。"""
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


class Handler(BaseHTTPRequestHandler):
    server_version = "AICAD/0.1"

    # ---------- 响应辅助 ----------
    def _send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, ctype):
        try:
            with open(path, "rb") as f:
                body = f.read()
        except FileNotFoundError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---------- 路由 ----------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path in ("/", "/index.html"):
            self._send_file(os.path.join(WEB_DIR, "index.html"), "text/html; charset=utf-8")
        elif path == "/api/config":
            c = cfg_mod.load_config()
            key = c.get("api_key", "")
            masked = (key[:4] + "****" + key[-4:]) if len(key) > 8 else ("****" if key else "")
            self._send_json({
                "api_key_set": bool(key),
                "api_key_masked": masked,
                "base_url": c.get("base_url"),
                "model": c.get("model"),
            })
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            data = {}
        if path == "/api/generate":
            self._handle_generate(data)
        elif path == "/api/config":
            self._handle_config(data)
        else:
            self.send_error(404)

    # ---------- 处理：配置 ----------
    def _handle_config(self, data):
        c = cfg_mod.load_config()
        for k in ("base_url", "model", "timeout", "max_tokens"):
            if k in data and data[k] is not None:
                c[k] = data[k]
        if data.get("api_key"):
            c["api_key"] = data["api_key"]
        cfg_mod.save_config(c)
        self._send_json({"ok": True})

    # ---------- 处理：建模 ----------
    def _handle_generate(self, data):
        prompt = (data.get("prompt") or "").strip()
        if not prompt:
            self._send_json({"error": "请输入建模描述。"}, 400)
            return
        cfg = cfg_mod.load_config()

        # 未配置密钥时进入演示模式（使用示例代码）
        if not cfg.get("api_key"):
            code = examples.demo_code(prompt)
            used_demo = True
        else:
            try:
                raw = ai_client.chat(prompt, prompts.SYSTEM_PROMPT, cfg)
                code = extract_code(raw)
                used_demo = False
            except Exception as e:
                self._send_json({"error": f"AI 调用失败：{e}"}, 500)
                return

        # 执行代码并导出
        try:
            shape = generator.run_code(code)
            stl = generator.export_stl(shape)
            step = generator.export_step(shape)
        except Exception as e:
            self._send_json(
                {"error": f"几何生成失败：{e}", "code": code, "used_demo": used_demo},
                400,
            )
            return

        self._send_json({
            "code": code,
            "used_demo": used_demo,
            "stl": base64.b64encode(stl).decode("ascii"),
            "step": base64.b64encode(step).decode("ascii") if step else None,
        })

    # 关闭默认访问日志，保持终端干净
    def log_message(self, fmt, *args):
        pass


def main(host="127.0.0.1", port=8000):
    """启动本地服务。"""
    server = HTTPServer((host, port), Handler)
    print(f"AI-CAD 已启动：请在浏览器打开 http://{host}:{port}")
    print("（首次使用可在界面右上角“设置”中填写 DeepSeek API Key；未填写时使用演示模式）")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
