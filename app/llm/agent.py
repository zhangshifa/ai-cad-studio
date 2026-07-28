"""工具调用 Agent 循环：模型 -> tool_calls -> 执行软件适配器 -> 回传结果 -> 循环"""
import json

from app.llm.client import LLMClient, LLMError
from app.tools.registry import get_tool_schemas, execute_tool

SYSTEM_PROMPT = """你是 AI CAD Studio 的设计自动化助手，运行在用户的 Windows 电脑上。
你可以通过工具直接控制以下软件，帮助用户完成制图、建模、切片与 3D 打印任务：

1. AutoCAD —— COM 自动化：画线/圆/多段线/矩形/文字、图层、任意命令与 AutoLISP、查询图元、保存图纸。
2. Blender —— 后台执行 bpy Python 脚本（建模、材质、渲染）。
3. FreeCAD —— 后台执行 FreeCAD Python 脚本（参数化建模、导出 STEP/STL）。
4. 切片软件 —— PrusaSlicer / CuraEngine 将 STL 切片为 G-code。
5. 3D 打印机 —— OctoPrint API 上传并打印，或串口直接发送 G-code。

工作准则：
- 优先使用专用工具；复杂 AutoCAD 操作可用 autocad_send_command 发送命令或 AutoLISP。
- 写 Blender/FreeCAD 脚本时代码必须完整可独立运行，输出文件保存到用户输出目录。
- 尺寸单位默认毫米(mm)。绘图前如有需要可创建图层。
- 执行有风险或不可逆的操作（覆盖文件、开始打印）前，先向用户确认。
- 工具执行失败时，分析错误原因，修正后重试（最多重试 2 次），仍失败则如实告知用户并给出解决建议。
- 用简体中文回复，简洁清晰地汇报做了什么、结果如何。"""


class Agent:
    """同步 Agent，可在工作线程中运行。通过回调向 UI 汇报进度。"""

    def __init__(self, client: LLMClient, max_rounds: int = 10,
                 on_status=None, on_tool_start=None, on_tool_end=None):
        self.client = client
        self.max_rounds = max_rounds
        self.on_status = on_status or (lambda s: None)
        self.on_tool_start = on_tool_start or (lambda name, args: None)
        self.on_tool_end = on_tool_end or (lambda name, result: None)
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def reset(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def run(self, user_text: str) -> str:
        """执行一轮用户请求，返回最终回复文本。"""
        self.messages.append({"role": "user", "content": user_text})
        tools = get_tool_schemas()

        for round_no in range(1, self.max_rounds + 1):
            self.on_status(f"正在思考（第 {round_no} 轮）…")
            try:
                resp = self.client.chat(self.messages, tools)
            except LLMError as e:
                raise
            self.messages.append(resp["assistant_message"])

            if not resp["tool_calls"]:
                return resp["content"] or "(模型未返回内容)"

            for tc in resp["tool_calls"]:
                self.on_tool_start(tc["name"], tc["arguments"])
                try:
                    result = execute_tool(tc["name"], tc["arguments"])
                except Exception as e:  # 适配器异常兜底
                    result = f"工具执行异常: {type(e).__name__}: {e}"
                result_str = result if isinstance(result, str) else json.dumps(
                    result, ensure_ascii=False)
                # 截断超长结果，避免撑爆上下文
                if len(result_str) > 6000:
                    result_str = result_str[:6000] + "\n...(结果已截断)"
                self.on_tool_end(tc["name"], result_str)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result_str,
                })

        return "已达到最大工具调用轮数，任务可能未完全完成。请检查结果或继续下达指令。"
