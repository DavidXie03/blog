import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
import platform

# 配置中文字体
if platform.system() == 'Darwin':  # macOS
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC']
else:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

fig, axes = plt.subplots(1, 2, figsize=(12, 7))

def draw_memory_regions(ax):
    """绘制栈和堆的区域背景"""
    # 栈区域（上方）
    stack_bg = Rectangle((-0.5, 3.2), 7, 1.8,
                         facecolor='#E3F2FD', edgecolor='#1976D2', 
                         linewidth=2, linestyle='-', alpha=0.5)
    ax.add_patch(stack_bg)
    ax.text(-0.3, 4.7, '栈 (Stack)', fontsize=11, fontweight='bold', 
            color='#1976D2', va='center', ha='left')
    
    # 堆区域（下方）
    heap_bg = Rectangle((-0.5, 0.1), 7, 2.9,
                        facecolor='#FFF3E0', edgecolor='#E65100', 
                        linewidth=2, linestyle='-', alpha=0.5)
    ax.add_patch(heap_bg)
    ax.text(-0.3, 2.7, '堆 (Heap)', fontsize=11, fontweight='bold', 
            color='#E65100', va='center', ha='left')

def draw_node(ax, x, y, name, ref_count, color, edge_color):
    """绘制堆上的Node对象"""
    rect = FancyBboxPatch((x - 0.9, y - 0.6), 1.8, 1.2,
                          boxstyle="round,pad=0.05",
                          facecolor=color, edgecolor=edge_color, linewidth=2)
    ax.add_patch(rect)
    ax.text(x, y + 0.2, name, ha='center', va='center', fontsize=11, fontweight='bold')
    ax.text(x, y - 0.25, f'引用计数={ref_count}', ha='center', va='center', fontsize=9, color='#555')

def draw_stack_ptr(ax, x, y, name, var_name):
    """绘制栈上的智能指针变量"""
    rect = FancyBboxPatch((x - 0.8, y - 0.4), 1.6, 0.8,
                          boxstyle="round,pad=0.03",
                          facecolor='white', edgecolor='#1976D2', linewidth=2)
    ax.add_patch(rect)
    ax.text(x, y + 0.1, var_name, ha='center', va='center', fontsize=10, fontweight='bold', color='#1976D2')
    ax.text(x, y - 0.18, f'({name})', ha='center', va='center', fontsize=8, color='#666')

def draw_arrow(ax, start, end, color='#333', style='->', connectionstyle="arc3,rad=0.1", linestyle='-'):
    """绘制箭头"""
    arrow = FancyArrowPatch(start, end,
                            connectionstyle=connectionstyle,
                            arrowstyle=style,
                            mutation_scale=15,
                            color=color,
                            linewidth=2,
                            linestyle=linestyle)
    ax.add_patch(arrow)

# ========== 左图：循环引用问题 ==========
ax1 = axes[0]
ax1.set_xlim(-1, 7)
ax1.set_ylim(-1, 5.5)
ax1.set_aspect('equal')
ax1.axis('off')
ax1.set_title('循环引用问题', fontsize=13, fontweight='bold', color='#C62828', pad=15)

# 绘制内存区域背景
draw_memory_regions(ax1)

# 栈上的智能指针变量
draw_stack_ptr(ax1, 1.5, 4, 'shared_ptr', 'parent')
draw_stack_ptr(ax1, 4.5, 4, 'shared_ptr', 'child')

# 堆上的Node对象
draw_node(ax1, 1.5, 1.5, 'Parent节点', 2, '#FFCDD2', '#C62828')
draw_node(ax1, 4.5, 1.5, 'Child节点', 2, '#FFCDD2', '#C62828')

# 栈上指针指向堆上对象
draw_arrow(ax1, (1.5, 3.6), (1.5, 2.1), color='#1976D2', connectionstyle="arc3,rad=0")
draw_arrow(ax1, (4.5, 3.6), (4.5, 2.1), color='#1976D2', connectionstyle="arc3,rad=0")

# 互相持有 (shared_ptr)
# Parent->child 指向 Child
draw_arrow(ax1, (2.4, 1.8), (3.6, 1.8), color='#C62828', connectionstyle="arc3,rad=-0.3")
ax1.text(3, 2.45, 'shared_ptr\n(child成员)', ha='center', va='center', fontsize=8, color='#C62828')

# Child->parent 指向 Parent
draw_arrow(ax1, (3.6, 1.2), (2.4, 1.2), color='#C62828', connectionstyle="arc3,rad=-0.3")
ax1.text(3, 0.35, 'shared_ptr\n(parent成员)', ha='center', va='center', fontsize=8, color='#C62828')

# 说明文字
ax1.text(3, -0.7, '函数返回后：引用计数各减1变为1\n互相持有导致永不归零，内存泄漏！', 
         ha='center', va='center', fontsize=10, color='#C62828',
         bbox=dict(boxstyle='round', facecolor='#FFEBEE', edgecolor='#C62828', pad=0.5))

# ========== 右图：weak_ptr解决方案 ==========
ax2 = axes[1]
ax2.set_xlim(-1, 7)
ax2.set_ylim(-1, 5.5)
ax2.set_aspect('equal')
ax2.axis('off')
ax2.set_title('打破循环依赖', fontsize=13, fontweight='bold', color='#2E7D32', pad=15)

# 绘制内存区域背景
draw_memory_regions(ax2)

# 栈上的智能指针变量
draw_stack_ptr(ax2, 1.5, 4, 'shared_ptr', 'parent')
draw_stack_ptr(ax2, 4.5, 4, 'shared_ptr', 'child')

# 堆上的Node对象
draw_node(ax2, 1.5, 1.5, 'Parent节点', 1, '#C8E6C9', '#2E7D32')
draw_node(ax2, 4.5, 1.5, 'Child节点', 2, '#C8E6C9', '#2E7D32')

# 栈上指针指向堆上对象
draw_arrow(ax2, (1.5, 3.6), (1.5, 2.1), color='#1976D2', connectionstyle="arc3,rad=0")
draw_arrow(ax2, (4.5, 3.6), (4.5, 2.1), color='#1976D2', connectionstyle="arc3,rad=0")

# Parent->child 指向 Child
draw_arrow(ax2, (2.4, 1.8), (3.6, 1.8), color='#2E7D32', connectionstyle="arc3,rad=-0.3")
ax2.text(3, 2.45, 'shared_ptr\n(child成员)', ha='center', va='center', fontsize=8, color='#2E7D32')

# Child->parent 用weak_ptr指回Parent（虚线表示弱引用）
draw_arrow(ax2, (3.6, 1.2), (2.4, 1.2), color='#888888', connectionstyle="arc3,rad=-0.3", linestyle='--')
ax2.text(3, 0.35, 'weak_ptr\n(不增加计数)', ha='center', va='center', fontsize=8, color='#888888')

# 说明文字
ax2.text(3, -0.7, '函数返回后：parent计数归零先析构\nchild随之析构，无内存泄漏', 
         ha='center', va='center', fontsize=10, color='#2E7D32',
         bbox=dict(boxstyle='round', facecolor='#E8F5E9', edgecolor='#2E7D32', pad=0.5))

plt.tight_layout()
plt.savefig('circular_reference.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.show()
print("图片已保存为 circular_reference.png")
