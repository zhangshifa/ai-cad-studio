"""设置对话框：AI 模型（提供商/API Key/模型/测试连接）、软件路径、3D 打印。"""
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QTabWidget, QWidget, QComboBox, QLineEdit,
                               QPushButton, QLabel, QSpinBox, QFileDialog,
                               QDoubleSpinBox, QDialogButtonBox)

from app.config import config, PROVIDERS
from app.llm.client import LLMClient, LLMError


class TestThread(QThread):
    ok = Signal(str)
    fail = Signal(str)

    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client

    def run(self):
        try:
            reply = self.client.test_connection()
            self.ok.emit(reply[:120])
        except LLMError as e:
            self.fail.emit(str(e)[:300])
        except Exception as e:
            self.fail.emit(f"{type(e).__name__}: {e}")


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置 - AI CAD Studio")
        self.resize(620, 520)
        self._test_thread = None
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        # ---- Tab 1: AI 模型 ----
        tab1 = QWidget()
        f1 = QFormLayout(tab1)
        f1.setSpacing(12)
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(list(PROVIDERS.keys()))
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("API Base URL")
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("sk-…")
        self.show_key_btn = QPushButton("显示")
        self.show_key_btn.setFixedWidth(56)
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.toggled.connect(
            lambda c: self.api_key_edit.setEchoMode(
                QLineEdit.Normal if c else QLineEdit.Password))
        key_row = QHBoxLayout()
        key_row.addWidget(self.api_key_edit, 1)
        key_row.addWidget(self.show_key_btn)
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.rounds_spin = QSpinBox()
        self.rounds_spin.setRange(1, 50)

        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self._test_connection)
        self.test_result = QLabel("")
        self.test_result.setWordWrap(True)

        f1.addRow("AI 提供商", self.provider_combo)
        f1.addRow("Base URL", self.base_url_edit)
        f1.addRow("API Key", key_row)
        f1.addRow("模型", self.model_combo)
        f1.addRow("温度", self.temp_spin)
        f1.addRow("最大工具轮数", self.rounds_spin)
        f1.addRow("", self.test_btn)
        f1.addRow("", self.test_result)
        self.tabs.addTab(tab1, "🤖 AI 模型")

        # ---- Tab 2: 软件路径 ----
        tab2 = QWidget()
        f2 = QFormLayout(tab2)
        f2.setSpacing(12)
        note = QLabel("AutoCAD 通过 COM 自动连接，无需配置路径（需已安装完整版并建议先启动）。")
        note.setWordWrap(True)
        note.setStyleSheet("color: #9aa3b5;")
        f2.addRow(note)
        self.blender_edit = self._path_row(f2, "Blender 路径", "blender.exe")
        self.freecad_edit = self._path_row(f2, "FreeCAD 路径", "FreeCADCmd.exe")
        self.slicer_edit = self._path_row(
            f2, "切片软件路径", "prusa-slicer-console.exe / CuraEngine.exe")
        self.profile_edit = self._path_row(
            f2, "切片配置文件", "config.ini / printer.def.json", any_file=True)
        self.output_edit = self._path_row(f2, "输出目录", "默认 ~/ai-cad-studio-output",
                                          is_dir=True)
        self.tabs.addTab(tab2, "🛠 软件路径")

        # ---- Tab 3: 3D 打印 ----
        tab3 = QWidget()
        f3 = QFormLayout(tab3)
        f3.setSpacing(12)
        self.octo_url_edit = QLineEdit()
        self.octo_url_edit.setPlaceholderText("http://localhost:5000")
        self.octo_key_edit = QLineEdit()
        self.octo_key_edit.setEchoMode(QLineEdit.Password)
        self.serial_port_edit = QLineEdit()
        self.serial_port_edit.setPlaceholderText("COM3")
        self.baud_spin = QSpinBox()
        self.baud_spin.setRange(9600, 1000000)
        self.baud_spin.setSingleStep(9600)
        f3.addRow("OctoPrint 地址", self.octo_url_edit)
        f3.addRow("OctoPrint API Key", self.octo_key_edit)
        f3.addRow("串口号", self.serial_port_edit)
        f3.addRow("波特率", self.baud_spin)
        self.tabs.addTab(tab3, "🖨 3D 打印")

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Save).setText("保存")
        btns.button(QDialogButtonBox.Cancel).setText("取消")
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _path_row(self, form, label, placeholder, is_dir=False, any_file=False):
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        btn = QPushButton("浏览…")
        btn.setFixedWidth(70)

        def browse():
            if is_dir:
                p = QFileDialog.getExistingDirectory(self, f"选择{label}")
            else:
                flt = "所有文件 (*.*)" if any_file else "可执行文件 (*.exe);;所有文件 (*.*)"
                p, _ = QFileDialog.getOpenFileName(self, f"选择{label}", "", flt)
            if p:
                edit.setText(p)

        btn.clicked.connect(browse)
        row = QHBoxLayout()
        row.addWidget(edit, 1)
        row.addWidget(btn)
        form.addRow(label, row)
        return edit

    # ---------------- 数据 ----------------
    def _load(self):
        self.provider_combo.setCurrentText(config.provider)
        self._on_provider_changed(config.provider, initial=True)
        self.temp_spin.setValue(config.data.get("temperature", 0.3))
        self.rounds_spin.setValue(config.data.get("max_agent_rounds", 10))
        sw = config.data["software"]
        self.blender_edit.setText(sw.get("blender_path", ""))
        self.freecad_edit.setText(sw.get("freecad_path", ""))
        self.slicer_edit.setText(sw.get("slicer_path", ""))
        self.profile_edit.setText(sw.get("slicer_profile", ""))
        self.output_edit.setText(sw.get("output_dir", ""))
        pr = config.data["printer"]
        self.octo_url_edit.setText(pr.get("octoprint_url", ""))
        self.octo_key_edit.setText(pr.get("octoprint_api_key", ""))
        self.serial_port_edit.setText(pr.get("serial_port", "COM3"))
        self.baud_spin.setValue(int(pr.get("baud_rate", 115200)))

    def _on_provider_changed(self, name, initial=False):
        info = PROVIDERS.get(name, {})
        saved_url = config.data.get("base_urls", {}).get(name, "")
        self.base_url_edit.setText(saved_url or info.get("base_url", ""))
        self.api_key_edit.setText(config.data.get("api_keys", {}).get(name, ""))
        self.model_combo.clear()
        self.model_combo.addItems(info.get("models", []))
        if initial and config.model:
            self.model_combo.setCurrentText(config.model)
        elif info.get("models"):
            self.model_combo.setCurrentIndex(0)

    def _test_connection(self):
        info = PROVIDERS.get(self.provider_combo.currentText(), {})
        client = LLMClient(
            provider_type=info.get("type", "openai"),
            base_url=self.base_url_edit.text().strip(),
            api_key=self.api_key_edit.text().strip(),
            model=self.model_combo.currentText().strip(),
            timeout=30,
        )
        self.test_btn.setEnabled(False)
        self.test_result.setStyleSheet("color: #9aa3b5;")
        self.test_result.setText("正在测试连接…")
        self._test_thread = TestThread(client)
        self._test_thread.ok.connect(self._test_ok)
        self._test_thread.fail.connect(self._test_fail)
        self._test_thread.finished.connect(lambda: self.test_btn.setEnabled(True))
        self._test_thread.start()

    def _test_ok(self, reply):
        self.test_result.setStyleSheet("color: #58d68d;")
        self.test_result.setText(f"✅ 连接成功：{reply}")

    def _test_fail(self, err):
        self.test_result.setStyleSheet("color: #ec7063;")
        self.test_result.setText(f"❌ 连接失败：{err}")

    def _save(self):
        provider = self.provider_combo.currentText()
        config.data["provider"] = provider
        config.data["model"] = self.model_combo.currentText().strip()
        config.data.setdefault("api_keys", {})[provider] = \
            self.api_key_edit.text().strip()
        base_url = self.base_url_edit.text().strip()
        default_url = PROVIDERS.get(provider, {}).get("base_url", "")
        config.data.setdefault("base_urls", {})[provider] = \
            "" if base_url == default_url else base_url
        config.data["temperature"] = self.temp_spin.value()
        config.data["max_agent_rounds"] = self.rounds_spin.value()
        sw = config.data["software"]
        sw["blender_path"] = self.blender_edit.text().strip()
        sw["freecad_path"] = self.freecad_edit.text().strip()
        sw["slicer_path"] = self.slicer_edit.text().strip()
        sw["slicer_profile"] = self.profile_edit.text().strip()
        sw["output_dir"] = self.output_edit.text().strip()
        pr = config.data["printer"]
        pr["octoprint_url"] = self.octo_url_edit.text().strip()
        pr["octoprint_api_key"] = self.octo_key_edit.text().strip()
        pr["serial_port"] = self.serial_port_edit.text().strip()
        pr["baud_rate"] = self.baud_spin.value()
        config.save()
        self.accept()
