import matplotlib.pyplot as plt

# ——— 如果中文标签出现乱码，可尝试指定支持中文的字体 ———
# Windows 示例：SimHei；macOS 示例：Arial Unicode MS；Linux 环境可用 Noto Sans CJK
plt.rcParams['font.family'] = 'Arial Unicode MS'   # macOS
# plt.rcParams['font.family'] = 'SimHei'          # Windows
# plt.rcParams['font.family'] = 'Noto Sans CJK SC' # Linux

# 数据
labels = ["Anti-Blue Light\\\nAnti-Pollution", "Skin Nourishment \n(Whitening\Anti-Aging)", "Light Texture", "Waterproof and \nSweat Resistant", "Sustainable Packaging"]
sizes  = [38, 45, 52, 25, 15]

# 绘制饼图
fig, ax = plt.subplots()
ax.pie(
    sizes,
    labels=labels,
    autopct='%1.1f%%',     # 显示百分比
    startangle=140,        # 起始角度，避免某一块正对 12 点方向
    counterclock=False     # 顺时针
)
ax.set_title("2025 Sunscreen Products Core Selling Points Percentage ", pad = 50)
ax.axis('equal')           # 让饼图保持圆形
plt.tight_layout()
plt.show()