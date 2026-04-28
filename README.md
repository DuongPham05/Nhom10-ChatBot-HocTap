# Nhom10-ChatBot-HocTap
Xây dựng chatbot hỗ trợ lên kế hoạch, lộ trình học tập,hiệu quả cao và chính xác.
#  Study Planner Chatbot

Chatbot AI hỗ trợ lập kế hoạch và lộ trình học tập cá nhân hóa.
sk-de5c482203bd4158bdcc06c1c10ed3f4
##  Cấu trúc thư mục

```
study-planner-desktop/
├── resources/
│   ├── icons/
│   ├── images/
│   ├── styles/app.qss
│   └── resources.qrc          ← thêm
│
├── forms/                     ← giữ nguyên (tốt)
│
├── src/
│   ├── api/
│   │   ├── anthropic_client.py
│   │   ├── api_worker.py      ← thêm (QThread, BẮT BUỘC)
│   │   ├── prompts.py
│   │   └── exceptions.py      ← thêm
│   │
│   ├── controllers/
│   │   ├── base_controller.py ← thêm
│   │   ├── chat_controller.py
│   │   ├── roadmap_controller.py
│   │   └── planner_controller.py
│   │
│   ├── models/
│   │   ├── message.py
│   │   ├── task.py
│   │   ├── roadmap_node.py
│   │   ├── app_state.py       ← thêm (singleton state)
│   │   └── settings.py        ← thêm (QSettings wrapper)
│   │
│   ├── views/
│   │   ├── components/        ← thêm (widget tái sử dụng)
│   │   ├── dialogs/           ← thêm (QDialog)
│   │   ├── chat/
│   │   ├── roadmap/
│   │   ├── planner/
│   │   └── dashboard/
│   │
│   ├── utils/
│   │   ├── date_helpers.py
│   │   ├── parse_roadmap.py
│   │   ├── study_subjects.py
│   │   └── logger.py          ← thêm
│   │
│   ├── config.py              ← thêm (BẮT BUỘC)
│   └── resources_rc.py
│
├── tests/
│   ├── conftest.py            ← thêm (pytest fixtures)
│   ├── test_chat.py
│   ├── test_roadmap.py
│   └── test_planner.py
│
├── docs/
├── .env.example
├── requirements.txt
├── pyproject.toml             ← thêm
├── main.py
└── README.md

##  Chức năng chính

| Chức năng | Mô tả |
|-----------|-------|
|  **Chat AI** | Hỏi đáp về lộ trình, gợi ý tài liệu, giải đáp thắc mắc |
|  **Tạo Roadmap** | Sinh lộ trình học tự động theo mục tiêu & trình độ |
|  **Weekly Planner** | Lập lịch học chi tiết theo tuần |
|  **Dashboard** | Theo dõi tiến độ & thống kê học tập |
|  **Study Timer** | Pomodoro timer tích hợp |
