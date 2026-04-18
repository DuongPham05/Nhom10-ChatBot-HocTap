import mysql.connector
from mysql.connector import Error
from datetime import datetime
import hashlib

class DatabaseManager:
    def __init__(self, host='localhost', database='chatbot_learning', user='root', password=''):
        """Khởi tạo kết nối database"""
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.connect()
    
    def connect(self):
        """Kết nối đến MySQL"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            if self.connection.is_connected():
                print("✅ Đã kết nối thành công đến MySQL database!")
                return True
        except Error as e:
            print(f"❌ Lỗi kết nối database: {e}")
            return False
    
    def create_user(self, username, email, password, full_name='', student_id='', school_name='', grade_level=''):
        """Tạo người dùng mới"""
        cursor = self.connection.cursor()
        # Mã hóa mật khẩu đơn giản (nên dùng bcrypt trong production)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            query = """
                INSERT INTO users (username, email, password_hash, full_name, student_id, school_name, grade_level)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (username, email, password_hash, full_name, student_id, school_name, grade_level))
            self.connection.commit()
            user_id = cursor.lastrowid
            print(f"✅ Đã tạo người dùng: {username} (ID: {user_id})")
            return user_id
        except Error as e:
            print(f"❌ Lỗi tạo người dùng: {e}")
            return None
        finally:
            cursor.close()
    
    def login(self, username, password):
        """Đăng nhập"""
        cursor = self.connection.cursor(dictionary=True)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            query = "SELECT * FROM users WHERE username = %s AND password_hash = %s AND is_active = TRUE"
            cursor.execute(query, (username, password_hash))
            user = cursor.fetchone()
            
            if user:
                # Cập nhật last_login
                update_query = "UPDATE users SET last_login = NOW() WHERE user_id = %s"
                cursor.execute(update_query, (user['user_id'],))
                self.connection.commit()
                print(f"✅ Đăng nhập thành công: {username}")
                return user
            else:
                print("❌ Sai tên đăng nhập hoặc mật khẩu")
                return None
        except Error as e:
            print(f"❌ Lỗi đăng nhập: {e}")
            return None
        finally:
            cursor.close()
    
    def save_roadmap(self, user_id, target_skill, current_level, hours_per_day, deadline_weeks, roadmap_content):
        """Lưu lộ trình học tập"""
        cursor = self.connection.cursor()
        
        # Chuyển đổi level từ text sang enum
        level_map = {
            '🌱 Mới bắt đầu': 'beginner',
            '📘 Trung bình': 'intermediate',
            '🚀 Khá': 'advanced'
        }
        level_enum = level_map.get(current_level, 'beginner')
        
        try:
            query = """
                INSERT INTO learning_roadmaps (user_id, target_skill, current_level, hours_per_day, deadline_weeks, roadmap_content)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, target_skill, level_enum, hours_per_day, deadline_weeks, roadmap_content))
            self.connection.commit()
            roadmap_id = cursor.lastrowid
            print(f"✅ Đã lưu lộ trình (ID: {roadmap_id}) cho user {user_id}")
            return roadmap_id
        except Error as e:
            print(f"❌ Lỗi lưu lộ trình: {e}")
            return None
        finally:
            cursor.close()
    
    def get_user_roadmaps(self, user_id, limit=10):
        """Lấy danh sách lộ trình của người dùng"""
        cursor = self.connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT roadmap_id, target_skill, current_level, hours_per_day, 
                       deadline_weeks, status, created_date
                FROM learning_roadmaps
                WHERE user_id = %s
                ORDER BY created_date DESC
                LIMIT %s
            """
            cursor.execute(query, (user_id, limit))
            roadmaps = cursor.fetchall()
            return roadmaps
        except Error as e:
            print(f"❌ Lỗi lấy danh sách lộ trình: {e}")
            return []
        finally:
            cursor.close()
    
    def get_roadmap_detail(self, roadmap_id):
        """Lấy chi tiết một lộ trình"""
        cursor = self.connection.cursor(dictionary=True)
        
        try:
            query = "SELECT * FROM learning_roadmaps WHERE roadmap_id = %s"
            cursor.execute(query, (roadmap_id,))
            roadmap = cursor.fetchone()
            return roadmap
        except Error as e:
            print(f"❌ Lỗi lấy chi tiết lộ trình: {e}")
            return None
        finally:
            cursor.close()
    
    def save_feedback(self, user_id, roadmap_id, rating, comment='', is_difficult=False):
        """Lưu feedback từ người dùng"""
        cursor = self.connection.cursor()
        
        try:
            query = """
                INSERT INTO user_feedback (user_id, roadmap_id, rating, comment, is_difficult)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, roadmap_id, rating, comment, is_difficult))
            self.connection.commit()
            print(f"✅ Đã lưu feedback cho roadmap {roadmap_id}")
            return True
        except Error as e:
            print(f"❌ Lỗi lưu feedback: {e}")
            return False
        finally:
            cursor.close()
    
    def get_recommended_resources(self, skill_category, level):
        """Lấy tài liệu đề xuất"""
        cursor = self.connection.cursor(dictionary=True)
        
        level_map = {
            '🌱 Mới bắt đầu': 'beginner',
            '📘 Trung bình': 'intermediate',
            '🚀 Khá': 'advanced'
        }
        level_enum = level_map.get(level, 'beginner')
        
        try:
            query = """
                SELECT * FROM recommended_resources
                WHERE (skill_category = %s OR skill_category = 'General')
                AND level = %s
                ORDER BY resource_id
                LIMIT 5
            """
            cursor.execute(query, (skill_category, level_enum))
            resources = cursor.fetchall()
            return resources
        except Error as e:
            print(f"❌ Lỗi lấy tài liệu: {e}")
            return []
        finally:
            cursor.close()
    
    def close(self):
        """Đóng kết nối"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ Đã đóng kết nối database")