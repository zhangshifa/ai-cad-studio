"""通用外部脚本执行器：供 Blender / FreeCAD 适配器复用。"""
import subprocess
import tempfile
from pathlib import Path


def run_script_with_exe(exe_path: str, exe_args_builder, script_code: str,
                        suffix: str = ".py", timeout: int = 300,
                        software_name: str = "外部软件") -> str:
    """把脚本写入临时文件后用外部程序执行。

    exe_args_builder: fn(script_path) -> [args...]
    """
    if not exe_path:
        return (f"错误：未配置 {software_name} 可执行文件路径。"
                f"请在“设置 → 软件路径”中填写。")
    if not Path(exe_path).exists():
        return f"错误：找不到 {software_name} 程序：{exe_path}"

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8")
    try:
        tmp.write(script_code)
        tmp.close()
        cmd = [exe_path] + exe_args_builder(tmp.name)
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
                encoding="utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            return f"错误：{software_name} 执行超时（>{timeout}s）。"
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        status = "成功" if proc.returncode == 0 else f"失败（退出码 {proc.returncode}）"
        parts = [f"{software_name} 执行{status}。"]
        if out:
            parts.append(f"--- 标准输出 ---\n{out[-3000:]}")
        if err:
            parts.append(f"--- 错误输出 ---\n{err[-2000:]}")
        return "\n".join(parts)
    finally:
        try:
            Path(tmp.name).unlink(missing_ok=True)
        except Exception:
            pass
