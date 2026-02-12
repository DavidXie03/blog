import matplotlib.pyplot as plt
import matplotlib.patches as patches
import platform

# 配置中文字体
if platform.system() == 'Darwin':  # macOS
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC']
else:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(8, 8))

# 栈帧结构（从高地址到低地址）
stack_items = [
    ("...", "调用方的栈帧", "#E0E0E0"),
    ("param2", "函数参数2 (第二个参数)", "#FFCDD2"),
    ("param1", "函数参数1 (第一个参数)", "#FFCDD2"),
    ("返回地址", "调用方的下一条指令地址", "#FFF9C4"),
    ("旧 EBP", "保存调用方的栈基址", "#E1F5FE"),
    ("local1", "局部变量1", "#C8E6C9"),
    ("local2", "局部变量2", "#C8E6C9"),
    ("...", "被调用方可能的更多数据", "#E0E0E0"),
]

box_height = 0.8
box_width = 4
start_y = 8
x_start = 2

# 绘制栈帧
for i, (name, desc, color) in enumerate(stack_items):
    y = start_y - i * box_height
    rect = patches.FancyBboxPatch((x_start, y), box_width, box_height,
                                   boxstyle="round,pad=0.02",
                                   facecolor=color, edgecolor='black', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x_start + box_width / 2, y + box_height / 2, name,
            ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(x_start + box_width + 0.3, y + box_height / 2, desc,
            ha='left', va='center', fontsize=9, color='#555555')

# 绘制地址标注
ax.annotate('高地址', xy=(1.5, start_y + 0.4), fontsize=10, ha='center')
ax.annotate('低地址', xy=(1.5, start_y - len(stack_items) * box_height + 0.4), fontsize=10, ha='center')

# 绘制箭头表示栈增长方向
ax.annotate('', xy=(1.5, start_y - len(stack_items) * box_height + 0.8),
            xytext=(1.5, start_y),
            arrowprops=dict(arrowstyle='->', color='#1976D2', lw=2))
ax.text(0.8, start_y - len(stack_items) * box_height / 2, '栈增长\n方向',
        ha='center', va='center', fontsize=9, color='#1976D2')

# 绘制分隔线和区域标注
separator_y = start_y - 3 * box_height
ax.axhline(y=separator_y, xmin=0.2, xmax=0.85, color='red', linestyle='--', linewidth=2)

# 区域标注
ax.text(x_start + box_width + 2.5, start_y - 1 * box_height, '调用方压入\n(调用前)',
        ha='center', va='center', fontsize=10, color='#C62828',
        bbox=dict(boxstyle='round', facecolor='#FFEBEE', edgecolor='#C62828'))

ax.text(x_start + box_width + 2.5, start_y - 5 * box_height, '被调用方分配\n(调用后)',
        ha='center', va='center', fontsize=10, color='#2E7D32',
        bbox=dict(boxstyle='round', facecolor='#E8F5E9', edgecolor='#2E7D32'))

# 绘制EBP指针（紧挨着描述文字右侧）
ebp_y = start_y - 4 * box_height + box_height / 2  # 旧EBP所在行的中心位置
desc_end_x = x_start + box_width + 0.3 + 2.0  # 描述文字结束位置（估算"保存调用方的栈基址"宽度）
ax.text(desc_end_x, ebp_y, ' ←EBP',
        ha='left', va='center', fontsize=10, fontweight='bold', color='#1976D2')

# 设置坐标轴
ax.set_xlim(0, 10)
ax.set_ylim(1.5, 9.5)
ax.set_aspect('equal')
ax.axis('off')

# 标题
ax.set_title('函数调用栈帧结构\nvoid foo(int param1, int param2) { int local1, local2; }',
             fontsize=12, fontweight='bold', pad=10)

plt.tight_layout()
plt.savefig('stack_frame.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.show()
print("图片已保存为 stack_frame.png")
