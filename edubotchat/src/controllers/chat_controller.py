# src/controllers/chat_controller.py
import sys
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QScrollArea, QLabel, QFrame
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from src.controllers.base_controller import BaseController
from src.api.ai_service import AIService
from google.genai import types  # Dùng cho định nghĩa tool schema

# ----------------------------------------------------------------------
# Worker thread để gọi AI (có thể call tool)
# ----------------------------------------------------------------------
class BotWorker(QThread):
    """Chạy gọi API Gemini trong thread riêng, hỗ trợ tool calling."""
    response_ready = pyqtSignal(str)           # Dùng cho response text thường
    tool_call_request = pyqtSignal(str, dict)  # (tool_name, arguments)

    def __init__(self, user_text: str, subject: str, history: list, tools_def: list):
        super().__init__()
        self.user_text = user_text
        self.subject = subject
        self.history = history
        self.tools_def = tools_def

    def run(self):
        ai = AIService()
        response = ai.chat_with_tools(
            user_message=self.user_text,
            tools_def=self.tools_def,
            subject=self.subject,
            history=self.history
        )

        if response is None:
            self.response_ready.emit("Xin lỗi, đã có lỗi kết nối AI. Vui lòng thử lại sau.")
            return

        # Kiểm tra xem AI có yêu cầu gọi tool không
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                part = candidate.content.parts[0]
                if hasattr(part, 'function_call') and part.function_call is not None:
                    func = part.function_call
                    tool_name = func.name
                    tool_args = {}
                    if func.args:
                        tool_args = {k: v for k, v in func.args.items()}
                    self.tool_call_request.emit(tool_name, tool_args)
                    return

        # Nếu không có tool call, lấy text response
        try:
            reply = response.text
        except Exception:
            reply = "Rất tiếc, tôi không thể xử lý yêu cầu này. Vui lòng thử lại."
        self.response_ready.emit(reply.strip())


