"""
src/views/chat/chat_view.py
----------------------------
View trang Chat với AI – phiên bản hoàn chỉnh có tool calling.

Flow:
  User nhập → _send() → ApiWorker(QThread) → tool_call hoặc response
                      ↘ _show_typing()    ↗

Tính năng:
  - Lịch sử chat nhiều session, lưu DB
  - AI nhận context cá nhân hóa từ DBManager (tiến độ, mục tiêu, điểm yếu)
  - Gửi kèm môn học để AI phân tích đúng môn
  - Lưu toàn bộ hội thoại vào MySQL (chat_history)
  - Block gửi khi đang chờ reply, hủy worker cũ nếu có
  - Attach ảnh / file / chèn ký hiệu toán
  - Tool calling: create_learning_schedule, generate_learning_roadmap
"""

from __future__ import annotations

from datetime import datetime
from typing   import Optional

from PyQt6.QtCore    import pyqtSignal, QTimer, Qt
from PyQt6.QtWidgets import (
    QListWidgetItem, QFileDialog,
    QSizePolicy, QSpacerItem, QMessageBox,
)

from src.controllers.base_controller  import BaseController
from src.models.app_state             import AppState
from src.models.message               import Message, MessageRole
from src.models.settings              import AppSettings
from src.api.api_worker               import ApiWorker
from src.api.prompts                  import SYSTEM_CHAT
from src.views.components.chat_bubble import ChatBubble, TypingIndicator
from src.utils.study_subjects         import strip_icon

# DB (import có fallback để app vẫn chạy khi chưa có DB)
try:
    from src.database.db_manager      import DBManager
    from src.database.context_builder import build_system_prompt
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False

# Google GenAI types cho tool definition
try:
    from google.genai import types
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


# ---------------------------------------------------------------------------
# ChatView
# ---------------------------------------------------------------------------

