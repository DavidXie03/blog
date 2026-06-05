#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
oneof 容器 case 的二维语义分解图
横轴：list / map（以及 map 的 key 类型 int / string）
纵轴：异构容器（值=AttrValue） / 同构特化容器（值=string）
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC']
plt.rcParams['axes.unicode_minus'] = False


def draw_oneof_dimensions(output_path=None):
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis('off')

    # 颜色
    color_list = '#FFCC80'        # 列表：橙
    color_map_int = '#90CAF9'     # int key map：蓝
    color_map_str = '#A5D6A7'     # string key map：绿
    color_homo = '#CE93D8'        # 同构特化：紫

    # 标题
    ax.text(7, 6.5, 'oneof 容器 case 的语义维度分解',
            ha='center', va='center', fontsize=16, fontweight='bold')

    # ─── 列标题 ───
    ax.text(5.0, 5.7, 'list 语义', ha='center', va='center',
            fontsize=13, fontweight='bold', color='#5D4037')
    ax.text(8.5, 5.7, 'map · int key', ha='center', va='center',
            fontsize=13, fontweight='bold', color='#0D47A1')
    ax.text(12.0, 5.7, 'map · string key', ha='center', va='center',
            fontsize=13, fontweight='bold', color='#1B5E20')

    # ─── 行标题 ───
    ax.text(0.3, 4.2, '异构容器', ha='left', va='center',
            fontsize=12, fontweight='bold', color='#333')
    ax.text(0.3, 3.8, 'value = AttrValue', ha='left', va='center',
            fontsize=9, color='#888', style='italic')

    ax.text(0.3, 1.7, '同构特化容器', ha='left', va='center',
            fontsize=12, fontweight='bold', color='#333')
    ax.text(0.3, 1.3, 'value = 固定标量', ha='left', va='center',
            fontsize=9, color='#888', style='italic')

    # ─── 单元格绘制函数 ───
    def cell(x_center, y_center, w, h, title, sub, color):
        rect = mpatches.FancyBboxPatch(
            (x_center - w / 2, y_center - h / 2), w, h,
            boxstyle='round,pad=0.05',
            facecolor=color, edgecolor='#444', linewidth=1.4,
        )
        ax.add_patch(rect)
        ax.text(x_center, y_center + 0.2, title,
                ha='center', va='center',
                fontsize=12, fontweight='bold', color='#1a1a1a')
        ax.text(x_center, y_center - 0.25, sub,
                ha='center', va='center',
                fontsize=9.5, color='#444')

    # ─── 第一行：异构容器 ───
    cell(5.0, 4.0, 2.6, 1.1,
         'ValueList',
         'repeated AttrValue', color_list)

    cell(8.5, 4.0, 2.6, 1.1,
         'IntMap',
         'map<int64, AttrValue>', color_map_int)

    cell(12.0, 4.0, 2.6, 1.1,
         'StringMap',
         'map<string, AttrValue>', color_map_str)

    # ─── 第二行：同构特化容器 ───
    cell(5.0, 1.5, 2.6, 1.1,
         'StringList',
         'repeated string', color_homo)

    # 中间和右侧空白单元（视觉上对齐）
    ax.text(8.5, 1.5, '— 不需要 —', ha='center', va='center',
            fontsize=10, color='#aaa', style='italic')
    ax.text(12.0, 1.5, '— 不需要 —', ha='center', va='center',
            fontsize=10, color='#aaa', style='italic')

    plt.tight_layout()
    if output_path is None:
        output_path = Path(__file__).parent / 'oneof_dimensions.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'图片已保存到: {output_path}')
    plt.close()


if __name__ == '__main__':
    draw_oneof_dimensions()
