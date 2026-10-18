"""几何生成模块：在受限命名空间内执行 AI 产出的 cadquery 代码，并导出 STL/STEP。

安全说明：
- 执行 AI 生成的代码存在风险，这里做了最小化收敛：
  1) 仅保留必需的内置函数；
  2) 重写 __import__，只允许导入白名单模块（cadquery / math / numpy）；
  3) 几何导出写到临时文件后立即删除，不落地业务数据。
- 本工具定位为本地单用户使用，仍建议仅在可信网络下运行。
"""


import builtins
import os
import tempfile


# 允许导入的模块白名单（其余一律禁止）
_ALLOWED_MODULES = {"cadquery", "math", "numpy"}


def _safe_import(name, *args, **kwargs):
    """受控导入：仅放行白名单内的顶层模块。"""
    if name.split(".")[0] not in _ALLOWED_MODULES:
        raise ImportError(f"出于安全考虑，禁止导入模块：{name}")
    return builtins.__import__(name, *args, **kwargs)


def _build_namespace():
    """构造受限执行命名空间，预置 cadquery 与 math。"""
    import cadquery as cq

    ns_builtins = {
        "abs": abs, "min": min, "max": max, "round": round, "len": len,
        "range": range, "enumerate": enumerate, "float": float, "int": int,
        "str": str, "list": list, "dict": dict, "tuple": tuple, "zip": zip,
        "sum": sum, "pow": pow, "sorted": sorted, "bool": bool, "set": set,
        "print": print,
        "Exception": Exception, "ValueError": ValueError,
        "TypeError": TypeError, "ImportError": ImportError, "RuntimeError": RuntimeError,
        "__import__": _safe_import,
    }
    return {"__builtins__": ns_builtins, "cq": cq, "math": __import__("math")}


def run_code(code: str):
    """执行代码并返回 cadquery 形状对象。

    :param code: Python 源码（应使用 cadquery，并把最终模型赋值给 model）
    :return: cadquery.Shape 对象
    :raises ValueError/RuntimeError: 代码为空或未定义 model
    """
    if not code or not code.strip():
        raise ValueError("代码为空，无法执行。")
    ns = _build_namespace()
    # 在受限命名空间中执行
    exec(code, ns)
    model = ns.get("model")
    if model is None:
        raise RuntimeError("生成的代码未定义变量 model（最终模型）。")
    # Workplane → 底层几何对象
    if hasattr(model, "val"):
        shape = model.val()
    else:
        shape = model
    return shape


def _export_to_bytes(shape, fmt: str) -> bytes:
    """借助 cadquery 导出器把形状写出为字节（先写临时文件再读回）。"""
    import cadquery as cq

    fd, path = tempfile.mkstemp(suffix="." + fmt.lower())
    os.close(fd)
    try:
        cq.exporters.export(shape, path, fmt.upper())
        with open(path, "rb") as f:
            return f.read()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def export_stl(shape) -> bytes:
    """导出 STL（二进制/ASCII，供 3D 打印切片软件使用）。"""
    return _export_to_bytes(shape, "STL")


def export_step(shape):
    """导出 STEP（CAD 互换格式，供 SolidWorks/Fusion 等打开）；不支持时返回 None。"""
    try:
        return _export_to_bytes(shape, "STEP")
    except Exception:
        return None
