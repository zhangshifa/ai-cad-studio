"""Blender 适配器：blender.exe --background --python script.py"""
from app.config import config
from app.adapters.script_runner import run_script_with_exe


def run_script(script: str, timeout: int = 300) -> str:
    exe = config.data["software"].get("blender_path", "")
    return run_script_with_exe(
        exe,
        lambda path: ["--background", "--python", path],
        script,
        timeout=timeout,
        software_name="Blender",
    )