# ----------------------------------------------------------------------
# ChatController – quản lý giao diện chat và tích hợp AI Agent
# ----------------------------------------------------------------------
class ChatController(BaseController):
    new_session_created = pyqtSignal(str)

    def __init__(self, main_window=None):
        # FIX: Khởi tạo các biến instance TRƯỚC khi gọi super().__init__()
        # để setup_ui() và connect_signals() (được gọi bên trong super) có thể dùng chúng.
        self.UI_FILE = ""  # Không dùng file .ui
        self.main_window = main_window
        self._chat_history = []
        self._typing_container = None
        self._current_bot_worker = None

        # FIX: Chỉ gọi super().__init__() – BaseController sẽ tự gọi
        # setup_ui() và connect_signals() đúng một lần.
        # KHÔNG gọi self.setup_ui() hay self.connect_signals() thêm nữa.
        super().__init__()

        self._append_message("👋 Xin chào! Tôi là trợ lý học tập. Bạn có thể nhờ tôi tạo lịch trình học tập hoặc roadmap cho bất kỳ môn học nào.", is_user=False)

    # ------------------------------------------------------------------
    # Định nghĩa tools cho Gemini
    # ------------------------------------------------------------------
    def get_tools_definitions(self):
        """Trả về danh sách tool (FunctionDeclaration) dùng trong chat_with_tools."""
        # Tool tạo lịch trình học tập
        create_schedule_tool = types.FunctionDeclaration(
            name="create_learning_schedule",
            description="Tạo một lịch trình học tập chi tiết cho một chủ đề nhất định.",
            parameters={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Chủ đề cần học, ví dụ: Python, Machine Learning."},
                    "level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"], "description": "Trình độ người học."},
                    "duration_weeks": {"type": "integer", "description": "Thời lượng lộ trình (tuần). Mặc định 4."},
                    "hours_per_week": {"type": "integer", "description": "Số giờ học mỗi tuần. Mặc định 5."}
                },
                "required": ["topic", "level"]
            }
        )

        # Tool tạo roadmap (yêu cầu AI trả về danh sách topics)
        generate_roadmap_tool = types.FunctionDeclaration(
            name="generate_learning_roadmap",
            description="Tạo lộ trình học tập dạng mốc các chủ đề chính. Hãy trả về danh sách các chủ đề với tên, trạng thái (done/in_progress/locked) và mô tả chi tiết.",
            parameters={
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "Tên môn học, ví dụ: Python."},
                    "level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"], "description": "Trình độ mong muốn."},
                    "topics": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "status": {"type": "string", "enum": ["done", "in_progress", "locked"]},
                                "detail": {"type": "string"}
                            },
                            "required": ["name", "status"]
                        }
                    }
                },
                "required": ["subject", "topics"]
            }
        )

        return types.Tool(function_declarations=[create_schedule_tool, generate_roadmap_tool])

    # ------------------------------------------------------------------
    # Xây dựng giao diện chat (thay vì dùng .ui)
    # ------------------------------------------------------------------
    def setup_ui(self):
        """Tạo các widget cho khung chat."""
        # FIX: Bỏ đoạn xóa layout cũ – không cần thiết vì setup_ui()
        # chỉ được gọi đúng một lần bởi BaseController.__init__().
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(10)

        # Khu vực hiển thị tin nhắn (dạng scroll)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #f8f9fa; }")

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(12)
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_area.setWidget(self.messages_container)
        self.main_layout.addWidget(self.scroll_area, 1)

        # Khung nhập liệu
        input_frame = QFrame()
        input_frame.setStyleSheet("QFrame { background-color: white; border-radius: 8px; border: 1px solid #dee2e6; }")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 5, 10, 5)

        self.chat_input = QTextEdit()
        self.chat_input.setPlaceholderText("Nhập yêu cầu của bạn...")
        self.chat_input.setMaximumHeight(100)
        self.chat_input.setStyleSheet("QTextEdit { border: none; font-size: 14px; }")
        input_layout.addWidget(self.chat_input, 1)

        self.send_btn = QPushButton("Gửi")
        self.send_btn.setFixedSize(60, 35)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a6cf7;
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3a5ce5; }
            QPushButton:pressed { background-color: #2a4cb5; }
        """)
        input_layout.addWidget(self.send_btn)

        self.clear_btn = QPushButton("Xóa")
        self.clear_btn.setFixedSize(60, 35)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5a6268; }
        """)
        input_layout.addWidget(self.clear_btn)

        self.main_layout.addWidget(input_frame)

    def connect_signals(self):
        self.send_btn.clicked.connect(self._send_message)
        self.clear_btn.clicked.connect(self._clear_chat)

    def refresh(self):
        """Làm mới trang chat (yêu cầu từ main.py)."""
        pass

    # ------------------------------------------------------------------
    # Xử lý gửi tin nhắn và nhận phản hồi
    # ------------------------------------------------------------------
    def _send_message(self):
        text = self.chat_input.toPlainText().strip()
        if not text:
            return

        self._append_message(text, is_user=True)
        self.chat_input.clear()
        self._chat_history.append({"role": "user", "content": text})
        self._show_typing_indicator()

        subject = ""
        if self.main_window and hasattr(self.main_window, 'subject_combo'):
            subject = self.main_window.subject_combo.currentText()

        tools = self.get_tools_definitions()
        self._current_bot_worker = BotWorker(
            user_text=text,
            subject=subject,
            history=self._chat_history.copy(),
            tools_def=[tools]
        )
        self._current_bot_worker.response_ready.connect(self._handle_ai_response)
        self._current_bot_worker.tool_call_request.connect(self._handle_tool_call)
        self._current_bot_worker.start()

    def _handle_ai_response(self, reply: str):
        self._remove_typing()
        self._append_message(reply, is_user=False)
        self._chat_history.append({"role": "assistant", "content": reply})
        self._current_bot_worker = None

    def _handle_tool_call(self, tool_name: str, tool_args: dict):
        self._remove_typing()

        if tool_name == "create_learning_schedule":
            if self.main_window and hasattr(self.main_window, 'planner'):
                planner = self.main_window.planner
                if hasattr(planner, 'create_learning_schedule'):
                    schedule = planner.create_learning_schedule(**tool_args)
                    display_text = self._format_schedule(schedule)
                    self._append_message(display_text, is_user=False)
                    self._chat_history.append({"role": "assistant", "content": display_text})
                else:
                    self._append_message("⚠️ Lỗi: Không tìm thấy chức năng tạo lịch trình trong Planner.", is_user=False)
            else:
                self._append_message("⚠️ Lỗi hệ thống: không thể kết nối với Planner.", is_user=False)

        elif tool_name == "generate_learning_roadmap":
            if self.main_window and hasattr(self.main_window, 'roadmap'):
                roadmap_ctrl = self.main_window.roadmap
                if hasattr(roadmap_ctrl, 'add_roadmap_from_ai'):
                    subject = tool_args.get("subject", "Môn học mới")
                    level = tool_args.get("level", "beginner")
                    topics_data = tool_args.get("topics", [])
                    if not topics_data:
                        topics_data = [
                            {"name": f"Nhập môn {subject}", "status": "in_progress", "detail": "Các khái niệm cơ bản"},
                            {"name": f"{subject} nâng cao", "status": "locked", "detail": "Chủ đề chuyên sâu"}
                        ]
                    roadmap_ctrl.add_roadmap_from_ai(subject, level, topics_data)
                    self._append_message(f"✅ Đã tạo lộ trình cho môn **{subject}** (trình độ {level}). Hãy xem trong tab **Lộ Trình**!", is_user=False)
                    self._chat_history.append({"role": "assistant", "content": f"✅ Đã tạo lộ trình cho môn {subject}."})
                else:
                    self._append_message("⚠️ Lỗi: RoadmapController chưa có chức năng thêm lộ trình từ AI.", is_user=False)
            else:
                self._append_message("⚠️ Lỗi hệ thống: không thể kết nối với Roadmap.", is_user=False)
        else:
            self._append_message(f"⚠️ Tôi chưa được huấn luyện để thực hiện tác vụ '{tool_name}'.", is_user=False)

        self._current_bot_worker = None

    # ------------------------------------------------------------------
    # Định dạng hiển thị
    # ------------------------------------------------------------------
    def _format_schedule(self, schedule: dict) -> str:
        if not schedule:
            return "Không thể tạo lịch trình. Vui lòng thử lại."
        topic = schedule.get('topic', 'Chủ đề')
        level = schedule.get('level', 'beginner')
        duration = schedule.get('duration_weeks', 4)
        hours = schedule.get('hours_per_week', 5)

        text = f"**📅 Lịch trình học {topic}**\n\n"
        text += f"- **Cấp độ:** {level}\n- **Thời lượng:** {duration} tuần\n- **Mỗi tuần:** {hours} giờ\n\n"
        for week in schedule.get('weeks', []):
            text += f"**Tuần {week['week']}:** {week.get('focus', '')}\n"
            for task in week.get('tasks', []):
                text += f"  - {task}\n"
            text += "\n"
        if 'notes' in schedule:
            text += f"📌 *Ghi chú:* {schedule['notes']}\n"
        return text

    def _format_roadmap(self, roadmap: dict) -> str:
        if not roadmap:
            return "Không thể tạo roadmap. Vui lòng thử lại."
        subject = roadmap.get('subject', 'Môn học')
        level = roadmap.get('level', 'beginner')
        text = f"**🗺️ Lộ trình học {subject}** (Trình độ: {level})\n\n"
        for idx, topic in enumerate(roadmap.get('topics', []), 1):
            status_icon = "✅" if topic.get('status') == "done" else "🔄" if topic.get('status') == "in_progress" else "🔒"
            text += f"{idx}. {status_icon} **{topic.get('name', '')}**\n"
            if 'detail' in topic:
                text += f"   *{topic['detail']}*\n"
        return text

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------
    def _append_message(self, message: str, is_user: bool = False):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        bubble = QLabel(message)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble.setMaximumWidth(500)
        bubble.setStyleSheet("padding: 10px; border-radius: 12px; font-size: 14px; font-family: 'Segoe UI', Arial, sans-serif;")
        if is_user:
            bubble.setStyleSheet(bubble.styleSheet() + "background-color: #e9ecef; color: black;")
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            bubble.setStyleSheet(bubble.styleSheet() + "background-color: #4a6cf7; color: white;")
            layout.addWidget(bubble)
            layout.addStretch()

        self.messages_layout.addWidget(container)
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def _show_typing_indicator(self):
        self._typing_container = QWidget()
        layout = QHBoxLayout(self._typing_container)
        layout.setContentsMargins(10, 5, 10, 5)
        typing_label = QLabel("🤖 AI đang suy nghĩ...")
        typing_label.setStyleSheet("color: #6c757d; font-style: italic;")
        layout.addWidget(typing_label)
        layout.addStretch()
        self.messages_layout.addWidget(self._typing_container)
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def _remove_typing(self):
        if hasattr(self, '_typing_container') and self._typing_container is not None:
            self._typing_container.deleteLater()
            self._typing_container = None

    def _clear_chat(self):
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._chat_history.clear()
        self._append_message("🧹 Đã xóa toàn bộ tin nhắn. Bạn cần tôi hỗ trợ gì không?", is_user=False)
        self.new_session_created.emit("Chat mới")

    def set_main_window(self, main_window):
        self.main_window = main_window

    def get_widget(self):
        return self