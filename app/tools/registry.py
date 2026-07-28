"""工具注册表：定义 Function Calling schema，并把调用分发到各软件适配器。"""
from app.config import config


def _schema(name, description, properties=None, required=None):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties or {},
                "required": required or [],
            },
        },
    }


_NUM = {"type": "number"}
_STR = {"type": "string"}

TOOL_SCHEMAS = [
    # ---------------- AutoCAD ----------------
    _schema("autocad_draw_line", "在 AutoCAD 模型空间绘制一条直线（单位 mm）",
            {"x1": _NUM, "y1": _NUM, "x2": _NUM, "y2": _NUM,
             "layer": {"type": "string", "description": "可选图层名"}},
            ["x1", "y1", "x2", "y2"]),
    _schema("autocad_draw_circle", "在 AutoCAD 绘制圆",
            {"cx": _NUM, "cy": _NUM, "radius": _NUM, "layer": _STR},
            ["cx", "cy", "radius"]),
    _schema("autocad_draw_polyline", "在 AutoCAD 绘制二维多段线",
            {"points": {"type": "array", "description": "点列表 [[x,y],...]",
                        "items": {"type": "array", "items": _NUM}},
             "closed": {"type": "boolean", "description": "是否闭合"},
             "layer": _STR},
            ["points"]),
    _schema("autocad_draw_rectangle", "在 AutoCAD 绘制矩形（左下角+宽高）",
            {"x": _NUM, "y": _NUM, "width": _NUM, "height": _NUM, "layer": _STR},
            ["x", "y", "width", "height"]),
    _schema("autocad_add_text", "在 AutoCAD 添加单行文字",
            {"x": _NUM, "y": _NUM, "text": _STR,
             "height": {"type": "number", "description": "字高，默认 2.5"},
             "layer": _STR},
            ["x", "y", "text"]),
    _schema("autocad_create_layer", "在 AutoCAD 创建图层",
            {"name": _STR,
             "color_index": {"type": "integer",
                             "description": "ACI 颜色索引 1红 2黄 3绿 4青 5蓝 6洋红 7白"}},
            ["name"]),
    _schema("autocad_send_command",
            "向 AutoCAD 命令行发送原生命令或 AutoLISP 表达式，适合标注、填充、块等复杂操作",
            {"command": {"type": "string",
                         "description": "命令文本，如 'DIMLINEAR ' 或 '(command \"_.zoom\" \"_e\")'"}},
            ["command"]),
    _schema("autocad_list_entities", "列出 AutoCAD 模型空间中的图元",
            {"limit": {"type": "integer", "description": "最多列出数量，默认 50"}}),
    _schema("autocad_zoom_extents", "AutoCAD 缩放到全图范围"),
    _schema("autocad_save_as", "保存 AutoCAD 图纸到指定路径(.dwg)",
            {"file_path": _STR}, ["file_path"]),

    # ---------------- Blender ----------------
    _schema("blender_run_script",
            "在 Blender 后台执行 bpy Python 脚本（建模/材质/渲染/导出）。脚本必须完整可独立运行。",
            {"script": {"type": "string", "description": "完整的 bpy Python 脚本"},
             "description": {"type": "string", "description": "脚本用途简述"}},
            ["script"]),

    # ---------------- FreeCAD ----------------
    _schema("freecad_run_script",
            "在 FreeCAD 控制台模式执行 Python 脚本（参数化建模、导出 STEP/STL/DXF）。",
            {"script": {"type": "string", "description": "完整的 FreeCAD Python 脚本"},
             "description": _STR},
            ["script"]),

    # ---------------- 切片 ----------------
    _schema("slicer_slice_stl", "用配置的切片软件(PrusaSlicer/CuraEngine)把 STL 切片为 G-code",
            {"stl_path": _STR,
             "output_gcode": {"type": "string", "description": "可选输出路径，默认输出目录"}},
            ["stl_path"]),

    # ---------------- 3D 打印 ----------------
    _schema("printer_octoprint_status", "查询 OctoPrint 打印机状态与温度"),
    _schema("printer_octoprint_upload", "上传 G-code 到 OctoPrint，可选立即开始打印",
            {"gcode_path": _STR,
             "start_print": {"type": "boolean",
                             "description": "是否立即开始打印（有风险，需用户确认后才可为 true）"}},
            ["gcode_path"]),
    _schema("printer_serial_send", "通过串口向 3D 打印机发送少量 G-code 指令（≤200 行）",
            {"gcode": {"type": "string", "description": "G-code 文本，换行分隔"},
             "port": {"type": "string", "description": "可选串口号，默认取配置"},
             "baud": {"type": "integer", "description": "可选波特率，默认取配置"}},
            ["gcode"]),

    # ---------------- 环境 ----------------
    _schema("get_workspace_info", "查询当前输出目录与已配置的软件路径，写脚本前可先调用"),
]


