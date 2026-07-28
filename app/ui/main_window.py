"""主窗口：左侧边栏（模型选择/适配器状态/设置）+ 右侧聊天面板。"""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                               QLabel, QComboBox, QPushButton, QFrame)

from app import __version__
from app.config import config, PROVIDERS
from app.ui.chat_widget import ChatWidget
from app.ui.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"AI CAD Studio v{__version__} — AI 连接自动化设计工具")
        self.resize(1180, 760)
        self._build_ui()
        self._refresh_sidebar()

    def _build_ui(self):
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---------- 侧边栏 ----------
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(260)
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(16, 18, 16, 16)
        sl.setSpacing(8)

        logo = QLabel("⚡ AI CAD Studio")
        logo.setObjectName("LogoLabel")
        subtitle = QLabel("AI 连接自动化设计工具")
        subtitle.setObjectName("SubtitleLabel")
        sl.addWidget(logo)
        sl.addWidget(subtitle)
        sl.addSpacing(8)

        t1 = QLabel("AI 模型")
        t1.setProperty("cls", "sectionTitle")
        sl.addWidget(t1)
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(list(PROVIDERS.keys()))
        self.provider_combo.currentTextChanged.connect(self._on_provider_change)
        sl.addWidget(self.provider_combo)
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.currentTextChanged.connect(self._on_model_change)
        sl.addWidget(self.model_combo)
        self.key_status = QLabel("")
        self.key_status.setStyleSheet("font-size: 11px;")
        sl.addWidget(self.key_status)

        t2 = QLabel("软件适配器")
        t2.setProperty("cls", "sectionTitle")
        sl.addWidget(t2)
        self.adapter_labels = {}
        for key, name in [("autocad", "AutoCAD (COM)"),
                          ("blender", "Blender"),
                          ("freecad", "FreeCAD"),
                          ("slicer", "切片软件"),
                          ("printer", "3D 打印机")]:
            lbl = QLabel(f"○ {name}")
            lbl.setStyleSheet("color: #9aa3b5; font-size: 12px;")
            self.adapter_labels[key] = (lbl, name)
            sl.addWidget(lbl)

        sl.addStretch(1)
        settings_btn = QPushButton("⚙ 设置")
        settings_btn.clicked.connect(self.open_settings)
        sl.addWidget(settings_btn)
        ver = QLabel(f"v{__version__} · MIT License")
        ver.setStyleSheet("color: #5b6270; font-size: 11px;")
        ver.setAlignment(Qt.AlignCenter)
        sl.addWidget(ver)

        # ---------- 聊天区 ----------
        self.chat = ChatWidget()
        self.chat.busy_changed.connect(
            lambda b: self.statusBar().showMessage("AI 正在工作…" if b else "就绪"))

        root.addWidget(sidebar)
        root.addWidget(self.chat, 1)
        self.setCentralWidget(central)
        self.statusBar().showMessage("就绪")

    # ---------------- 侧边栏逻辑 ----------------
    def _refresh_sidebar(self):
        self._loading = True
        self.provider_combo.setCurrentText(config.provider)
        self.model_combo.clear()
        self.model_combo.addItems(PROVIDERS.get(config.provider, {}).get("models", []))
        if config.model:
            self.model_combo.setCurrentText(config.model)
        self._loading = False
        self._refresh_status()

    def _refresh_status(self):
        if config.api_key:
            self.key_status.setText("🔑 API Key 已配置")
            self.key_status.setStyleSheet("color: #58d68d; font-size: 11px;")
        else:
            self.key_status.setText("⚠ 未配置 API Key（点击下方设置）")
            self.key_status.setStyleSheet("color: #f5b041; font-size: 11px;")

        sw = config.data["software"]
        pr = config.data["printer"]
        states = {
            "autocad": True,  # COM 即用型，标记为可用（运行时检测）
            "blender": bool(sw.get("blender_path")) and Path(sw["blender_path"]).exists(),
            "freecad": bool(sw.get("freecad_path")) and Path(sw["freecad_path"]).exists(),
            "slicer": bool(sw.get("slicer_path")) and Path(sw["slicer_path"]).exists(),
            "printer": bool(pr.get("octoprint_api_key")) or bool(pr.get("serial_port")),
        }
        for key, (lbl, name) in self.adapter_labels.items():
            if states.get(key):
                lbl.setText(f"● {name}")
                lbl.setStyleSheet("color: #58d68d; font-size: 12px;")
            else:
                lbl.setText(f"○ {name}（未配置）")
                lbl.setStyleSheet("color: #9aa3b5; font-size: 12px;")

    def _on_provider_change(self, name):
        if getattr(self, "_loading", False):
            return
        config.data["provider"] = name
        models = PROVIDERS.get(name, {}).get("models", [])
        self._loading = True
        self.model_combo.clear()
        self.model_combo.addItems(models)
        self._loading = False
        if models:
            config.data["model"] = models[0]
        config.save()
        self._refresh_status()

    def _on_model_change(self, model):
        if getattr(self, "_loading", False) or not model.strip():
            return
        config.data["model"] = model.strip()
        config.save()

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self._refresh_sidebar()
