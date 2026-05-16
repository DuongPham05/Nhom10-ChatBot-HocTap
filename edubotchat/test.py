import mysql.connector

try:
    # Kết nối MySQL
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="edubot"
    )

    # Kiểm tra kết nối
    if connection.is_connected():
        db_info = connection.get_server_info()
        print("Kết nối MySQL thành công!")
        print("MySQL Server version:", db_info)

        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE();")

        record = cursor.fetchone()
        print("Đang kết nối tới database:", record)

except mysql.connector.Error as e:
    print("Lỗi kết nối MySQL:", e)

finally:
    # Đóng kết nối
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        print("Đã đóng kết nối MySQL.")