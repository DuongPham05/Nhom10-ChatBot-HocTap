import sys
import json
import os
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

#ROADMAP LOGIC
class RoadmapGenerator:
    def __init__(self):
        pass
    
    def detect_target(self, target_text):
        """Phát hiện mục tiêu học tập"""
        target_lower = target_text.lower()
        
        if "python" in target_lower:
            return "Python"
        elif "web" in target_lower or "html" in target_lower or "css" in target_lower:
            return "Web"
        elif "sql" in target_lower or "database" in target_lower:
            return "SQL"
        elif "qt" in target_lower or "pyqt" in target_lower:
            return "Qt"
        else:
            return "General"
    
    def get_roadmap(self, target, level, hours_per_day, deadline_weeks):
        """Tạo lộ trình chính"""
        target_key = self.detect_target(target)
        
        if target_key == "Python":
            return self.get_python_roadmap(level, hours_per_day, deadline_weeks)
        elif target_key == "Qt":
            return self.get_qt_roadmap(level, hours_per_day, deadline_weeks)
        elif target_key == "Web":
            return self.get_web_roadmap(level, hours_per_day, deadline_weeks)
        else:
            return self.get_general_roadmap(target, level, hours_per_day, deadline_weeks)
    
    def get_python_roadmap(self, level, hours, weeks):
        roadmap = f"""
{'='*80}
LỘ TRÌNH HỌC PYTHON ({weeks} tuần - {hours} giờ/ngày)
{'='*80}

Trình độ hiện tại: {level}

"""
        if "Mới" in level:
            roadmap += """
📚 GIAI ĐOẠN 1: NỀN TẢNG (Tuần 1-2)
----------------------------------------
• Biến, kiểu dữ liệu, nhập/xuất
• Câu lệnh điều kiện if/elif/else
• Vòng lặp for, while
• List, Tuple, Dictionary

✅ Bài tập: Viết chương trình quản lý danh sách sinh viên

📚 GIAI ĐOẠN 2: HÀM VÀ MODULE (Tuần 3-4)
----------------------------------------
• Định nghĩa hàm, tham số, return
• Xử lý lỗi try/except
• Module và package
• Đọc/ghi file

✅ Bài tập: Ứng dụng note cá nhân

📚 GIAI ĐOẠN 3: OOP CƠ BẢN (Tuần 5-6)
----------------------------------------
• Class và Object
• Thuộc tính và phương thức
• Kế thừa và đa hình

✅ Bài tập: Hệ thống quản lý thư viện

📚 GIAI ĐOẠN 4: DỰ ÁN (Tuần 7-8)
----------------------------------------
• Xây dựng ứng dụng To-Do List hoàn chỉnh
• Áp dụng toàn bộ kiến thức
• Code có comment, xử lý lỗi tốt
"""
        elif "Trung bình" in level:
            roadmap += """
📚 GIAI ĐOẠN 1: NÂNG CAO (Tuần 1-2)
----------------------------------------
• Lambda, map, filter, reduce
• List comprehension
• Decorator cơ bản
• Context manager

📚 GIAI ĐOẠN 2: THƯ VIỆN (Tuần 3-4)
----------------------------------------
• requests - Gọi API
• beautifulsoup4 - Crawl dữ liệu
• pandas - Xử lý dữ liệu
• matplotlib - Vẽ biểu đồ

📚 GIAI ĐOẠN 3: DỰ ÁN (Tuần 5-6)
----------------------------------------
• Crawl web và phân tích dữ liệu
• Xây dựng REST API với Flask
• Phân tích dữ liệu với pandas
"""
        else:
            roadmap += """
📚 GIAI ĐOẠN 1: CHUYÊN SÂU (Tuần 1-2)
----------------------------------------
• Threading và multiprocessing
• Async/await (asyncio)
• Design patterns
• Unit testing với pytest

📚 GIAI ĐOẠN 2: FRAMEWORK (Tuần 3-4)
----------------------------------------
• Django hoặc FastAPI
• ORM nâng cao
• Middleware và authentication
• Deployment

📚 DỰ ÁN CUỐI KHÓA
----------------------------------------
• Hệ thống hoàn chỉnh có database, API, frontend
"""
        
        roadmap += f"""

💡 LỜI KHUYÊN CHO {hours} GIỜ/NGÀY:
• Chia nhỏ: 2h lý thuyết + 2h thực hành + 1h review
• Code mỗi ngày ít nhất 50 dòng
• Tham gia cộng đồng Python Vietnam

📚 TÀI LIỆU THAM KHẢO:
• python.org
• w3schools.com/python
• codelearn.io
"""
        return roadmap
    
    def get_qt_roadmap(self, level, hours, weeks):
        roadmap = f"""
{'='*80}
LỘ TRÌNH HỌC QT6/PYQT6 ({weeks} tuần - {hours} giờ/ngày)
{'='*80}

Trình độ hiện tại: {level}

📚 TUẦN 1: LÀM QUEN VỚI QT
----------------------------------------
• Cài đặt PyQt6, Qt Designer
• Tạo cửa sổ đầu tiên (QWidget, QMainWindow)
• Layout cơ bản (QVBox, QHBox, QGrid)
✅ Bài tập: Tạo form đăng nhập

📚 TUẦN 2: WIDGETS CƠ BẢN
----------------------------------------
• QLabel, QLineEdit, QPushButton
• QComboBox, QTextEdit, QSpinBox
• Kết nối signal/slot
✅ Bài tập: Ứng dụng máy tính đơn giản

📚 TUẠN 3: SỰ KIỆN VÀ HỘP THOẠI
----------------------------------------
• Xử lý sự kiện click, nhập liệu
• QMessageBox, QFileDialog
• Menu bar, toolbar, status bar
✅ Bài tập: Text editor cơ bản

📚 TUẦN 4: DỰ ÁN CHATBOT (ĐỒ ÁN CỦA BẠN)
----------------------------------------
• Tích hợp logic tạo lộ trình
• Lưu/xuất dữ liệu ra JSON/MySQL
• Xử lý lỗi và validate input
• Hoàn thiện giao diện chuyên nghiệp

📚 TÀI LIỆU THAM KHẢO:
• ZetCode PyQt6 Tutorial
• Qt Documentation
• Real Python - PyQt6
"""
        return roadmap
    
    def get_web_roadmap(self, level, hours, weeks):
        return f"""
{'='*80}
LỘ TRÌNH HỌC WEB DEVELOPMENT ({weeks} tuần - {hours} giờ/ngày)
{'='*80}

📚 GIAI ĐOẠN 1: HTML/CSS (Tuần 1-2)
----------------------------------------
• HTML cơ bản (thẻ, form, table)
• CSS styling (flexbox, grid)
• Responsive design
✅ Bài tập: Tạo landing page

📚 GIAI ĐOẠN 2: JAVASCRIPT (Tuần 3-4)
----------------------------------------
• Biến, hàm, mảng, object
• DOM manipulation
• Event handling
✅ Bài tập: Tạo to-do list web

📚 GIAI ĐOẠN 3: BACKEND (Tuần 5-6)
----------------------------------------
• Node.js hoặc Python Flask
• REST API cơ bản
• Kết nối database
✅ Bài tập: Blog đơn giản

📚 TÀI LIỆU:
• freecodecamp.org
• theodinproject.com
• w3schools.com
"""
    
    def get_general_roadmap(self, target, level, hours, weeks):
        return f"""
{'='*80}
LỘ TRÌNH HỌC: {target.upper()}
{'='*80}

Trình độ: {level} | {hours} giờ/ngày | {weeks} tuần

📚 GIAI ĐOẠN 1 - NỀN TẢNG (Tuần 1-{max(1, weeks//3)})
----------------------------------------
• Tìm hiểu khái niệm cơ bản
• Làm bài tập theo tutorial
• Thực hành ít nhất 1 giờ/ngày

📚 GIAI ĐOẠN 2 - THỰC HÀNH (Tuần {max(1, weeks//3)+1}-{weeks*2//3})
----------------------------------------
• Xây dựng 3-5 dự án nhỏ
• Đọc code mẫu từ GitHub
• Tham gia diễn đàn hỏi đáp

📚 GIAI ĐOẠN 3 - DỰ ÁN (Tuần {weeks*2//3+1}-{weeks})
----------------------------------------
• Làm 1 dự án hoàn chỉnh
• Viết tài liệu hướng dẫn
• Demo và nhận feedback

💡 LỜI KHUYÊN:
• Tìm khóa học chất lượng trên Coursera, YouTube
• Join group Facebook/Reddit về {target}
• Code mỗi ngày, không bỏ ngày nào

🔍 ĐỂ ĐƯỢC TƯ VẤN CHI TIẾT HƠN:
Hãy nhập mục tiêu cụ thể hơn (Python, Qt, Web, SQL, Machine Learning...)
"""

