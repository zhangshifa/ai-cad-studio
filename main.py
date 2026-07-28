"""AI CAD Studio 入口

AI 连接自动化设计工具：通过 AI 控制 AutoCAD / Blender / FreeCAD / 切片软件 / 3D 打印机。
"""
import sys


def main():
    from PySide6.QtWidgets import QApplication
    from app.ui.styles import DARK_QSS
    from app.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("AI CAD Studio")
    app.setStyleSheet(DARK_QSS)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
