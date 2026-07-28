"""聊天面板：消息气泡流 + 工具调用卡片 + 输入区，Agent 在后台线程运行。"""
import json

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                               QFrame, QLabel, QTextEdit, QPushButton,
                               QSizePolicy)

from app.config import config, PROVIDERS
from app.llm.client import LLMClient, LLMError
from app.llm.agent import Agent


class AgentThread(QThread):
    status = Signal(str)
    tool_start = Signal(str, str)   # name, args_json
    tool_end = Signal(str, str)     # name, result
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, agent: Agent, user_text: str, parent=None):
        super().__init__(parent)
        self.agent = agent
        self.user_text = user_text

    def run(self):
        self.agent.on_status = lambda s: self.status.emit(s)
        self.agent.on_tool_start = lambda n, a: self.tool_start.emit(
            n, json.dumps(a, ensure_ascii=False))
        self.agent.on_tool_end = lambda n, r: self.tool_end.emit(n, r)
        try:
            reply = self.agent.run(self.user_text)
            self.finished_ok.emit(reply)
        except LLMError as e:
            self.failed.emit(str(e))
        except Exception as e:
            self.failed.emit(f"{type(e).__name__}: {e}")


class ChatWidget(QWidget):
    busy_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.agent = None
        self.thread = None
        self._build_ui()
        self._welcome()

    # ---------------- UI ----------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.msg_container = QWidget()
        self.msg_container.setStyleSheet("background: transparent;")
        self.msg_layout = QVBoxLayout(self.msg_container)
        self.msg_layout.setContentsMargins(4, 4, 4, 4)
        self.msg_layout.setSpacing(10)
        self.msg_layout.addStretch(1)
        self.scroll.setWidget(self.msg_container)
        layout.addWidget(self.scroll, 1)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #9aa3b5; font-size: 12px;")
        layout.addWidget(self.status_label)

        input_row = QHBoxLayout()
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText(
            "向 AI 下达设计指令，例如：在 AutoCAD 里画一个 100x60 的矩形并标注尺寸…\n"
            "Ctrl+Enter 发送")
        self.input_edit.setFixedHeight(78)
        self.input_edit.installEventFilter(self)
        input_row.addWidget(self.input_edit, 1)

        btn_col = QVBoxLayout()
        self.send_btn = QPushButton("发送")
        self.send_btn.setProperty("cls", "primary")
        self.send_btn.setFixedWidth(88)
        self.send_btn.clicked.connect(self.send)
        self.clear_btn = QPushButton("新会话")
        self.clear_btn.setFixedWidth(88)
        self.clear_btn.clicked.connect(self.new_session)
        btn_col.addWidget(self.send_btn)
        btn_col.addWidget(self.clear_btn)
        input_row.addLayout(btn_col)
        layout.addLayout(input_row)

    def eventFilter(self, obj, event):
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent
        if obj is self.input_edit and event.type() == QEvent.KeyPress:
            ke: QKeyEvent = event
            if ke.key() in (Qt.Key_Return, Qt.Key_Enter) and \
                    ke.modifiers() & Qt.ControlModifier:
                self.send()
                return True
        return super().eventFilter(obj, event)

    # ---------------- 气泡 ----------------
    def _add_widget(self, w):
        self.msg_layout.insertWidget(self.msg_layout.count() - 1, w)
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))

    def _bubble(self, text: str, role: str):
        frame = QFrame()
        frame.setProperty("cls", "userBubble" if role == "user" else "aiBubble")
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(12, 9, 12, 9)
        label = QLabel(text)
        label.setProperty("cls", "bubbleText")
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if role == "user":
            label.setStyleSheet("color: white; background: transparent;")
        inner.addWidget(label)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        frame.setMaximumWidth(720)
        if role == "user":
            row.addStretch(1)
            row.addWidget(frame)
        else:
            row.addWidget(frame)
            row.addStretch(1)
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wrapper.setLayout(row)
        self._add_widget(wrapper)
        return label

    def _tool_card(self, name: str, args_json: str):
        frame = QFrame()
        frame.setProperty("cls", "toolCard")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 8, 12, 8)
        title = QLabel(f"🔧 调用工具 {name}")
        title.setProperty("cls", "toolTitle")
        body = QLabel(f"参数: {args_json[:400]}")
        body.setProperty("cls", "toolBody")
        body.setWordWrap(True)
        result_label = QLabel("⏳ 执行中…")
        result_label.setProperty("cls", "toolBody")
        result_label.setWordWrap(True)
        result_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(title)
        lay.addWidget(body)
        lay.addWidget(result_label)

        row = QHBoxLayout()
        row.setContentsMargins(24, 0, 0, 0)
        frame.setMaximumWidth(700)
        row.addWidget(frame)
        row.addStretch(1)
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wrapper.setLayout(row)
        self._add_widget(wrapper)
        return result_label

    def _welcome(self):
        self._bubble(
            "👋 你好，我是 AI CAD Studio 设计助手。\n\n"
            "我可以帮你：\n"
            "• 控制 AutoCAD 绘图、标注、管理图层\n"
            "• 用 Blender / FreeCAD 建模并导出 STL/STEP\n"
            "• 调用切片软件生成 G-code 并发送到 3D 打印机\n\n"
            "请先点击左侧「⚙ 设置」配置 AI 模型的 API Key 和软件路径，然后直接对我说需求即可。",
            "ai")

    # ---------------- 交互 ----------------
    def _make_agent(self):
        info = PROVIDERS.get(config.provider, {})
        client = LLMClient(
            provider_type=info.get("type", "openai"),
            base_url=config.base_url,
            api_key=config.api_key,
            model=config.model,
            temperature=config.data.get("temperature", 0.3),
        )
        if self.agent is None:
            self.agent = Agent(client, max_rounds=config.data.get("max_agent_rounds", 10))
        else:
            self.agent.client = client  # 保留会话历史，仅更新客户端
        return self.agent

    def new_session(self):
        if self.thread and self.thread.isRunning():
            return
        if self.agent:
            self.agent.reset()
        # 清空气泡
        while self.msg_layout.count() > 1:
            item = self.msg_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._welcome()

    def send(self):
        text = self.input_edit.toPlainText().strip()
        if not text:
            return
        if self.thread and self.thread.isRunning():
            return
        if not config.api_key and config.provider != "Ollama (本地)":
            self._bubble("⚠ 尚未配置 API Key，请先打开左侧「⚙ 设置」填写。", "ai")
            return

        self.input_edit.clear()
        self._bubble(text, "user")
        agent = self._make_agent()

        self.thread = AgentThread(agent, text)
        self.thread.status.connect(self.status_label.setText)
        self.thread.tool_start.connect(self._on_tool_start)
        self.thread.tool_end.connect(self._on_tool_end)
        self.thread.finished_ok.connect(self._on_done)
        self.thread.failed.connect(self._on_error)
        self.thread.finished.connect(lambda: self._set_busy(False))
        self._set_busy(True)
        self._current_tool_label = None
        self.thread.start()

    def _set_busy(self, busy: bool):
        self.send_btn.setEnabled(not busy)
        self.clear_btn.setEnabled(not busy)
        if not busy:
            self.status_label.setText("")
        self.busy_changed.emit(busy)

    def _on_tool_start(self, name, args_json):
        self.status_label.setText(f"正在执行工具 {name} …")
        self._current_tool_label = self._tool_card(name, args_json)

    def _on_tool_end(self, name, result):
        if self._current_tool_label is not None:
            short = result if len(result) <= 800 else result[:800] + " …"
            self._current_tool_label.setText(f"✅ 结果: {short}")
            self._current_tool_label = None

    def _on_done(self, reply):
        self._bubble(reply, "ai")

    def _on_error(self, err):
        self._bubble(f"❌ 出错了：{err}", "ai")
