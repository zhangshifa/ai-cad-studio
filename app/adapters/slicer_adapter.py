"""切片适配器：调用 PrusaSlicer 或 CuraEngine 命令行把 STL 切成 G-code。"""
import subprocess
from pathlib import Path

from app.config import config


def slice_stl(stl_path: str, output_gcode: str = "", timeout: int = 600) -> str:
    exe = config.data["software"].get("slicer_path", "")
    profile = config.data["software"].get("slicer_profile", "")

    if not exe:
        return "错误：未配置切片软件路径（PrusaSlicer / CuraEngine），请在设置中填写。"
    if not Path(exe).exists():
        return f"错误：找不到切片程序：{exe}"
    stl = Path(stl_path)
    if not stl.exists():
        return f"错误：找不到 STL 文件：{stl_path}"

    if not output_gcode:
        output_gcode = str(Path(config.output_dir) / (stl.stem + ".gcode"))
    Path(output_gcode).parent.mkdir(parents=True, exist_ok=True)

    exe_name = Path(exe).name.lower()
    if "cura" in exe_name:
        # CuraEngine slice -j <def.json> -l <stl> -o <gcode>
        if not profile:
            return "错误：CuraEngine 需要打印机定义文件(.def.json)，请在设置的“切片配置”中填写。"
        cmd = [exe, "slice", "-j", profile, "-l", str(stl), "-o", output_gcode]
    else:
        # PrusaSlicer（含 prusa-slicer-console.exe）
        cmd = [exe, "--export-gcode", str(stl), "--output", output_gcode]
        if profile:
            cmd += ["--load", profile]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return f"错误：切片超时（>{timeout}s）。"

    if proc.returncode == 0 and Path(output_gcode).exists():
        size_kb = Path(output_gcode).stat().st_size // 1024
        return f"切片成功：{output_gcode}（{size_kb} KB）"
    return (f"切片失败（退出码 {proc.returncode}）。\n"
            f"输出: {(proc.stdout or '')[-1500:]}\n错误: {(proc.stderr or '')[-1500:]}")
