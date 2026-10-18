"""启动入口：把项目根加入模块搜索路径后启动本地 Web 服务。

用法：
    python run.py            # 默认 127.0.0.1:8000
    python run.py 8080       # 自定义端口

建议使用本项目自带的 venv（已安装 cadquery）：
    venv\\Scripts\\python.exe run.py
"""


import os
import sys


# 将项目根目录加入搜索路径，确保能 import ai_cad
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_cad.server import main


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    main(port=port)
