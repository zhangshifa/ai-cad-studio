"""3D 打印机适配器：OctoPrint REST API 与串口直连两种方式。"""
from pathlib import Path

import requests

from app.config import config


def _octo():
    p = config.data["printer"]
    url = (p.get("octoprint_url") or "").rstrip("/")
    key = p.get("octoprint_api_key") or ""
    if not url or not key:
        raise RuntimeError("未配置 OctoPrint 地址或 API Key，请在设置中填写。")
    return url, {"X-Api-Key": key}


def octoprint_status() -> str:
    try:
        url, headers = _octo()
        r = requests.get(f"{url}/api/printer", headers=headers, timeout=15)
        if r.status_code == 409:
            return "OctoPrint 已连接，但打印机未连接（409）。"
        if r.status_code != 200:
            return f"OctoPrint 返回错误 {r.status_code}: {r.text[:300]}"
        data = r.json()
        state = data.get("state", {}).get("text", "未知")
        temps = data.get("temperature", {})
        tool = temps.get("tool0", {})
        bed = temps.get("bed", {})
        return (f"打印机状态: {state}\n"
                f"喷头温度: {tool.get('actual', '?')}°C / 目标 {tool.get('target', '?')}°C\n"
                f"热床温度: {bed.get('actual', '?')}°C / 目标 {bed.get('target', '?')}°C")
    except requests.RequestException as e:
        return f"无法连接 OctoPrint: {e}"
    except RuntimeError as e:
        return str(e)


def octoprint_upload_and_print(gcode_path: str, start_print: bool = False) -> str:
    gp = Path(gcode_path)
    if not gp.exists():
        return f"错误：找不到 G-code 文件：{gcode_path}"
    try:
        url, headers = _octo()
        with open(gp, "rb") as f:
            r = requests.post(
                f"{url}/api/files/local",
                headers=headers,
                files={"file": (gp.name, f, "application/octet-stream")},
                data={"select": "true", "print": "true" if start_print else "false"},
                timeout=120,
            )
        if r.status_code in (200, 201):
            action = "并已开始打印" if start_print else "（未开始打印，可手动确认后打印）"
            return f"已上传 {gp.name} 到 OctoPrint {action}。"
        return f"上传失败 {r.status_code}: {r.text[:300]}"
    except requests.RequestException as e:
        return f"无法连接 OctoPrint: {e}"
    except RuntimeError as e:
        return str(e)


def serial_send_gcode(gcode_lines, port: str = "", baud: int = 0) -> str:
    """通过串口向打印机逐行发送 G-code（适合少量控制指令，如回原点、预热）。"""
    try:
        import serial  # pyserial
    except ImportError:
        return "错误：未安装 pyserial，请执行 pip install pyserial。"

    p = config.data["printer"]
    port = port or p.get("serial_port", "COM3")
    baud = int(baud or p.get("baud_rate", 115200))
    if isinstance(gcode_lines, str):
        gcode_lines = [l for l in gcode_lines.splitlines() if l.strip()]
    if len(gcode_lines) > 200:
        return "错误：串口模式单次最多发送 200 行 G-code；大文件请使用 OctoPrint 上传。"

    try:
        import time
        with serial.Serial(port, baud, timeout=10) as ser:
            time.sleep(2)  # 等待打印机复位
            ser.reset_input_buffer()
            replies = []
            for line in gcode_lines:
                ser.write((line.strip() + "\n").encode("ascii", errors="ignore"))
                resp = ser.readline().decode(errors="replace").strip()
                replies.append(f"{line.strip()} -> {resp or '(无响应)'}")
            return f"已通过 {port}@{baud} 发送 {len(gcode_lines)} 行 G-code：\n" + \
                "\n".join(replies[-20:])
    except serial.SerialException as e:
        return f"串口错误（{port}）: {e}"
