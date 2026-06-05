#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wire format 字节布局对比图
对比 map<int64, float> 和 map<string, float> 编码同一项数据时的字节布局差异
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC']
plt.rcParams['axes.unicode_minus'] = False


# 颜色：Tag 一种、Length 一种、Key 数据一种、Value 数据一种、外壳一种
COLOR_OUTER_TAG = '#90A4AE'   # 外层 tag/length 灰蓝
COLOR_INNER_TAG = '#B0BEC5'   # 内层 tag/length 浅灰蓝
COLOR_KEY_DATA = '#FFE082'    # key 黄
COLOR_VAL_DATA = '#A5D6A7'    # value 绿
COLOR_HIGHLIGHT = '#EF9A9A'   # 突出多出的字节（差额）红


def byte_cell(ax, x, y, w, h, hex_str, label, color, edgecolor='#444',
              fontsize_hex=11, fontsize_label=8, label_color='#555'):
    """绘制一个字节单元：上半显示 hex 值，下方显示语义标签。"""
    rect = mpatches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle='round,pad=0.005',
        facecolor=color, edgecolor=edgecolor, linewidth=1.2,
    )
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, hex_str,
            ha='center', va='center', fontsize=fontsize_hex, fontweight='bold')
    if label:
        ax.text(x + w / 2, y - 0.18, label,
                ha='center', va='top',
                fontsize=fontsize_label, color=label_color)


def draw_panel(ax, y_top, title, total_size, bytes_def, highlight_range=None):
    """
    bytes_def: list of (hex_str, semantic_label, color, width_factor)
    width_factor: 多字节组在视觉上占的格子数（如 5B varint 占 5 格）
    """
    cell_w = 0.7
    gap = 0.05
    h = 0.7
    x = 0.5

    # 标题
    ax.text(0.3, y_top + 1.15, title,
            ha='left', va='center', fontsize=13, fontweight='bold')
    ax.text(13.5, y_top + 1.15, f'总计 {total_size} 字节',
            ha='right', va='center', fontsize=12, color='#bf360c',
            fontweight='bold')

    # 绘制每个字节
    for hex_str, label, color, width in bytes_def:
        cell_total_w = cell_w * width + gap * (width - 1)
        byte_cell(ax, x, y_top, cell_total_w, h, hex_str, label, color)
        x += cell_total_w + gap

    # 高亮多出的部分
    if highlight_range is not None:
        x_start, x_end = highlight_range
        rect = mpatches.Rectangle(
            (x_start - 0.05, y_top - 0.5),
            x_end - x_start + 0.1, h + 0.7,
            facecolor='none', edgecolor='#d32f2f',
            linewidth=2, linestyle='--'
        )
        ax.add_patch(rect)
        ax.text((x_start + x_end) / 2, y_top - 0.6, '↑ 多出的 6 字节',
                ha='center', va='top', fontsize=11,
                color='#d32f2f', fontweight='bold')


def draw_wire_format_bytes(output_path=None):
    fig, ax = plt.subplots(figsize=(13.5, 7.5))
    ax.set_xlim(0, 14)
    ax.set_ylim(-0.5, 7.5)
    ax.axis('off')

    # 总标题
    ax.text(7, 7.2, 'Wire format 字节布局对比：map 编码同一项数据',
            ha='center', va='center', fontsize=15, fontweight='bold')
    ax.text(7, 6.75, 'data[1700000001] = 0.92',
            ha='center', va='center', fontsize=12, color='#555')

    # ─── 上面板：map<int64, float> ───
    bytes_int = [
        ('0A', 'data tag', COLOR_OUTER_TAG, 1),
        ('0D', 'len=13', COLOR_OUTER_TAG, 1),
        ('08', 'key tag', COLOR_INNER_TAG, 1),
        ('81 ED B0 BA 06', 'varint(1700000001)', COLOR_KEY_DATA, 5),
        ('12', 'val tag', COLOR_INNER_TAG, 1),
        ('05', 'len=5', COLOR_INNER_TAG, 1),
        ('15', 'float tag', COLOR_INNER_TAG, 1),
        ('XX XX XX XX', 'IEEE754(0.92)', COLOR_VAL_DATA, 4),
    ]
    draw_panel(ax, 4.5, 'map<int64, float>', 15, bytes_int)

    # ─── 下面板：map<string, float> ───
    bytes_str = [
        ('0A', 'data tag', COLOR_OUTER_TAG, 1),
        ('13', 'len=19', COLOR_OUTER_TAG, 1),
        ('0A', 'key tag', COLOR_INNER_TAG, 1),
        ('0A', 'len=10', COLOR_HIGHLIGHT, 1),
        ('"1700000001"', '10 字节 ASCII', COLOR_HIGHLIGHT, 5),
        ('12', 'val tag', COLOR_INNER_TAG, 1),
        ('05', 'len=5', COLOR_INNER_TAG, 1),
        ('15', 'float tag', COLOR_INNER_TAG, 1),
        ('XX XX XX XX', 'IEEE754(0.92)', COLOR_VAL_DATA, 4),
    ]
    # 高亮范围（单位 ax 坐标系）：
    #   前 3 字节：0A 13 0A 占 3*(0.7+0.05)=2.25，从 x=0.5 开始 → 到 x=2.75
    #   差额是接着的 1B(0A=len) + 5B(string) - 5B(varint) 那一段
    # 简化：高亮 "0A" len byte + "1700000001" 那 5 格区域（视觉上比 int64 版本多出 6B）
    # 实际计算：cell_w=0.7, gap=0.05, h=0.7; x_start_of_highlight 对应 "len=10" 字节
    # 经过：tag(1)+len(1)+keytag(1) = 3 个单元
    cell_w, gap = 0.7, 0.05
    x_start = 0.5 + 3 * (cell_w + gap)
    x_end = x_start + 1 * cell_w + gap + 5 * cell_w + 4 * gap
    draw_panel(ax, 1.6, 'map<string, float>', 21, bytes_str,
               highlight_range=(x_start, x_end))

    # 图例
    legend_y = -0.1
    legend_items = [
        ('外层 tag / 长度', COLOR_OUTER_TAG),
        ('内层 tag / 长度', COLOR_INNER_TAG),
        ('Key 数据', COLOR_KEY_DATA),
        ('Value 数据', COLOR_VAL_DATA),
    ]
    lx = 1.0
    for text, color in legend_items:
        rect = mpatches.FancyBboxPatch(
            (lx, legend_y), 0.4, 0.3,
            boxstyle='round,pad=0.01',
            facecolor=color, edgecolor='#444', linewidth=1)
        ax.add_patch(rect)
        ax.text(lx + 0.5, legend_y + 0.15, text, va='center', fontsize=10)
        lx += 3.0

    plt.tight_layout()
    if output_path is None:
        output_path = Path(__file__).parent / 'wire_format_bytes.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'图片已保存到: {output_path}')
    plt.close()


if __name__ == '__main__':
    draw_wire_format_bytes()