def get_tool_schemas():
    return TOOL_SCHEMAS


def execute_tool(name: str, args: dict) -> str:
    """分发执行。适配器模块按需导入，避免启动时加载 COM。"""
    args = args or {}

    if name.startswith("autocad_"):
        from app.adapters import autocad_adapter as ac
        try:
            if name == "autocad_draw_line":
                return ac.draw_line(args["x1"], args["y1"], args["x2"], args["y2"],
                                    args.get("layer", ""))
            if name == "autocad_draw_circle":
                return ac.draw_circle(args["cx"], args["cy"], args["radius"],
                                      args.get("layer", ""))
            if name == "autocad_draw_polyline":
                return ac.draw_polyline(args["points"], args.get("closed", False),
                                        args.get("layer", ""))
            if name == "autocad_draw_rectangle":
                return ac.draw_rectangle(args["x"], args["y"], args["width"],
                                         args["height"], args.get("layer", ""))
            if name == "autocad_add_text":
                return ac.add_text(args["x"], args["y"], args["text"],
                                   args.get("height", 2.5), args.get("layer", ""))
            if name == "autocad_create_layer":
                return ac.create_layer(args["name"], args.get("color_index", 7))
            if name == "autocad_send_command":
                return ac.send_command(args["command"])
            if name == "autocad_list_entities":
                return ac.list_entities(args.get("limit", 50))
            if name == "autocad_zoom_extents":
                return ac.zoom_extents()
            if name == "autocad_save_as":
                return ac.save_as(args["file_path"])
        except RuntimeError as e:
            return f"AutoCAD 错误: {e}"
        except Exception as e:
            return f"AutoCAD 操作失败: {type(e).__name__}: {e}"

    if name == "blender_run_script":
        from app.adapters import blender_adapter
        return blender_adapter.run_script(args["script"])

    if name == "freecad_run_script":
        from app.adapters import freecad_adapter
        return freecad_adapter.run_script(args["script"])

    if name == "slicer_slice_stl":
        from app.adapters import slicer_adapter
        return slicer_adapter.slice_stl(args["stl_path"], args.get("output_gcode", ""))

    if name == "printer_octoprint_status":
        from app.adapters import printer_adapter
        return printer_adapter.octoprint_status()

    if name == "printer_octoprint_upload":
        from app.adapters import printer_adapter
        return printer_adapter.octoprint_upload_and_print(
            args["gcode_path"], args.get("start_print", False))

    if name == "printer_serial_send":
        from app.adapters import printer_adapter
        return printer_adapter.serial_send_gcode(
            args["gcode"], args.get("port", ""), args.get("baud", 0))

    if name == "get_workspace_info":
        sw = config.data["software"]
        return (f"输出目录: {config.output_dir}\n"
                f"Blender: {sw.get('blender_path') or '未配置'}\n"
                f"FreeCAD: {sw.get('freecad_path') or '未配置'}\n"
                f"切片软件: {sw.get('slicer_path') or '未配置'}\n"
                f"切片配置: {sw.get('slicer_profile') or '未配置'}\n"
                f"OctoPrint: {config.data['printer'].get('octoprint_url') or '未配置'}")

    return f"错误：未知工具 {name}"
