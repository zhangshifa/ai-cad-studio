"""FreeCAD 适配器：FreeCADCmd.exe script.py（无 GUI 控制台模式）"""
from app.config import config
from app.adapters.script_runner import run_script_with_exe


def run_script(script: str, timeout: int = 300) -> str:
    exe = config.data["software"].get("freecad_path", "")
    return run_script_with_exe(
        exe,
        lambda path: [path],
        script,
        timeout=timeout,
        software_name="FreeCAD",
    )
