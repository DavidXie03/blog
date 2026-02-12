#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C++ 内存布局绘图脚本
用于生成内存布局示意图，展示栈、堆、数据段、代码段的分布
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# 设置字体：使用 Arial Unicode MS，中英文风格统一
# Arial Unicode MS 在 macOS 上完整支持中英文字符，且字体风格一致
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC']
plt.rcParams['axes.unicode_minus'] = False


def draw_memory_layout(output_path: str = None):
    """
    绘制C++内存布局图
    
    Args:
        output_path: 输出图片路径，默认保存到脚本同目录下的 memory_layout.png
    """
    fig, ax = plt.subplots(figsize=(8, 9))

    # 定义内存区域（从上到下：高地址到低地址）
    # 格式: (名称, 描述, 增长方向, y坐标, 高度, 颜色)
    regions = [
        ('栈 Stack', '局部变量、函数参数', '↓ 向下增长', 0.86, 0.10, '#81C784'),
        ('空闲区域', '', '', 0.74, 0.08, '#EEEEEE'),
        ('堆 Heap', '动态分配的内存', '↑ 向上增长', 0.60, 0.10, '#FFB74D'),
        ('.bss 段', '未初始化的全局/静态变量', '', 0.49, 0.07, '#64B5F6'),
        ('.data 段', '已初始化的全局/静态变量', '', 0.39, 0.07, '#4FC3F7'),
        ('.rodata 常量区', '字符串字面量、const全局常量', '', 0.25, 0.08, '#CE93D8'),
        ('.text 代码段', '程序指令', '', 0.14, 0.08, '#F48FB1'),
    ]

    # 绘制数据段外框（包含.bss和.data），使用虚线框样式
    # .data段: y=0.39, h=0.07 → 底部0.39，下边界留0.01间距 → 0.38
    # .bss段: y=0.49, h=0.07 → 顶部0.56，上边界留0.01间距 → 0.57
    data_section_rect = mpatches.FancyBboxPatch(
        (0.13, 0.38), 0.74, 0.19,
        boxstyle='round,pad=0.01',
        facecolor='none',
        edgecolor='#1565C0',  # 蓝色虚线框
        linewidth=2,
        linestyle='--'
    )
    ax.add_patch(data_section_rect)
    # 数据段标签放在右侧
    ax.text(0.89, 0.475, '数据段', ha='left', va='center',
           fontsize=12, color='#1565C0', fontweight='bold')

    # 绘制只读区域外框（包含.rodata常量区和.text代码段）
    # .text段: y=0.14, h=0.08 → 底部0.14，下边界留0.01间距 → 0.13
    # .rodata段: y=0.25, h=0.08 → 顶部0.33，上边界留0.01间距 → 0.34
    readonly_section_rect = mpatches.FancyBboxPatch(
        (0.13, 0.13), 0.74, 0.21,
        boxstyle='round,pad=0.01',
        facecolor='none',
        edgecolor='#7B1FA2',
        linewidth=2,
        linestyle='--'
    )
    ax.add_patch(readonly_section_rect)
    ax.text(0.89, 0.235, '只读区域', ha='left', va='center',
           fontsize=12, color='#7B1FA2', fontweight='bold')

    # 绘制每个内存区域
    for name, desc, growth, y, h, color in regions:
        rect = mpatches.FancyBboxPatch(
            (0.15, y), 0.7, h,
            boxstyle='round,pad=0.01',
            facecolor=color,
            edgecolor='#333333',
            linewidth=1.5
        )
        ax.add_patch(rect)
        
        if name == '空闲区域':
            # 空闲区域使用斜体和双向箭头
            ax.text(0.5, y + h/2, name, ha='center', va='center',
                   fontsize=14, color='#888888', style='italic')
            ax.annotate('', xy=(0.5, y + 0.01), xytext=(0.5, y + h - 0.01),
                       arrowprops=dict(arrowstyle='<->', color='#888888', lw=1.5))
        else:
            # 普通区域显示名称和描述
            ax.text(0.5, y + h/2 + 0.015, name, ha='center', va='center',
                   fontsize=15, fontweight='bold')
            ax.text(0.5, y + h/2 - 0.025, desc, ha='center', va='center',
                   fontsize=12, color='#555555')
        
        # 显示增长方向
        if growth:
            ax.text(0.88, y + h/2, growth, ha='left', va='center',
                   fontsize=12, color='#333333')

    # 添加地址标注
    ax.text(0.08, 0.97, '高地址', ha='center', va='center',
           fontsize=13, fontweight='bold')
    ax.text(0.08, 0.12, '低地址', ha='center', va='center',
           fontsize=13, fontweight='bold')

    # 添加地址方向箭头
    ax.annotate('', xy=(0.08, 0.15), xytext=(0.08, 0.95),
               arrowprops=dict(arrowstyle='->', color='#333333', lw=2))

    # 设置坐标轴
    ax.set_xlim(0, 1)
    ax.set_ylim(0.05, 1)
    ax.axis('off')
    ax.set_title('C++ 程序内存布局', fontsize=18, fontweight='bold', pad=20)

    plt.tight_layout()
    
    # 保存图片
    if output_path is None:
        from pathlib import Path
        output_path = Path(__file__).parent / 'memory_layout.png'
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'图片已保存到: {output_path}')
    
    plt.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='绘制C++内存布局图')
    parser.add_argument('-o', '--output', help='输出文件路径')
    args = parser.parse_args()
    
    draw_memory_layout(output_path=args.output)