class ChatView(BaseController):
    """Controller + View trang Chat."""

    UI_FILE = "chat_page.ui"

    # Signals ra ngoài
    new_session_created = pyqtSignal(str)   # title → Dashboard recent list
    message_sent        = pyqtSignal()       # → Dashboard stats (đếm câu hỏi)

    # ------------------------------------------------------------------ #
    #  Khởi tạo                                                           #
    # ------------------------------------------------------------------ #

    def __init__(self, settings: AppSettings, parent=None):
        self._settings = settings
        self._worker:  Optional[ApiWorker]      = None
        self._typing:  Optional[TypingIndicator] = None
        self._main_window = None
        self._chat_history = []  # lưu lịch sử dạng dict để gửi API
        super().__init__(parent)

    # ------------------------------------------------------------------ #
    #  BaseController interface                                            #
    # ------------------------------------------------------------------ #

    def setup_ui(self):
        self._state    = AppState.instance()
        self._curr_sid = self._state.current_session

        # Nếu chưa có session nào, tạo mặc định
        if not self._curr_sid:
            self._curr_sid = self._state.new_session("Chat mới")

        # Khởi tạo _chat_history từ state
        self._sync_history_from_state()

        self._populate_sessions()
        self._render_history(self._curr_sid)

    def connect_signals(self):
        # ── Sidebar ──────────────────────────────────────────────────
        self.btnNewChat.clicked.connect(self._new_session)
        self.searchSessions.textChanged.connect(self._filter_sessions)
        self.sessionsList.itemClicked.connect(self._on_session_clicked)

        # ── Gửi tin nhắn ─────────────────────────────────────────────
        self.btnSend.clicked.connect(self._send)
        self.chatInputField.keyPressEvent = self._key_press

        # ── Môn học ──────────────────────────────────────────────────
        self.subjectCombo.currentTextChanged.connect(self._on_subject_changed)

        # ── Gợi ý nhanh ──────────────────────────────────────────────
        self.suggBtn1.clicked.connect(
            lambda: self._fill("Giải thích định lý Pitago cho mình nghe")
        )
        self.suggBtn2.clicked.connect(
            lambda: self._fill("Công thức hóa học và tính chất của HCl là gì?")
        )
        self.suggBtn3.clicked.connect(
            lambda: self._fill("Luyện tập từ vựng tiếng Anh B1 theo chủ đề")
        )

        # ── Toolbar ──────────────────────────────────────────────────
        self.btnClearChat.clicked.connect(self._clear_chat)
        self.btnAttachImage.clicked.connect(self._attach_image)
        self.btnAttachFile.clicked.connect(self._attach_file)
        self.btnFormulaInput.clicked.connect(self._insert_formula)

    def refresh(self):
        self._populate_sessions()
        self._sync_history_from_state()

    def set_main_window(self, mw):
        """Giữ reference đến MainWindow (cần để gọi planner/roadmap)."""
        self._main_window = mw

    # ================================================================== #
    #  Session management                                                  #
    # ================================================================== #

    def _populate_sessions(self, filter_text: str = ""):
        """Render danh sách session vào sidebar."""
        self.sessionsList.clear()
        for sid in self._state.session_order:
            title = self._state.session_title(sid)
            if filter_text.lower() in title.lower():
                item = QListWidgetItem(f"💬  {title}")
                item.setData(Qt.ItemDataRole.UserRole, sid)
                self.sessionsList.addItem(item)

        # Highlight session đang mở
        for i in range(self.sessionsList.count()):
            item = self.sessionsList.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == self._curr_sid:
                self.sessionsList.setCurrentItem(item)
                break

    def _filter_sessions(self, text: str):
        self._populate_sessions(text)

    def _on_session_clicked(self, item: QListWidgetItem):
        sid = item.data(Qt.ItemDataRole.UserRole)
        if sid and sid != self._curr_sid:
            self._cancel_worker()
            self._curr_sid = sid
            self._state.current_session = sid
            self._sync_history_from_state()
            self._clear_messages_ui()
            self._render_history(sid)

    def _new_session(self):
        """Tạo session chat mới."""
        self._cancel_worker()
        now   = datetime.now().strftime("%d/%m %H:%M")
        title = f"Chat {now}"
        sid   = self._state.new_session(title)

        self._curr_sid              = sid
        self._state.current_session = sid
        self._sync_history_from_state()

        self._populate_sessions()
        self._clear_messages_ui()
        self.new_session_created.emit(title)

    def _sync_history_from_state(self):
        """Đồng bộ _chat_history từ AppState messages."""
        self._chat_history = []
        for msg in self._state.get_messages(self._curr_sid):
            role = "user" if msg.is_user else "assistant"
            self._chat_history.append({"role": role, "content": msg.content})

    # ================================================================== #
    #  Message rendering                                                   #
    # ================================================================== #

    def _render_history(self, sid: str):
        """Vẽ lại toàn bộ lịch sử chat của session."""
        for msg in self._state.get_messages(sid):
            self._add_bubble(msg)
        QTimer.singleShot(80, self._scroll_bottom)

    def _add_bubble(self, msg: Message):
        layout = self.messagesLayout
        self._pop_spacer(layout)
        bubble = ChatBubble(msg)
        layout.addWidget(bubble)
        self._push_spacer(layout)

    def _append_message(self, text: str, is_user: bool = False):
        """Thêm tin nhắn trực tiếp (dùng cho tool response)."""
        role = MessageRole.USER if is_user else MessageRole.ASSISTANT
        msg = self._state.add_message(self._curr_sid, role, text)
        self._add_bubble(msg)
        self._chat_history.append({"role": role.value, "content": text})
        QTimer.singleShot(50, self._scroll_bottom)

    def _show_typing(self):
        layout = self.messagesLayout
        self._pop_spacer(layout)
        self._typing = TypingIndicator()
        layout.addWidget(self._typing)
        self._push_spacer(layout)
        QTimer.singleShot(50, self._scroll_bottom)

    def _hide_typing(self):
        if self._typing:
            self._typing.setParent(None)
            self._typing.deleteLater()
            self._typing = None

    def _clear_messages_ui(self):
        """Xóa toàn bộ bubble khỏi layout (không xóa data)."""
        layout = self.messagesLayout
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    @staticmethod
    def _pop_spacer(layout):
        last = layout.count() - 1
        if last >= 0 and layout.itemAt(last).spacerItem():
            layout.removeItem(layout.itemAt(last))

    @staticmethod
    def _push_spacer(layout):
        layout.addItem(
            QSpacerItem(
                0, 0,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            )
        )

    def _scroll_bottom(self):
        sb = self.chatScrollArea.verticalScrollBar()
        sb.setValue(sb.maximum())
    #  Send / receive messages with tool calling
    def _key_press(self, event):
        from PyQt6.QtWidgets import QPlainTextEdit
        if (event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
                and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)):
            self._send()
        else:
            QPlainTextEdit.keyPressEvent(self.chatInputField, event)

    def _send(self):
        text = self.chatInputField.toPlainText().strip()
        if not text or self._worker:
            return

        subject = strip_icon(self.subjectCombo.currentText())

        msg = self._state.add_message(self._curr_sid, MessageRole.USER, text)
        self._add_bubble(msg)
        self.chatInputField.clear()
        self.btnSend.setEnabled(False)
        self.message_sent.emit()

        if _DB_AVAILABLE:
            try:
                DBManager.instance().save_chat_message(
                    role="user",
                    content=text,
                    session_name=self._state.session_title(self._curr_sid),
                )
            except Exception:
                pass

        self._show_typing()

        system = self._build_system(subject)
        tools = self.get_tools_definitions()  # Lấy tool definitions

        self._worker = ApiWorker(
            user_text=text,
            history=self._state.get_messages(self._curr_sid),
            system=system,
            subject=subject,
            api_key=self._settings.api_key,
            tools_def=[tools],   # Truyền tools vào worker
            parent=self,
        )
        self._worker.response_ready.connect(self._on_reply)
        self._worker.tool_call_request.connect(self._handle_tool_call)  # Kết nối tool call
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished_work.connect(self._on_worker_done)
        self._worker.start()

    def _build_system(self, subject: str) -> str:
        base = SYSTEM_CHAT
        # Thêm hướng dẫn ưu tiên dùng tool
        tool_instruction = (
            "\n\nQUAN TRỌNG: "
            "Nếu người dùng yêu cầu tạo lịch học, lên kế hoạch học tập, "
            "tạo lịch trình (ví dụ: 'tạo lịch học ngày hôm nay', 'lập kế hoạch học Python'), "
            "bạn PHẢI gọi tool 'create_learning_schedule'. "
            "Đừng trả lời bằng văn bản thông thường. "
            "Hãy tự động xác định duration_type='day' nếu người dùng nói 'hôm nay' hoặc 'ngày mai', "
            "ngược lại dùng 'week'."
        )
        if _DB_AVAILABLE:
            try:
                prompt = build_system_prompt(subject if subject and "Tất cả" not in subject else None)
                return prompt + tool_instruction
            except Exception:
                return base + tool_instruction
        else:
            return base + tool_instruction

    def _on_reply(self, text: str):
        self._hide_typing()
        msg = self._state.add_message(self._curr_sid, MessageRole.ASSISTANT, text)
        self._add_bubble(msg)
        if _DB_AVAILABLE:
            try:
                DBManager.instance().save_chat_message(
                    role="assistant",
                    content=text,
                    session_name=self._state.session_title(self._curr_sid),
                )
            except Exception:
                pass
        QTimer.singleShot(50, self._scroll_bottom)

    def _on_error(self, err: str):
        self._hide_typing()
        fake_msg = Message(
            role=MessageRole.ASSISTANT,
            content=f"⚠️ Lỗi: {err}\nVui lòng kiểm tra API key hoặc kết nối mạng.",
        )
        self._add_bubble(fake_msg)

    def _on_worker_done(self):
        self._worker = None
        self.btnSend.setEnabled(True)

    def _cancel_worker(self):
        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(2000)
        self._worker = None
        self._hide_typing()
        self.btnSend.setEnabled(True)
    # ================================================================== #
    #  Tool definitions (Gemini Function Calling)                         #
    # ================================================================== #

    def get_tools_definitions(self):
        """Trả về danh sách tool (FunctionDeclaration) dùng trong chat_with_tools."""
        # Tool tạo lịch trình học tập (hỗ trợ ngày hoặc tuần)
        create_schedule_tool = types.FunctionDeclaration(
            name="create_learning_schedule",
            description=(
                "Tạo lịch trình học tập chi tiết cho một ngày hoặc nhiều tuần. "
                "Sẽ tự động thêm các nhiệm vụ (tasks) vào Planner của người dùng."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Chủ đề cần học (VD: Python, Giải tích)"},
                    "level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"], "description": "Trình độ"},
                    "duration_type": {"type": "string", "enum": ["day", "week"], "description": "Loại lịch: theo ngày hoặc theo tuần"},
                    "target_date": {"type": "string", "description": "Nếu duration_type='day', ngày cụ thể (VD: '2025-05-20' hoặc 'today'). Bỏ qua nếu là tuần."},
                    "duration_weeks": {"type": "integer", "description": "Số tuần (chỉ dùng khi duration_type='week'). Mặc định 4."},
                    "hours_per_day": {"type": "number", "description": "Số giờ học mỗi ngày (chỉ dùng khi duration_type='day'). Mặc định 2."},
                    "hours_per_week": {"type": "integer", "description": "Số giờ mỗi tuần (chỉ dùng khi duration_type='week'). Mặc định 5."}
                },
                "required": ["topic", "level", "duration_type"]
            }
        )
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

        # Tool tạo roadmap
        generate_roadmap_tool = types.FunctionDeclaration(
            name="generate_learning_roadmap",
            description="Tạo lộ trình học tập dạng mốc các chủ đề chính. Hãy trả về danh sách các chủ đề với tên, trạng thái (done/in_progress/locked) và mô tả chi tiết.",
            parameters={
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "Tên môn học, ví dụ: Python, Toán học."},
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
                "required": ["subject"]
            }
        )

        return types.Tool(function_declarations=[create_schedule_tool, generate_roadmap_tool])

    # ================================================================== #
    #  Gửi / nhận tin nhắn                                                #
    # ================================================================== #

    def _key_press(self, event):
        """Enter gửi, Shift+Enter xuống dòng."""
        from PyQt6.QtWidgets import QPlainTextEdit
        if (
            event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        ):
            self._send()
        else:
            QPlainTextEdit.keyPressEvent(self.chatInputField, event)

    def _send(self):
        text = self.chatInputField.toPlainText().strip()
        if not text:
            return
        if self._worker:
            return

        subject = strip_icon(self.subjectCombo.currentText())

        # ── Lưu & hiển thị tin user ───────────────────────────────────
        msg = self._state.add_message(self._curr_sid, MessageRole.USER, text)
        self._add_bubble(msg)
        self.chatInputField.clear()
        self.btnSend.setEnabled(False)
        self.message_sent.emit()
        self._chat_history.append({"role": "user", "content": text})

        # Lưu vào DB nếu có
        if _DB_AVAILABLE:
            try:
                DBManager.instance().save_chat_message(
                    role="user",
                    content=text,
                    session_name=self._state.session_title(self._curr_sid),
                )
            except Exception:
                pass

        self._show_typing()

        # ── Xây system prompt có context cá nhân hóa ─────────────────
        system = self._build_system(subject)

        # ── Khởi động worker với tools ───────────────────────────────
        tools = self.get_tools_definitions()
        tools_list = [tools] if tools else None

        self._worker = ApiWorker(
            user_text=text,
            history=self._chat_history.copy(),
            system=system,
            subject=subject,
            api_key=self._settings.api_key,
            tools_def=tools_list,
            parent=self,
        )
        self._worker.response_ready.connect(self._on_reply)
        self._worker.tool_call_request.connect(self._handle_tool_call)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished_work.connect(self._on_worker_done)
        self._worker.start()

    def _build_system(self, subject: str) -> str:
        """Xây dựng system prompt cá nhân hóa từ DB."""
        if not _DB_AVAILABLE:
            return SYSTEM_CHAT
        try:
            prompt = build_system_prompt(
                subject=subject if subject and "Tất cả" not in subject else None
            )
            return prompt
        except Exception:
            return SYSTEM_CHAT

    def _on_reply(self, text: str):
        """Nhận phản hồi text từ AI (không tool call)."""
        self._hide_typing()
        msg = self._state.add_message(self._curr_sid, MessageRole.ASSISTANT, text)
        self._add_bubble(msg)
        self._chat_history.append({"role": "assistant", "content": text})

        if _DB_AVAILABLE:
            try:
                DBManager.instance().save_chat_message(
                    role="assistant",
                    content=text,
                    session_name=self._state.session_title(self._curr_sid),
                )
            except Exception:
                pass

        QTimer.singleShot(50, self._scroll_bottom)

    def _handle_tool_call(self, tool_name: str, tool_args: dict):
        """Xử lý tool call từ AI."""
        self._hide_typing()

        if tool_name == "create_learning_schedule":
            self._handle_create_schedule(tool_args)

        elif tool_name == "generate_learning_roadmap":
            self._handle_generate_roadmap(tool_args)

        else:
            self._append_message(f"⚠️ Tôi chưa được huấn luyện để thực hiện tác vụ '{tool_name}'.", is_user=False)

        self._worker = None

    def _handle_create_schedule(self, args: dict):
        """Tạo lịch trình học và thêm vào Planner."""
        if self._main_window and hasattr(self._main_window, 'planner'):
            planner = self._main_window.planner
            if hasattr(planner, 'create_learning_schedule'):
                try:
                    schedule = planner.create_learning_schedule(
                        topic=args.get("topic", "Chủ đề mới"),
                        level=args.get("level", "beginner"),
                        duration_weeks=args.get("duration_weeks", 4),
                        hours_per_week=args.get("hours_per_week", 5),
                    )
                    display_text = self._format_schedule(schedule)
                    self._append_message(display_text, is_user=False)
                    self._chat_history.append({"role": "assistant", "content": display_text})
                except Exception as e:
                    self._append_message(f"⚠️ Lỗi khi tạo lịch trình: {str(e)}", is_user=False)
            else:
                self._append_message("⚠️ Lỗi: Planner chưa có chức năng tạo lịch trình.", is_user=False)
        else:
            self._append_message("⚠️ Lỗi hệ thống: không thể kết nối với Planner.", is_user=False)

    def _handle_generate_roadmap(self, args: dict):
        """Tạo lộ trình học từ AI và thêm vào Roadmap."""
        if self._main_window and hasattr(self._main_window, 'roadmap'):
            roadmap_ctrl = self._main_window.roadmap
            subject = args.get("subject", "Môn học mới")
            level = args.get("level", "beginner")
            topics_data = args.get("topics", [])

            if not topics_data:
                topics_data = [
                    {"name": f"Nhập môn {subject}", "status": "in_progress",
                     "detail": f"Các khái niệm cơ bản của {subject}"},
                    {"name": f"{subject} nâng cao", "status": "locked",
                     "detail": "Các chủ đề chuyên sâu"}
                ]

            # Gọi method add_roadmap_from_ai nếu có, nếu không thì dùng generate_learning_roadmap
            if hasattr(roadmap_ctrl, 'add_roadmap_from_ai'):
                roadmap_ctrl.add_roadmap_from_ai(subject, level, topics_data)
                self._append_message(
                    f"✅ Đã tạo lộ trình cho môn **{subject}** (trình độ {level}). Hãy xem trong tab **Lộ Trình**!",
                    is_user=False
                )
            elif hasattr(roadmap_ctrl, 'generate_learning_roadmap'):
                result = roadmap_ctrl.generate_learning_roadmap(subject=subject, current_pct=0, target_pct=100, weeks_remaining=4)
                self._append_message(
                    f"✅ Đã tạo lộ trình cho môn **{subject}**. {result.get('topics_count', 0)} chủ đề đã được thêm vào Lộ Trình.",
                    is_user=False
                )
            else:
                self._append_message("⚠️ Lỗi: RoadmapView chưa có chức năng tạo lộ trình từ AI.", is_user=False)
        else:
            self._append_message("⚠️ Lỗi hệ thống: không thể kết nối với Roadmap.", is_user=False)

    def _format_schedule(self, schedule: dict) -> str:
        """Định dạng lịch trình học để hiển thị dạng markdown-like."""
        if not schedule:
            return "Không thể tạo lịch trình. Vui lòng thử lại."

        topic = schedule.get('topic', 'Chủ đề')
        level = schedule.get('level', 'beginner')
        duration = schedule.get('duration_weeks', 4)
        hours = schedule.get('hours_per_week', 5)

        text = f"**📅 Lịch trình học {topic}**\n\n"
        text += f"- **Cấp độ:** {level}\n"
        text += f"- **Thời lượng:** {duration} tuần\n"
        text += f"- **Mỗi tuần:** {hours} giờ\n\n"

        for week in schedule.get('weeks', []):
            text += f"**Tuần {week['week']}:** {week.get('focus', '')}\n"
            for task in week.get('tasks', []):
                text += f"  - {task}\n"
            text += "\n"

        if 'notes' in schedule:
            text += f"📌 *Ghi chú:* {schedule['notes']}\n"

        return text

    def _on_error(self, err: str):
        """Hiển thị lỗi như tin nhắn bot."""
        self._hide_typing()
        error_msg = f"⚠️ Không thể kết nối AI: {err}\nVui lòng kiểm tra API key hoặc kết nối mạng."
        self._append_message(error_msg, is_user=False)

    def _on_worker_done(self):
        """Worker kết thúc (dù thành công hay lỗi)."""
        self._worker = None
        self.btnSend.setEnabled(True)

    def _cancel_worker(self):
        """Hủy worker đang chạy (khi chuyển session hoặc tạo session mới)."""
        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(2000)
        self._worker = None
        self._hide_typing()
        self.btnSend.setEnabled(True)
    #  Tool call handler
    def _handle_tool_call(self, tool_name: str, tool_args: dict):
        self._hide_typing()
        if tool_name == "create_learning_schedule":
            if self._main_window and hasattr(self._main_window, 'planner'):
                planner = self._main_window.planner
                if hasattr(planner, 'create_learning_schedule'):
                    # Gọi phương thức đã nâng cấp trong PlannerView
                    schedule = planner.create_learning_schedule(**tool_args)
                    display_text = self._format_schedule(schedule)
                    self._append_message(display_text, is_user=False)
                    self._chat_history.append({"role": "assistant", "content": display_text})
                else:
                    self._append_message("⚠️ Lỗi: Planner chưa hỗ trợ tạo lịch.", is_user=False)
            else:
                self._append_message("⚠️ Lỗi hệ thống: không thể kết nối với Planner.", is_user=False)

        elif tool_name == "generate_learning_roadmap":
            if self._main_window and hasattr(self._main_window, 'roadmap'):
                roadmap = self._main_window.roadmap
                if hasattr(roadmap, 'add_roadmap_from_ai'):
                    roadmap.add_roadmap_from_ai(
                        tool_args.get("subject", "Môn học mới"),
                        tool_args.get("level", "beginner"),
                        tool_args.get("topics", [])
                    )
                    self._append_message(
                        f"✅ Đã tạo lộ trình cho môn **{tool_args.get('subject')}**. Xem trong tab Lộ Trình!",
                        is_user=False
                    )
                else:
                    self._append_message("⚠️ Lỗi: Roadmap chưa hỗ trợ thêm lộ trình từ AI.", is_user=False)
            else:
                self._append_message("⚠️ Lỗi hệ thống: không thể kết nối với Roadmap.", is_user=False)
        else:
            self._append_message(f"⚠️ Tool '{tool_name}' chưa được hỗ trợ.", is_user=False)

        self._worker = None

    def _format_schedule(self, schedule: dict) -> str:
        if not schedule:
            return "Không thể tạo lịch trình."
        msg = f"**📅 {schedule.get('topic', 'Lịch học')}**\n"
        msg += f"- Trình độ: {schedule.get('level', '')}\n"
        if schedule.get('duration_type') == 'day':
            msg += f"- Ngày: {schedule.get('date', '')}\n- Số giờ: {schedule.get('hours', 2)}\n"
            msg += "**Các nhiệm vụ đã thêm vào Planner:**\n"
            for task in schedule.get('tasks_created', []):
                msg += f"  - {task}\n"
        else:
            msg += f"- Thời lượng: {schedule.get('duration_weeks', 4)} tuần\n- Mỗi tuần: {schedule.get('hours_per_week', 5)} giờ\n"
            msg += "**Các nhiệm vụ đã thêm:**\n"
            for task in schedule.get('tasks_created', []):
                msg += f"  - {task}\n"
        if schedule.get('notes'):
            msg += f"\n📌 {schedule['notes']}"
        msg += "\n\n✅ Hãy vào tab **Lịch Học** để xem chi tiết và theo dõi tiến độ."
        return msg

    def _append_message(self, text: str, is_user: bool = False):
        fake_msg = Message(role=MessageRole.ASSISTANT if not is_user else MessageRole.USER, content=text)
        self._add_bubble(fake_msg)
        self._chat_history.append({"role": "assistant" if not is_user else "user", "content": text})

    # ================================================================== #
    #  Helpers / Toolbar                                                   #
    # ================================================================== #

    def _on_subject_changed(self, text: str):
        subject = strip_icon(text)
        if subject and "Tất cả" not in subject:
            self.botStatusLabel.setText(f"🟢 Sẵn sàng – {subject}")
        else:
            self.botStatusLabel.setText("🟢 Sẵn sàng hỗ trợ")

    def _fill(self, text: str):
        """Điền sẵn text vào ô nhập."""
        self.chatInputField.setPlainText(text)
        self.chatInputField.setFocus()

    def _clear_chat(self):
        """Xóa lịch sử chat của session hiện tại."""
        if not self.confirm(
            self, "Xoá Chat",
            "Xoá toàn bộ lịch sử chat này?\nHành động không thể hoàn tác."
        ):
            return
        self._cancel_worker()
        # Xóa trong state
        if self._curr_sid in self._state._sessions:
            self._state._sessions[self._curr_sid] = []
        self._chat_history = []
        self._clear_messages_ui()
        self.botStatusLabel.setText("🟢 Chat đã được xóa")

    def _attach_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn ảnh", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if path:
            fname = path.replace("\\", "/").split("/")[-1]
            self._fill(f"[Ảnh đính kèm: {fname}]\n")

    def _attach_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file", "",
            "Documents (*.pdf *.docx *.txt *.xlsx *.pptx);;All Files (*)"
        )
        if path:
            fname = path.replace("\\", "/").split("/")[-1]
            self._fill(f"[File đính kèm: {fname}]\n")

    def _insert_formula(self):
        """Chèn ký hiệu toán học vào vị trí con trỏ."""
        from PyQt6.QtWidgets import QMenu, QAction
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu{background:#2d3748;color:#e2e8f0;border:1px solid #4a5568;"
            "border-radius:8px;padding:4px;}"
            "QMenu::item{padding:6px 16px;border-radius:4px;}"
            "QMenu::item:selected{background:#4a6cf7;}"
        )
        symbols = [
            ("∑  Tổng",          "∑"),
            ("√  Căn bậc hai",   "√"),
            ("π  Pi",            "π"),
            ("∞  Vô cực",        "∞"),
            ("∫  Tích phân",     "∫"),
            ("∂  Đạo hàm riêng", "∂"),
            ("≤  Nhỏ hơn bằng",  "≤"),
            ("≥  Lớn hơn bằng",  "≥"),
            ("≠  Khác",          "≠"),
            ("α β γ  Hy Lạp",   "α β γ δ ε λ μ σ θ φ"),
        ]
        for label, sym in symbols:
            act = QAction(label, self)
            act.triggered.connect(lambda _, s=sym: self._insert_symbol(s))
            menu.addAction(act)

        menu.exec(self.btnFormulaInput.mapToGlobal(
            self.btnFormulaInput.rect().bottomLeft()
        ))

    def _insert_symbol(self, sym: str):
        cur = self.chatInputField.toPlainText()
        self.chatInputField.setPlainText(cur + sym + " ")
        self.chatInputField.setFocus()
        cursor = self.chatInputField.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.chatInputField.setTextCursor(cursor)

    # ================================================================== #
    #  Public API – dùng từ MainWindow                                    #
    # ================================================================== #
    def set_main_window(self, mw):
        self._main_window = mw
        # Lưu lại _chat_history (nếu cần)
        self._chat_history = []
        
    def send_message_programmatic(self, text: str, subject: str = ""):
        """Gửi tin nhắn từ code (VD: từ Planner/Roadmap)."""
        if subject:
            idx = self.subjectCombo.findText(subject, Qt.MatchFlag.MatchContains)
            if idx >= 0:
                self.subjectCombo.setCurrentIndex(idx)
        self._fill(text)
        self._send()

    def get_current_session_title(self) -> str:
        return self._state.session_title(self._curr_sid)
    