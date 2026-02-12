import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Ellipse
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(1, 1, figsize=(8, 5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis('off')

# 颜色定义
color_lvalue = '#4CAF50'      # 绿色
color_prvalue = '#2196F3'     # 蓝色
color_xvalue = '#9C27B0'      # 紫色
color_glvalue = '#C8E6C9'     # 浅绿
color_rvalue = '#BBDEFB'      # 浅蓝

# 使用椭圆绘制韦恩图样式
# glvalue 椭圆 (左侧)
glvalue_ellipse = Ellipse((3.5, 2.8), 5, 3.5, 
                           facecolor=color_glvalue, edgecolor='#388E3C', 
                           linewidth=2, alpha=0.6)
ax.add_patch(glvalue_ellipse)

# rvalue 椭圆 (右侧) 
rvalue_ellipse = Ellipse((6.5, 2.8), 5, 3.5,
                          facecolor=color_rvalue, edgecolor='#1976D2', 
                          linewidth=2, alpha=0.6)
ax.add_patch(rvalue_ellipse)

# 标签 - glvalue
ax.text(1.2, 4.8, 'glvalue', fontsize=13, ha='center', 
        fontweight='bold', color='#388E3C')
ax.text(1.2, 4.4, '(泛左值)', fontsize=11, ha='center', color='#388E3C')
ax.text(1.2, 4.0, '有身份', fontsize=10, ha='center', 
        style='italic', color='#388E3C')

# 标签 - rvalue
ax.text(8.8, 4.8, 'rvalue', fontsize=13, ha='center', 
        fontweight='bold', color='#1976D2')
ax.text(8.8, 4.4, '(右值)', fontsize=11, ha='center', color='#1976D2')
ax.text(8.8, 4.0, '可移动', fontsize=10, ha='center', 
        style='italic', color='#1976D2')

# lvalue 区域 (左侧独立区域)
lvalue_box = FancyBboxPatch((1.3, 1.8), 2.2, 1.8,
                             boxstyle="round,pad=0.05,rounding_size=0.2",
                             facecolor=color_lvalue, edgecolor='#2E7D32',
                             linewidth=2, alpha=0.9)
ax.add_patch(lvalue_box)
ax.text(2.4, 3.15, 'lvalue', fontsize=14, ha='center', 
        fontweight='bold', color='white')
ax.text(2.4, 2.7, '(左值)', fontsize=11, ha='center', color='white')
ax.text(2.4, 2.2, '变量名、*ptr', fontsize=10, ha='center', color='white')

# xvalue 区域 (中间交叉区域)
xvalue_box = FancyBboxPatch((4.15, 1.8), 1.7, 1.8,
                             boxstyle="round,pad=0.05,rounding_size=0.2",
                             facecolor=color_xvalue, edgecolor='#7B1FA2',
                             linewidth=2, alpha=0.9)
ax.add_patch(xvalue_box)
ax.text(5, 3.15, 'xvalue', fontsize=14, ha='center', 
        fontweight='bold', color='white')
ax.text(5, 2.7, '(将亡值)', fontsize=11, ha='center', color='white')
ax.text(5, 2.2, 'std::move()', fontsize=10, ha='center', color='white')

# prvalue 区域 (右侧独立区域)
prvalue_box = FancyBboxPatch((6.5, 1.8), 2.2, 1.8,
                              boxstyle="round,pad=0.05,rounding_size=0.2",
                              facecolor=color_prvalue, edgecolor='#1565C0',
                              linewidth=2, alpha=0.9)
ax.add_patch(prvalue_box)
ax.text(7.6, 3.15, 'prvalue', fontsize=14, ha='center', 
        fontweight='bold', color='white')
ax.text(7.6, 2.7, '(纯右值)', fontsize=11, ha='center', color='white')
ax.text(7.6, 2.2, '字面量、x+y', fontsize=10, ha='center', color='white')

# 添加标题
ax.text(5, 5.5, 'C++11 值类别体系', fontsize=16, ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig('/Users/davidxie/PycharmProjects/writer/cpp基础/images/value_category.png', 
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("值类别体系图已生成")
