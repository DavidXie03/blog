import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))

# 颜色定义
color_obj = '#FFE0B2'        # 对象框 - 浅橙
color_heap = '#C8E6C9'       # 堆内存 - 浅绿
color_ptr = '#FF5722'        # 指针箭头 - 橙红
color_null = '#BDBDBD'       # 空指针 - 灰色

def draw_object(ax, x, y, name, ptr_value, size_value, has_arrow=True, arrow_target=None):
    """绘制对象框"""
    # 对象外框
    obj_box = FancyBboxPatch((x, y), 2.2, 1.5,
                              boxstyle="round,pad=0.02,rounding_size=0.1",
                              facecolor=color_obj, edgecolor='#FF9800',
                              linewidth=2)
    ax.add_patch(obj_box)
    
    # 对象名
    ax.text(x + 1.1, y + 1.7, name, fontsize=12, ha='center', fontweight='bold')
    
    # 成员变量
    ax.text(x + 0.15, y + 1.1, f'data_: {ptr_value}', fontsize=9, ha='left', 
            family='monospace')
    ax.text(x + 0.15, y + 0.6, f'size_: {size_value}', fontsize=9, ha='left',
            family='monospace')
    
    # 指针箭头 - 从对象框顶部边缘出发，避免与方形重合
    if has_arrow and arrow_target:
        ax.annotate('', xy=arrow_target, xytext=(x + 1.1, y + 1.5),
                   arrowprops=dict(arrowstyle='->', color=color_ptr, lw=2,
                                   connectionstyle='arc3,rad=0.1'))

def draw_heap(ax, x, y, values, label):
    """绘制堆内存"""
    width = len(values) * 0.6
    heap_box = FancyBboxPatch((x, y), width, 0.8,
                               boxstyle="round,pad=0.02,rounding_size=0.05",
                               facecolor=color_heap, edgecolor='#4CAF50',
                               linewidth=2)
    ax.add_patch(heap_box)
    
    # 分隔线和值
    for i, val in enumerate(values):
        if i > 0:
            ax.plot([x + i * 0.6, x + i * 0.6], [y, y + 0.8], 
                   color='#4CAF50', lw=1)
        ax.text(x + i * 0.6 + 0.3, y + 0.4, str(val), fontsize=10, 
               ha='center', va='center')
    
    ax.text(x + width/2, y - 0.3, label, fontsize=9, ha='center', 
           style='italic', color='#666666')

# ============ 左图：移动前 ============
ax1 = axes[0]
ax1.set_xlim(0, 9)
ax1.set_ylim(0, 6)
ax1.axis('off')
ax1.set_title('移动前', fontsize=14, fontweight='bold', pad=10)

# 堆内存
draw_heap(ax1, 4, 4, [1, 2, 3, 4, 5], '堆内存')

# 源对象 src - 箭头指向堆内存底部中央
draw_object(ax1, 0.5, 2, 'src', '0x1234', '5', has_arrow=True, arrow_target=(5.5, 4))

# 目标对象 dst (未初始化状态)
dst_box = FancyBboxPatch((6.3, 2), 2.2, 1.5,
                          boxstyle="round,pad=0.02,rounding_size=0.1",
                          facecolor='#E0E0E0', edgecolor='#9E9E9E',
                          linewidth=2, linestyle='--')
ax1.add_patch(dst_box)
ax1.text(7.4, 3.7, 'dst', fontsize=12, ha='center', fontweight='bold')
ax1.text(7.4, 2.75, '(未初始化)', fontsize=10, ha='center', color='#666666')

# 标注
ax1.text(4.5, 0.5, 'Buffer dst = std::move(src);', fontsize=11, ha='center',
        family='monospace', style='italic',
        bbox=dict(boxstyle='round', facecolor='#FFF3E0', edgecolor='#FFB74D'))

# ============ 右图：移动后 ============
ax2 = axes[1]
ax2.set_xlim(0, 9)
ax2.set_ylim(0, 6)
ax2.axis('off')
ax2.set_title('移动后', fontsize=14, fontweight='bold', pad=10)

# 堆内存 (位置不变)
draw_heap(ax2, 4, 4, [1, 2, 3, 4, 5], '堆内存 (未拷贝)')

# 源对象 src (已被移动，置空状态)
src_box = FancyBboxPatch((0.5, 2), 2.2, 1.5,
                          boxstyle="round,pad=0.02,rounding_size=0.1",
                          facecolor='#EEEEEE', edgecolor='#BDBDBD',
                          linewidth=2)
ax2.add_patch(src_box)
ax2.text(1.6, 3.7, 'src', fontsize=12, ha='center', fontweight='bold', color='#9E9E9E')
ax2.text(0.65, 3.1, 'data_: nullptr', fontsize=9, ha='left', 
        family='monospace', color='#9E9E9E')
ax2.text(0.65, 2.6, 'size_: 0', fontsize=9, ha='left',
        family='monospace', color='#9E9E9E')
ax2.text(1.6, 2.1, '(有效但不确定)', fontsize=8, ha='center',
        style='italic', color='#F44336')

# 目标对象 dst (获得资源) - 箭头指向堆内存底部中央
draw_object(ax2, 6.3, 2, 'dst', '0x1234', '5', has_arrow=True, arrow_target=(5.5, 4))

# 标注
ax2.text(4.5, 0.5, '资源被"窃取"，非拷贝', fontsize=11, ha='center',
        style='italic',
        bbox=dict(boxstyle='round', facecolor='#E8F5E9', edgecolor='#81C784'))

plt.tight_layout()
plt.savefig('/Users/davidxie/PycharmProjects/writer/cpp基础/images/move_semantics.png', 
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("移动语义示意图已生成")
