"""
parse_roadmap.py - Parse văn bản roadmap do AI trả về thành cấu trúc cây.
"""

import re
from src.models.roadmap_node import RoadmapNode


def parse_roadmap_text(text: str) -> RoadmapNode:
    """Phân tích văn bản roadmap thành cây RoadmapNode.

    Định dạng mong đợi (Markdown-like):
    # Chủ đề lớn
    ## Chủ đề con 1
    ### Chủ đề con 1.1
    ## Chủ đề con 2

    Args:
        text: Văn bản roadmap nhiều dòng

    Returns:
        RoadmapNode gốc
    """
    lines = text.strip().splitlines()
    root = RoadmapNode(title="Lộ trình học tập")
    stack = [(0, root)]  # (level, node)

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Xác định level dựa vào số dấu #
        match = re.match(r'^(#{1,6})\s+(.*)', line)
        if not match:
            # Dòng không có heading -> bỏ qua hoặc thêm vào description của node hiện tại
            if stack:
                current_node = stack[-1][1]
                if current_node.description:
                    current_node.description += "\n" + line
                else:
                    current_node.description = line
            continue

        hashes = match.group(1)
        title = match.group(2).strip()
        level = len(hashes)

        # Tạo node mới
        new_node = RoadmapNode(title=title)

        # Tìm cha phù hợp
        while stack and stack[-1][0] >= level:
            stack.pop()

        if stack:
            parent = stack[-1][1]
            parent.add_child(new_node)
        else:
            # Nếu stack rỗng, thêm vào root
            root.add_child(new_node)

        stack.append((level, new_node))

    return root


def roadmap_to_markdown(root: RoadmapNode, level: int = 1) -> str:
    """Chuyển cây roadmap ngược lại thành Markdown.

    Args:
        root: Node gốc
        level: Cấp độ tiêu đề bắt đầu (mặc định 1)

    Returns:
        Chuỗi markdown
    """
    lines = []
    prefix = "#" * level
    status = "✅" if root.completed else "⬜"
    lines.append(f"{prefix} {status} {root.title}")

    if root.description:
        lines.append(root.description)

    for child in root.children:
        lines.append(roadmap_to_markdown(child, level + 1))

    return "\n".join(lines)