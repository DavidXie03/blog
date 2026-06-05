#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wire format 字节布局对比图（list 篇）
对比 StringList（repeated string）和 ValueList（repeated AttrValue）
装同一个字符串元素 "hello" 时的字节布局差异
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC']
plt.rcParams['axes.unicode_minus'] = False


# 颜色和原 wire_format_bytes.py 保持一致
COLOR_OUTER_TAG = '#90A4AE'   # 外层 tag/length 灰蓝
COLOR_INNER_TAG = '#B0BEC5'   # 内层 tag/length 浅灰蓝
COLOR_VAL_DATA = '#A5D6A7'    # value 数据 绿
COLOR_HIGHLIGHT = '#EF9A9A'   # 突出多出的字节（差额）红


def byte_cell(ax, x, y, w, h, hex_str, label, color, edgecolor='#444',
              fontsize_hex=11, fontsize_label=8, label_color='#555'):
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


def draw_panel(ax, y_top, title, total_size, bytes_def, highlight_range=None,
               highlight_label=''):
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
        ax.text((x_start + x_end) / 2, y_top - 0.6, highlight_label,
                ha='center', va='top', fontsize=11,
                color='#d32f2f', fontweight='bold')


def draw_wire_format_bytes_list(output_path=None):
    fig, ax = plt.subplots(figsize=(13.5, 7.5))
    ax.set_xlim(0, 14)
    ax.set_ylim(-0.5, 7.5)
    ax.axis('off')

    # 总标题
    ax.text(7, 7.2, 'Wire format 字节布局对比：list 装一个字符串元素',
            ha='center', va='center', fontsize=15, fontweight='bold')
    ax.text(7, 6.75, 'elements = ["hello"]',
            ha='center', va='center', fontsize=12, color='#555')

    # ─── 上面板：StringList = repeated string ───
    # field 1, wire type 2 (LENGTH_DELIMITED) → tag = 0x0A
    # length = 5, "hello"
    bytes_homo = [
        ('0A', 'tag (elements)', COLOR_OUTER_TAG, 1),
        ('05', 'len=5', COLOR_OUTER_TAG, 1),
        ('"hello"', '5 字节 ASCII', COLOR_VAL_DATA, 5),
    ]
    draw_panel(ax, 4.5, 'StringList = repeated string', 7, bytes_homo)

    # ─── 下面板：ValueList = repeated AttrValue ───
    # 外层 elements: field 1, wire type 2 → 0x0A
    # 外层 length = 7（内层 AttrValue 字节数）
    # 内层 AttrValue.string_value: field 2, wire type 2 → 0x12
    # 内层 length = 5
    # "hello"
    bytes_hetero = [
        ('0A', 'tag (elements)', COLOR_OUTER_TAG, 1),
        ('07', 'len=7', COLOR_OUTER_TAG, 1),
        ('12', 'tag (string_value)', COLOR_HIGHLIGHT, 1),
        ('05', 'len=5', COLOR_HIGHLIGHT, 1),
        ('"hello"', '5 字节 ASCII', COLOR_VAL_DATA, 5),
    ]
    # 高亮多出的 2 字节（AttrValue wrapper 的内层 tag + length）
    cell_w, gap = 0.7, 0.05
    x_start = 0.5 + 2 * (cell_w + gap)        # 第 3 个单元起（内层 tag）
    x_end = x_start + 2 * cell_w + 1 * gap    # 高亮 2 个单元（内层 tag + 内层 length）
    draw_panel(ax, 1.6, 'ValueList = repeated AttrValue', 9, bytes_hetero,
               highlight_range=(x_start, x_end),
               highlight_label='↑ AttrValue wrapper 多出的 2 字节')

    # 图例
    legend_y = -0.1
    legend_items = [
        ('外层 tag / 长度', COLOR_OUTER_TAG),
        ('内层 wrapper（多出）', COLOR_HIGHLIGHT),
        ('Value 数据', COLOR_VAL_DATA),
    ]
    lx = 1.5
    for text, color in legend_items:
        rect = mpatches.FancyBboxPatch(
            (lx, legend_y), 0.4, 0.3,
            boxstyle='round,pad=0.01',
            facecolor=color, edgecolor='#444', linewidth=1)
        ax.add_patch(rect)
        ax.text(lx + 0.5, legend_y + 0.15, text, va='center', fontsize=10)
        lx += 4.0

    plt.tight_layout()
    if output_path is None:
        output_path = Path(__file__).parent / 'wire_format_bytes_list.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'图片已保存到: {output_path}')
    plt.close()


if __name__ == '__main__':
    draw_wire_format_bytes_list()
