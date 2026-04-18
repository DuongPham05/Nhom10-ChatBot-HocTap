"""
Chatbot Logic - Tạo lộ trình học tập thông minh
Tuần 1 + 2: Rule-based nhưng rất chi tiết và thực tế
"""

class RoadmapGenerator:
    def __init__(self):
        self.roadmap_db = {
            "python": self.get_python_roadmap,
            "web": self.get_web_roadmap,
            "sql": self.get_sql_roadmap,
            "qt": self.get_qt_roadmap,
            "machine learning": self.get_ml_roadmap,
            "javascript": self.get_js_roadmap,
        }
    
    def detect_target(self, target_text):
        """Phát hiện mục tiêu học tập từ câu nhập"""
        target_lower = target_text.lower()
        
        if "python" in target_lower:
            return "python"
        elif "web" in target_lower or "html" in target_lower or "css" in target_lower:
            return "web"
        elif "sql" in target_lower or "database" in target_lower:
            return "sql"
        elif "qt" in target_lower or "pyqt" in target_lower:
            return "qt"
        elif "machine learning" in target_lower or "ml" in target_lower or "ai" in target_lower:
            return "machine learning"
        elif "javascript" in target_lower or "js" in target_lower:
            return "javascript"
        else:
            return "general"
    
    def get_roadmap(self, target, level, hours_per_day, deadline_weeks):
        """Tạo lộ trình chính"""
        target_key = self.detect_target(target)
        
        if target_key in self.roadmap_db:
            roadmap_func = self.roadmap_db[target_key]
            return roadmap_func(level, hours_per_day, deadline_weeks)
        else:
            return self.get_general_roadmap(target, level, hours_per_day, deadline_weeks)
    
    def get_python_roadmap(self, level, hours, weeks):
        roadmap = f"""🎯 LỘ TRÌNH HỌC PYTHON ({weeks} tuần - {hours} giờ/ngày)

📊 Trình độ hiện tại: {level}

"""
        if level == "🌱 Mới bắt đầu":
            roadmap += """✅ TUẦN 1-2: NỀN TẢNG CỐT LÕI
• Ngày 1-3: Biến, kiểu dữ liệu, input/output
• Ngày 4-7: Câu lệnh điều kiện (if/elif/else)
• Ngày 8-10: Vòng lặp for, while
• Ngày 11-14: List, Tuple, Dictionary
📝 Bài tập cuối tuần 2: Viết chương trình quản lý danh sách sinh viên

✅ TUẦN 3-4: HÀM VÀ MODULE
• Ngày 15-17: Định nghĩa hàm, tham số, return
• Ngày 18-20: Xử lý lỗi (try/except)
• Ngày 21-22: Module và package
• Ngày 23-24: Đọc/ghi file
📝 Bài tập: Viết ứng dụng note cá nhân lưu ra file

✅ TUẦN 5-6: OOP CƠ BẢN
• Ngày 25-27: Class và Object
• Ngày 28-30: Thuộc tính và phương thức
• Ngày 31-32: Kế thừa và đa hình
• Ngày 33-34: Property và magic methods
📝 Bài tập: Xây dựng hệ thống quản lý thư viện đơn giản

✅ TUẦN 7-8: DỰ ÁN HOÀN CHỈNH
• Xây dựng ứng dụng quản lý công việc (To-Do App)
• Áp dụng toàn bộ kiến thức đã học
• Code có comment, xử lý lỗi tốt
"""
        elif level == "📘 Trung bình":
            roadmap += """✅ TUẦN 1-2: ÔN TẬP VÀ NÂNG CAO
• Hàm nâng cao: lambda, map, filter, reduce
• List comprehension và generator
• Decorator cơ bản
• Context manager (with statement)

✅ TUẦN 3-4: THƯ VIỆN PHỔ BIẾN
• requests: Gọi API
• beautifulsoup4: Crawl dữ liệu
• pandas: Xử lý dữ liệu
• matplotlib: Vẽ biểu đồ

✅ TUẦN 5-8: DỰ ÁN THỰC TẾ
• Dự án 1: Crawl dữ liệu web và phân tích
• Dự án 2: Xây dựng REST API với Flask
• Dự án 3: Phân tích dữ liệu với pandas + matplotlib
"""
        else:  # Khá
            roadmap += """✅ TUẦN 1-2: CHUYÊN SÂU
• Threading và multiprocessing
• Async/await (asyncio)
• Design patterns trong Python
• Unit testing với pytest

✅ TUẦN 3-4: FRAMEWORK CHUYÊN NGHIỆP
• Django hoặc FastAPI
• ORM nâng cao
• Middleware và authentication
• Deployment lên cloud

✅ DỰ ÁN CUỐI KHÓA:
• Xây dựng hệ thống hoàn chỉnh có database, API, frontend
"""
        
        roadmap += f"""
💡 LỜI KHUYÊN CHO {hours} GIỜ/NGÀY:
• Chia nhỏ: 2h lý thuyết + 2h thực hành + 1h review
• Code mỗi ngày ít nhất 50 dòng
• Tham gia cộng đồng Python Vietnam trên Facebook
• Tài liệu tham khảo: python.org, w3schools, codelearn.io
"""
        return roadmap
    
    def get_qt_roadmap(self, level, hours, weeks):
        roadmap = f"""🎯 LỘ TRÌNH HỌC QT6/PYQT6 ({weeks} tuần)

📊 Trình độ: {level}

✅ TUẦN 1: LÀM QUEN VỚI QT
• Ngày 1-2: Cài đặt PyQt6, Qt Designer
• Ngày 3-4: Tạo cửa sổ đầu tiên, QWidget, QMainWindow
• Ngày 5-7: Layout cơ bản (QVBox, QHBox, QGrid)
📝 Bài tập: Tạo form đăng nhập đơn giản

✅ TUẦN 2: WIDGETS CƠ BẢN
• Ngày 8-10: QLabel, QLineEdit, QPushButton, QComboBox
• Ngày 11-12: QTextEdit, QSpinBox, QCheckBox
• Ngày 13-14: Kết nối signal/slot
📝 Bài tập: Làm ứng dụng tính toán đơn giản

✅ TUẦN 3: SỰ KIỆN VÀ HỘP THOẠI
• Ngày 15-17: Xử lý sự kiện click, nhập liệu
• Ngày 18-19: QMessageBox, QFileDialog, QInputDialog
• Ngày 20-21: Menu bar, toolbar, status bar
📝 Bài tập: Text editor có menu File, Edit, Help

✅ TUẦN 4: DỰ ÁN CHATBOT (CHÍNH CỦA BẠN)
• Tích hợp logic tạo lộ trình
• Lưu/xuất dữ liệu
• Xử lý lỗi và validate input
• Hoàn thiện giao diện theo đồ án

🎯 KẾT QUẢ ĐẦU RA: Ứng dụng Chatbot hoàn chỉnh có GUI chuyên nghiệp

📚 TÀI LIỆU: 
• ZetCode PyQt6 Tutorial
• Qt Documentation
• Real Python - PyQt6
"""
        return roadmap
    
    def get_general_roadmap(self, target, level, hours, weeks):
        return f"""🎯 LỘ TRÌNH HỌC: {target.upper()} ({weeks} tuần)

📊 Trình độ: {level} | ⏰ {hours} giờ/ngày

✅ GIAI ĐOẠN 1 - NỀN TẢNG (Tuần 1-{weeks//3}):
• Tìm hiểu khái niệm cơ bản của {target}
• Làm bài tập theo tutorial từ cơ bản đến nâng cao
• Thực hành ít nhất 1 giờ mỗi ngày

✅ GIAI ĐOẠN 2 - THỰC HÀNH (Tuần {weeks//3+1}-{weeks*2//3}):
• Xây dựng 3-5 dự án nhỏ
• Đọc code mẫu từ GitHub
• Tham gia diễn đàn, hỏi đáp khi gặp khó

✅ GIAI ĐOẠN 3 - DỰ ÁN (Tuần {weeks*2//3+1}-{weeks}):
• Làm 1 dự án hoàn chỉnh
• Viết tài liệu và hướng dẫn cài đặt
• Demo sản phẩm và nhận feedback

💡 LỜI KHUYÊN:
• Tìm khóa học chất lượng trên Coursera, Udemy, YouTube
• Join group Facebook/Reddit về {target}
• Code mỗi ngày, không bỏ ngày nào
• Sau mỗi tuần, review lại những gì đã học

🔍 GỢI Ý CỤ THỂ HƠN:
Hãy cho tôi biết bạn muốn học framework/công nghệ cụ thể nào trong {target} để tôi tư vấn chi tiết hơn!
"""
    
    def get_web_roadmap(self, level, hours, weeks):
        return self.get_general_roadmap("Web Development (HTML/CSS/JS)", level, hours, weeks)
    
    def get_sql_roadmap(self, level, hours, weeks):
        return self.get_general_roadmap("SQL và Database", level, hours, weeks)
    
    def get_ml_roadmap(self, level, hours, weeks):
        return self.get_general_roadmap("Machine Learning", level, hours, weeks)
    
    def get_js_roadmap(self, level, hours, weeks):
        return self.get_general_roadmap("JavaScript", level, hours, weeks)