#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工业界协议特化光谱：从通用到特化，5 档（L0~L4）
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC']
plt.rcParams['axes.unicode_minus'] = False


def draw_spectrum(output_path=None):
    fig, ax = plt.subplots(figsize=(14, 6.2))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis('off')

    # 标题
    ax.text(7, 6.6, '协议特化光谱：通用 ←——→ 特化',
            ha='center', va='center', fontsize=15, fontweight='bold')

    # ─── 顶部坐标轴：通用 ←──→ 特化 ───
    ax.annotate('',
                xy=(13.4, 5.85), xytext=(0.6, 5.85),
                arrowprops=dict(arrowstyle='<->', color='#666', lw=1.2))
    ax.text(0.5, 5.85, '通用', ha='right', va='center',
            fontsize=11, color='#444', fontweight='bold')
    ax.text(13.5, 5.85, '特化', ha='left', va='center',
            fontsize=11, color='#444', fontweight='bold')

    # 维度提示（顶部，三组对照）
    dim_y = 5.25
    ax.text(0.5, dim_y, '最灵活 / 最大字节 / 最易演进',
            ha='left', va='center', fontsize=9.5,
            color='#888', style='italic')
    ax.text(13.5, dim_y, '最快 / 最小字节 / 最难演进',
            ha='right', va='center', fontsize=9.5,
            color='#888', style='italic')

    # ─── 5 个档位色块 ───
    # 每档颜色：从冷到暖
    levels = [
        ('L0', 'JSON / XML',           '#BBDEFB'),  # 浅蓝
        ('L1', 'Protobuf\ndefault',     '#C5E1A5'),  # 浅绿
        ('L2', 'Protobuf +\n领域 oneof 特化', '#FFCC80'),  # 浅橙（高亮）
        ('L3', 'FlatBuffers /\nCap\'n Proto', '#FFAB91'),  # 橙
        ('L4', 'SBE / 手写二进制\n（高频交易）', '#EF9A9A'),  # 浅红
    ]

    box_y = 2.6      # 色块底
    box_h = 1.8      # 色块高
    box_w = 2.3      # 色块宽
    gap = 0.4        # 色块间距
    total_w = 5 * box_w + 4 * gap   # = 13.1
    start_x = (14 - total_w) / 2    # = 0.45

    box_centers = []
    for i, (lvl, name, color) in enumerate(levels):
        x = start_x + i * (box_w + gap)
        is_highlight = (i == 2)  # L2

        # 色块
        edge_color = '#C62828' if is_highlight else '#444'
        edge_width = 2.5 if is_highlight else 1.2
        rect = FancyBboxPatch(
            (x, box_y), box_w, box_h,
            boxstyle='round,pad=0.05',
            facecolor=color, edgecolor=edge_color, linewidth=edge_width,
        )
        ax.add_patch(rect)

        # 档位标识（大字）
        ax.text(x + box_w / 2, box_y + box_h - 0.45, lvl,
                ha='center', va='center', fontsize=18, fontweight='bold',
                color='#1a1a1a')

        # 协议名（多行）
        ax.text(x + box_w / 2, box_y + 0.55, name,
                ha='center', va='center', fontsize=10.5,
                color='#222')

        box_centers.append(x + box_w / 2)

    # ─── L2 标注（"多数大型业务在这一档"） ───
    l2_cx = box_centers[2]
    ax.annotate(
        '多数大型业务在这一档',
        xy=(l2_cx, box_y + box_h + 0.05),
        xytext=(l2_cx, box_y + box_h + 0.85),
        ha='center', va='center', fontsize=11,
        color='#C62828', fontweight='bold',
        arrowprops=dict(arrowstyle='->', color='#C62828', lw=1.5),
    )

    # ─── 档间箭头与收益标注（底部） ───
    gains = [
        '-50% 字节\n-80% CPU',
        '-10~30%\n字节',
        '-20~50% 字节\n零拷贝场景\n-90% CPU',
        '极端定制',
    ]

    arrow_y = box_y - 0.15
    label_y = arrow_y - 0.7

    for i in range(4):
        x_from = box_centers[i] + box_w / 2 - 0.1
        x_to = box_centers[i + 1] - box_w / 2 + 0.1
        # 箭头
        arr = FancyArrowPatch(
            (x_from, arrow_y), (x_to, arrow_y),
            arrowstyle='->,head_length=8,head_width=6',
            color='#555', linewidth=1.4,
        )
        ax.add_patch(arr)

        # 收益标签
        mid_x = (x_from + x_to) / 2
        ax.text(mid_x, label_y, gains[i],
                ha='center', va='center', fontsize=9.5,
                color='#5D4037', style='italic')

    plt.tight_layout()
    if output_path is None:
        output_path = Path(__file__).parent / 'specialization_spectrum.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'图片已保存到: {output_path}')
    plt.close()


if __name__ == '__main__':
    draw_spectrum()
