"""AutoCAD 适配器：通过 Windows COM 自动化控制 AutoCAD。

要求：本机已安装 AutoCAD（完整版，支持 COM），建议先手动启动 AutoCAD。
"""
import sys

_acad = None


def _require_windows():
    if sys.platform != "win32":
        raise RuntimeError("AutoCAD COM 自动化仅支持 Windows。")


def _get_app():
    """连接 AutoCAD：优先附着到已运行实例，否则尝试启动新实例。"""
    global _acad
    _require_windows()
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    if _acad is not None:
        try:
            _ = _acad.Name  # 探活
            return _acad
        except Exception:
            _acad = None
    try:
        _acad = win32com.client.GetActiveObject("AutoCAD.Application")
    except Exception:
        try:
            _acad = win32com.client.Dispatch("AutoCAD.Application")
            _acad.Visible = True
        except Exception as e:
            raise RuntimeError(
                "无法连接 AutoCAD。请确认已安装完整版 AutoCAD 并先手动启动它。"
                f"（{e}）"
            ) from e
    return _acad


def _get_doc():
    app = _get_app()
    try:
        if app.Documents.Count == 0:
            app.Documents.Add()
        return app.ActiveDocument
    except Exception as e:
        raise RuntimeError(f"无法获取 AutoCAD 活动文档: {e}") from e


def _pt(x, y, z=0.0):
    """构造 COM 三维点 (VARIANT double 数组)"""
    import pythoncom
    import win32com.client
    return win32com.client.VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8, (float(x), float(y), float(z)))


def _flat_pts(points):
    """[[x,y],...] -> VARIANT 平面多段线坐标数组"""
    import pythoncom
    import win32com.client
    flat = []
    for p in points:
        flat.extend([float(p[0]), float(p[1])])
    return win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, flat)


def _set_layer(entity, layer):
    if layer:
        try:
            entity.Layer = layer
        except Exception:
            pass


# ---------------- 工具实现 ----------------

def draw_line(x1, y1, x2, y2, layer=""):
    doc = _get_doc()
    ent = doc.ModelSpace.AddLine(_pt(x1, y1), _pt(x2, y2))
    _set_layer(ent, layer)
    doc.Regen(1)
    return f"已绘制直线 ({x1},{y1}) -> ({x2},{y2})" + (f"，图层 {layer}" if layer else "")


def draw_circle(cx, cy, radius, layer=""):
    doc = _get_doc()
    ent = doc.ModelSpace.AddCircle(_pt(cx, cy), float(radius))
    _set_layer(ent, layer)
    doc.Regen(1)
    return f"已绘制圆 圆心({cx},{cy}) 半径{radius}"


def draw_polyline(points, closed=False, layer=""):
    if not points or len(points) < 2:
        return "错误：多段线至少需要 2 个点。"
    doc = _get_doc()
    ent = doc.ModelSpace.AddLightWeightPolyline(_flat_pts(points))
    if closed:
        ent.Closed = True
    _set_layer(ent, layer)
    doc.Regen(1)
    return f"已绘制多段线，共 {len(points)} 个点" + ("（闭合）" if closed else "")


def draw_rectangle(x, y, width, height, layer=""):
    pts = [[x, y], [x + width, y], [x + width, y + height], [x, y + height]]
    return draw_polyline(pts, closed=True, layer=layer) + \
        f"（矩形 {width}x{height}，左下角 ({x},{y})）"


def add_text(x, y, text, height=2.5, layer=""):
    doc = _get_doc()
    ent = doc.ModelSpace.AddText(str(text), _pt(x, y), float(height))
    _set_layer(ent, layer)
    doc.Regen(1)
    return f"已添加文字 “{text}” 于 ({x},{y})，字高 {height}"


def create_layer(name, color_index=7):
    doc = _get_doc()
    layer = doc.Layers.Add(str(name))
    try:
        layer.Color = int(color_index)
    except Exception:
        pass
    return f"已创建/获取图层 {name}（颜色索引 {color_index}）"


def send_command(command):
    """发送原生命令行指令或 AutoLISP 表达式（自动补回车）"""
    doc = _get_doc()
    cmd = command if command.endswith(("\n", "\r", " ")) else command + "\r"
    doc.SendCommand(cmd)
    return f"已发送命令: {command}"


def list_entities(limit=50):
    doc = _get_doc()
    ms = doc.ModelSpace
    total = ms.Count
    items = []
    for i in range(min(total, int(limit))):
        try:
            e = ms.Item(i)
            items.append(f"[{i}] {e.ObjectName} (图层 {e.Layer})")
        except Exception:
            items.append(f"[{i}] <读取失败>")
    return f"模型空间共 {total} 个图元：\n" + "\n".join(items)


def zoom_extents():
    app = _get_app()
    app.ZoomExtents()
    return "已缩放到图纸范围。"


def save_as(file_path):
    doc = _get_doc()
    doc.SaveAs(str(file_path))
    return f"图纸已保存到 {file_path}"