# ==================== MAIN APPLICATION ====================
class ChatbotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.roadmap_gen = RoadmapGenerator()
        self.current_roadmap = ""
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("🤖 Chatbot Hỗ Trợ Lộ Trình Học Tập")
        self.setGeometry(100, 100, 1000, 800)
        
        # Widget trung tâm
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        
        # Tiêu đề
        title = QLabel("🎯 Chatbot Xây Dựng Lộ Trình Học Tập Cá Nhân Hóa")
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Group nhập liệu
        input_group = QGroupBox("📝 Thông Tin Người Dùng")
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # Mục tiêu
        grid.addWidget(QLabel("Mục tiêu học tập:"), 0, 0)
        self.txtTarget = QLineEdit()
        self.txtTarget.setPlaceholderText("Ví dụ: Học Python, Làm đồ án Qt, Học Web...")
        grid.addWidget(self.txtTarget, 0, 1)
        
        # Trình độ
        grid.addWidget(QLabel("Trình độ hiện tại:"), 1, 0)
        self.comboLevel = QComboBox()
        self.comboLevel.addItems(["🌱 Mới bắt đầu", "📘 Trung bình", "🚀 Khá"])
        grid.addWidget(self.comboLevel, 1, 1)
        
        # Thời gian
        grid.addWidget(QLabel("Thời gian học/ngày:"), 2, 0)
        self.spinHours = QSpinBox()
        self.spinHours.setRange(1, 12)
        self.spinHours.setValue(5)
        self.spinHours.setSuffix(" giờ")
        grid.addWidget(self.spinHours, 2, 1)
        
        # Deadline
        grid.addWidget(QLabel("Deadline (tuần):"), 3, 0)
        self.spinDeadline = QSpinBox()
        self.spinDeadline.setRange(1, 24)
        self.spinDeadline.setValue(4)
        self.spinDeadline.setSuffix(" tuần")
        grid.addWidget(self.spinDeadline, 3, 1)
        
        input_group.setLayout(grid)
        layout.addWidget(input_group)
        
        # Hàng nút bấm
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.btnCreate = QPushButton("🚀 Tạo Lộ Trình")
        self.btnSave = QPushButton("💾 Lưu Vào Database")
        self.btnSearch = QPushButton("🔍 Tra Cứu Lộ Trình")
        self.btnAdjust = QPushButton("⚙️ Điều Chỉnh")
        self.btnClear = QPushButton("🗑️ Xóa Trắng")
        
        for btn in [self.btnCreate, self.btnSave, self.btnSearch, self.btnAdjust, self.btnClear]:
            btn.setMinimumHeight(40)
            button_layout.addWidget(btn)
        
        layout.addLayout(button_layout)
        
        # Group kết quả
        result_group = QGroupBox("📖 Lộ Trình Học Tập Chi Tiết")
        result_layout = QVBoxLayout()
        self.txtRoadmap = QTextEdit()
        self.txtRoadmap.setReadOnly(True)
        result_layout.addWidget(self.txtRoadmap)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        # Status label
        self.lblStatus = QLabel("✅ Sẵn sàng - Nhập thông tin và bấm Tạo Lộ Trình")
        self.lblStatus.setStyleSheet("color: #2e7d32; padding: 5px; background-color: #e8f5e9; border-radius: 5px;")
        layout.addWidget(self.lblStatus)
        
        # Kết nối sự kiện
        self.btnCreate.clicked.connect(self.create_roadmap)
        self.btnSave.clicked.connect(self.save_to_file)
        self.btnSearch.clicked.connect(self.search_roadmap)
        self.btnAdjust.clicked.connect(self.adjust_plan)
        self.btnClear.clicked.connect(self.clear_all)
        
        # Hiển thị ví dụ
        self.show_example()
    
    def create_roadmap(self):
        """Tạo lộ trình dựa trên thông tin người dùng"""
        target = self.txtTarget.text().strip()
        if not target:
            QMessageBox.warning(self, "Thiếu thông tin", 
                               "Vui lòng nhập mục tiêu học tập!\n\nVí dụ: Python, Web, SQL, Qt...")
            return
        
        level = self.comboLevel.currentText()
        hours = self.spinHours.value()
        deadline = self.spinDeadline.value()
        
        # Cập nhật trạng thái
        self.lblStatus.setText("⏳ Đang tạo lộ trình phù hợp cho bạn...")
        self.txtRoadmap.setText("Đang xử lý, vui lòng chờ...")
        
        # Tạo lộ trình
        roadmap = self.roadmap_gen.get_roadmap(target, level, hours, deadline)
        self.current_roadmap = roadmap
        
        # Tạo header thông tin
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        separator = "=" * 80
        
        header = f"""
{separator}
CHATBOT LỘ TRÌNH HỌC TẬP CÁ NHÂN HÓA
{separator}
Ngày tạo: {current_time}
Trình độ: {level}
Thời gian: {hours} giờ/ngày
Mục tiêu: {target}
Deadline: {deadline} tuần
{separator}

"""
        
        self.txtRoadmap.setText(header + roadmap)
        self.lblStatus.setText("✅ Đã tạo lộ trình thành công! Bạn có thể lưu hoặc tra cứu sau.")
    
    def save_to_file(self):
        """Lưu lộ trình ra file JSON"""
        if not self.current_roadmap:
            QMessageBox.warning(self, "Chưa có lộ trình", 
                               "Hãy tạo lộ trình trước khi lưu!")
            return
        
        target = self.txtTarget.text()
        level = self.comboLevel.currentText()
        hours = self.spinHours.value()
        deadline = self.spinDeadline.value()
        
        # Dữ liệu lưu
        data = {
            "target": target,
            "level": level,
            "hours": hours,
            "deadline": deadline,
            "roadmap": self.current_roadmap,
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Đọc dữ liệu cũ nếu có
        filename = "roadmaps.json"
        all_roadmaps = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    all_roadmaps = json.load(f)
            except:
                all_roadmaps = []
        
        # Thêm mới
        all_roadmaps.append(data)
        
        # Lưu lại
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_roadmaps, f, ensure_ascii=False, indent=2)
        
        self.lblStatus.setText(f"✅ Đã lưu lộ trình vào file {filename}")
        QMessageBox.information(self, "Thành công", 
                               f"Đã lưu lộ trình thành công!\n\nTổng số lộ trình đã lưu: {len(all_roadmaps)}")
    
    def search_roadmap(self):
        """Tra cứu lộ trình đã lưu"""
        filename = "roadmaps.json"
        if not os.path.exists(filename):
            QMessageBox.information(self, "Chưa có dữ liệu", 
                                   "Chưa có lộ trình nào được lưu. Hãy tạo và lưu trước!")
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                all_roadmaps = json.load(f)
        except:
            QMessageBox.warning(self, "Lỗi", "Không thể đọc file dữ liệu!")
            return
        
        if not all_roadmaps:
            QMessageBox.information(self, "Trống", "Chưa có lộ trình nào được lưu!")
            return
        
        # Hiển thị danh sách gần đây
        recent = all_roadmaps[-5:]  # 5 lộ trình gần nhất
        search_result = "📚 DANH SÁCH 5 LỘ TRÌNH GẦN NHẤT:\n\n"
        search_result += "=" * 60 + "\n"
        
        for i, item in enumerate(recent, 1):
            search_result += f"{i}. 🎯 Mục tiêu: {item['target']}\n"
            search_result += f"   📊 Trình độ: {item['level']}\n"
            search_result += f"   ⏰ {item['hours']} giờ/ngày - {item['deadline']} tuần\n"
            search_result += f"   📅 Tạo lúc: {item['created_date']}\n"
            search_result += "-" * 60 + "\n"
        
        search_result += "\n💡 Để xem chi tiết lộ trình, hãy mở file 'roadmaps.json' bằng trình soạn thảo văn bản."
        
        self.txtRoadmap.setText(search_result)
        self.lblStatus.setText("🔍 Đã tra cứu - Hiển thị 5 lộ trình gần nhất")
    
    def adjust_plan(self):
        """Điều chỉnh kế hoạch nếu không theo kịp"""
        if not self.current_roadmap:
            QMessageBox.warning(self, "Chưa có lộ trình", 
                               "Hãy tạo lộ trình trước khi điều chỉnh!")
            return
        
        reply = QMessageBox.question(self, "Điều chỉnh kế hoạch",
                                     "Bạn đang gặp vấn đề gì?\n\n"
                                     "Chọn 'Có' nếu: Không theo kịp (giảm tải)\n"
                                     "Chọn 'Không' nếu: Không hiểu bài (tài liệu dễ hơn)",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.Yes)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Giảm tải
            adjustment = "\n\n" + "="*80 + "\n"
            adjustment += "⚠️ ĐIỀU CHỈNH KẾ HOẠCH (GIẢM TẢI)\n"
            adjustment += "="*80 + "\n"
            adjustment += "• Đã giảm 30% nội dung mỗi tuần\n"
            adjustment += "• Tập trung vào phần kiến thức cốt lõi\n"
            adjustment += "• Kéo dài thời gian thêm 2 tuần\n"
            adjustment += "• Ưu tiên làm bài tập thực hành thay vì lý thuyết\n"
            adjustment += "\n📚 TÀI LIỆU DỄ HIỂU HƠN:\n"
            adjustment += "  - w3schools.com (có tiếng Việt)\n"
            adjustment += "  - codelearn.io (học tương tác)\n"
            adjustment += "  - YouTube: 'Code với Tâm', 'Lập trình thật dễ'\n"
            
            self.txtRoadmap.setText(self.current_roadmap + adjustment)
            self.lblStatus.setText("⚙️ Đã điều chỉnh - Giảm tải nội dung")
        else:
            # Đề xuất tài liệu
            adjustment = "\n\n" + "="*80 + "\n"
            adjustment += "📖 TÀI LIỆU HỌC DỄ HIỂU HƠN\n"
            adjustment += "="*80 + "\n"
            adjustment += "1. VIDEO BÀI GIẢNG (chậm, chi tiết):\n"
            adjustment += "   - Kênh YouTube: 'Code với Tâm'\n"
            adjustment += "   - Kênh YouTube: 'Lập trình thật dễ'\n"
            adjustment += "   - Playlist 'Python cho người mới bắt đầu'\n\n"
            adjustment += "2. WEBSITE TƯƠNG TÁC:\n"
            adjustment += "   - codelearn.io (học qua game)\n"
            adjustment += "   - sololearn.com (app điện thoại)\n"
            adjustment += "   - hackerrank.com (thực hành)\n\n"
            adjustment += "3. NHÓM HỖ TRỢ:\n"
            adjustment += "   - Facebook: 'Hỏi đáp lập trình Việt Nam'\n"
            adjustment += "   - Discord: 'Lập trình viên trẻ'\n\n"
            adjustment += "4. SÁCH MIỄN PHÍ:\n"
            adjustment += "   - 'Automate the Boring Stuff with Python'\n"
            adjustment += "   - 'Học Python qua dự án' (tiếng Việt)\n"
            
            self.txtRoadmap.setText(self.current_roadmap + adjustment)
            self.lblStatus.setText("📚 Đã đề xuất tài liệu dễ hiểu hơn")
    
    def clear_all(self):
        """Xóa trắng tất cả"""
        self.txtTarget.clear()
        self.comboLevel.setCurrentIndex(0)
        self.spinHours.setValue(5)
        self.spinDeadline.setValue(4)
        self.txtRoadmap.clear()
        self.current_roadmap = ""
        self.lblStatus.setText("✅ Đã xóa trắng - Sẵn sàng nhập thông tin mới")
    
    def show_example(self):
        """Hiển thị ví dụ khi khởi động"""
        example = """🎯 VÍ DỤ NHANH:

Bạn muốn học Python để làm đồ án?

👉 CÁCH SỬ DỤNG:
1. Nhập vào ô "Mục tiêu học tập": Học Python
2. Chọn trình độ: Mới bắt đầu
3. Điều chỉnh thời gian: 5 giờ/ngày
4. Deadline: 4 tuần
5. Bấm "Tạo Lộ Trình" để xem kết quả!

✨ CÁC MỤC TIÊU ĐƯỢC HỖ TRỢ:
• Python (3 cấp độ: mới bắt đầu, trung bình, khá)
• Qt6 / PyQt6 (đặc biệt phù hợp với đồ án của bạn)
• Web Development (HTML/CSS/JS)
• SQL / Database
• Hoặc nhập bất kỳ mục tiêu nào khác

🔧 TÍNH NĂNG CỦA CHATBOT:
• 💾 Lưu lộ trình vào file JSON
• 🔍 Tra cứu lộ trình đã lưu
• ⚙️ Điều chỉnh khi không theo kịp
• 🗑️ Xóa trắng để nhập mới

💡 Hãy thử ngay bằng cách nhập "Học Python" và bấm "Tạo Lộ Trình"!
"""
        self.txtRoadmap.setText(example)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatbotApp()
    window.show()
    sys.exit(app.exec())