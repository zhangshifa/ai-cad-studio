"""内置示例库：未配置 AI 密钥时，根据关键词返回一段可用的 cadquery 代码，
让用户在配置密钥前就能看到建模→预览→导出 的完整链路。
"""


# 默认示例：带六个均布螺栓孔的法兰盘
FLANGE_EXAMPLE = '''
import cadquery as cq
# 一个带六个均布螺栓孔的法兰盘
model = (
    cq.Workplane("XY")
    .circle(30).extrude(6)            # 主体圆盘，厚度 6mm
    .faces(">Z").workplane()
    .hole(12)                          # 中心孔
    .polarArray(22, 0, 360, 6)         # 圆周均布 6 个
    .hole(4.5)                         # 螺栓孔
)
'''

# 齿轮示例：圆盘 + 圆周均布轮齿（用拉伸矩形近似）
GEAR_EXAMPLE = '''
import cadquery as cq
# 简易直齿轮：轮缘 + 均布轮齿 + 中心孔
teeth = 12
r_in = 20          # 齿根半径
r_out = 25         # 齿顶半径
base = cq.Workplane("XY").circle(r_in).extrude(8)
for i in range(teeth):
    ang = 360.0 / teeth * i
    tooth = (
        cq.Workplane("XY")
        .rect(6, (r_out - r_in) + 4)
        .extrude(8)
        .translate((0, (r_in + r_out) / 2, 0))
        .rotate((0, 0, 0), (0, 0, 1), ang)
    )
    base = base.union(tooth)
model = base.faces(">Z").workplane().hole(8)
'''

# 杯子示例：圆柱壳（抽壳），演示曲面/薄壁
CUP_EXAMPLE = '''
import cadquery as cq
# 一个带底的圆杯（外壁 + 抽壳）
model = (
    cq.Workplane("XY")
    .circle(25).extrude(60)          # 实体圆柱
    .shell(2)                         # 壁厚 2mm，掏空内部
)
'''


def demo_code(prompt):
    """根据自然语言关键词挑选示例；无匹配时返回默认法兰。"""
    p = (prompt or "").lower()
    if "齿轮" in p or "gear" in p:
        return GEAR_EXAMPLE
    if "杯" in p or "cup" in p or "杯子" in p:
        return CUP_EXAMPLE
    return FLANGE_EXAMPLE
