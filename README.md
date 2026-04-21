# Nhom10-ChatBot-HocTap
Xây dựng chatbot hỗ trợ lên kế hoạch, lộ trình học tập
#  Study Planner Chatbot

Chatbot AI hỗ trợ lập kế hoạch và lộ trình học tập cá nhân hóa.

##  Cấu trúc thư mục

```
study-planner-chatbot/
├── public/                         # Static assets
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── api/                        # Giao tiếp với Anthropic API
│   │   ├── anthropic.js            # Cấu hình & gọi Claude API
│   │   └── prompts.js              # System prompts cho từng chức năng
│   │
│   ├── components/
│   │   ├── Chat/                   # Module chatbot chính
│   │   │   ├── ChatWindow.jsx      # Cửa sổ chat chính
│   │   │   ├── MessageBubble.jsx   # Hiển thị từng tin nhắn
│   │   │   ├── InputBar.jsx        # Thanh nhập liệu
│   │   │   └── TypingIndicator.jsx # Hiệu ứng đang gõ
│   │   │
│   │   ├── Roadmap/                # Lộ trình học tập
│   │   │   ├── RoadmapView.jsx     # Hiển thị roadmap dạng timeline
│   │   │   ├── RoadmapNode.jsx     # Từng node trong roadmap
│   │   │   └── RoadmapExport.jsx   # Xuất roadmap ra PDF/PNG
│   │   │
│   │   ├── Planner/                # Kế hoạch học theo tuần/tháng
│   │   │   ├── WeeklyPlanner.jsx   # Lịch học theo tuần
│   │   │   ├── TaskCard.jsx        # Card nhiệm vụ học tập
│   │   │   ├── ProgressBar.jsx     # Thanh tiến độ
│   │   │   └── StudyTimer.jsx      # Pomodoro timer
│   │   │
│   │   └── Dashboard/              # Tổng quan & thống kê
│   │       ├── StatsPanel.jsx      # Thống kê tiến độ
│   │       ├── GoalTracker.jsx     # Theo dõi mục tiêu
│   │       └── StreakCounter.jsx   # Đếm chuỗi ngày học
│   │
│   ├── hooks/                      # Custom React Hooks
│   │   ├── useChat.js              # Quản lý state chat
│   │   ├── useRoadmap.js           # Logic tạo & lưu roadmap
│   │   ├── usePlanner.js           # Logic kế hoạch học
│   │   └── useLocalStorage.js      # Lưu dữ liệu local
│   │
│   ├── utils/                      # Tiện ích
│   │   ├── dateHelpers.js          # Xử lý ngày tháng
│   │   ├── parseRoadmap.js         # Parse JSON roadmap từ AI
│   │   └── studySubjects.js        # Danh sách môn học mẫu
│   │
│   ├── styles/                     # Global styles
│   │   ├── globals.css
│   │   └── variables.css           # CSS custom properties
│   │
│   ├── pages/                      # Các trang chính
│   │   ├── HomePage.jsx
│   │   ├── ChatPage.jsx
│   │   ├── RoadmapPage.jsx
│   │   └── PlannerPage.jsx
│   │
│   └── App.jsx                     # Root component
│
├── docs/
│   ├── architecture.md             # Kiến trúc hệ thống
│   ├── api-reference.md            # Tài liệu API
│   └── prompt-engineering.md       # Thiết kế prompt
│
├── tests/
│   ├── chat.test.js
│   ├── roadmap.test.js
│   └── planner.test.js
│
├── .env.example                    # Mẫu biến môi trường
├── package.json
└── README.md
```

##  Chức năng chính

| Chức năng | Mô tả |
|-----------|-------|
|  **Chat AI** | Hỏi đáp về lộ trình, gợi ý tài liệu, giải đáp thắc mắc |
|  **Tạo Roadmap** | Sinh lộ trình học tự động theo mục tiêu & trình độ |
|  **Weekly Planner** | Lập lịch học chi tiết theo tuần |
|  **Dashboard** | Theo dõi tiến độ & thống kê học tập |
|  **Study Timer** | Pomodoro timer tích hợp |
