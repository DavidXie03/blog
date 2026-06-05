#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Varint 编码示意图
展示 300 如何被 protobuf 的 varint 编码成 2 字节
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC']
plt.rcParams['axes.unicode_minus'] = False


def draw_byte_box(ax, x, y, w, h, text, facecolor, edgecolor='#333',
                  fontsize=14, fontweight='normal', text_color='#1a1a1a'):
    rect = mpatches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle='round,pad=0.01',
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.5,
    )
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, text,
            ha='center', va='center',
            fontsize=fontsize, fontweight=fontweight, color=text_color)


def draw_varint_300(output_path=None):
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis('off')

    # 颜色
    color_bin_high = '#E1BEE7'  # 高位 7 bit 浅紫
    color_bin_low = '#C5E1A5'   # 低位 7 bit 浅绿
    color_flag_more = '#FFB74D'  # 标志位 1 浅橙
    color_flag_end = '#90CAF9'  # 标志位 0 浅蓝
    color_byte = '#FFF59D'      # 最终字节浅黄

    # 标题
    ax.text(5, 6.6, 'Varint 编码示例：300', ha='center', va='center',
            fontsize=17, fontweight='bold')

    # ─── 第 1 行：原始二进制 ───
    ax.text(0.3, 5.5, '①  二进制：', ha='left', va='center',
            fontsize=13, fontweight='bold')

    bits_300 = '100101100'  # 9 位
    # 把 9 位摆到右侧，按 1 位/格
    bits_x_start = 3.0
    bit_w = 0.45
    for i, b in enumerate(bits_300):
        # 高 2 位用紫色，低 7 位用绿色
        bg = color_bin_high if i < 2 else color_bin_low
        draw_byte_box(ax, bits_x_start + i * bit_w, 5.25, bit_w * 0.92, 0.55,
                      b, bg, fontsize=14)

    ax.text(bits_x_start + 9 * bit_w + 0.3, 5.5, '= 300 (9 位)',
            ha='left', va='center', fontsize=12, color='#555')

    # 标注高 / 低
    ax.text(bits_x_start + bit_w, 5.95, '高 2 位', ha='center', va='bottom',
            fontsize=10, color='#7B1FA2')
    ax.text(bits_x_start + 5.5 * bit_w, 5.95, '低 7 位', ha='center', va='bottom',
            fontsize=10, color='#558B2F')

    # ─── 第 2 行：切分 ───
    ax.text(0.3, 4.0, '②  按 7 bit 切：', ha='left', va='center',
            fontsize=13, fontweight='bold')

    # 低 7 位
    ax.text(2.6, 4.0, '低 7 位:', ha='right', va='center', fontsize=12)
    low7 = '0101100'
    for i, b in enumerate(low7):
        draw_byte_box(ax, 2.8 + i * bit_w, 3.75, bit_w * 0.92, 0.5,
                      b, color_bin_low, fontsize=13)
    ax.text(2.8 + 7 * bit_w + 0.3, 4.0, '= 0x2C',
            ha='left', va='center', fontsize=12, color='#555')

    # 高 2 位（左侧补 5 个 0）
    ax.text(2.6, 3.1, '高 2 位:', ha='right', va='center', fontsize=12)
    high2 = '0000010'  # 补到 7 位
    for i, b in enumerate(high2):
        bg = color_bin_high if i >= 5 else '#F3E5F5'
        draw_byte_box(ax, 2.8 + i * bit_w, 2.85, bit_w * 0.92, 0.5,
                      b, bg, fontsize=13)
    ax.text(2.8 + 7 * bit_w + 0.3, 3.1, '= 0x02 (补到 7 位)',
            ha='left', va='center', fontsize=12, color='#555')

    # ─── 第 3 行：加标志位 ───
    ax.text(0.3, 1.95, '③  加标志位：', ha='left', va='center',
            fontsize=13, fontweight='bold')

    # 第一字节（low7 + 标志位 1）
    ax.text(2.6, 1.95, '字节 1:', ha='right', va='center', fontsize=12)
    # 标志位 1
    draw_byte_box(ax, 2.8, 1.7, bit_w * 0.92, 0.5,
                  '1', color_flag_more, fontsize=13, fontweight='bold')
    # 接 7 个 bit
    for i, b in enumerate(low7):
        draw_byte_box(ax, 2.8 + (i + 1) * bit_w, 1.7, bit_w * 0.92, 0.5,
                      b, color_bin_low, fontsize=13)
    ax.text(2.8 + 8 * bit_w + 0.3, 1.95, '→ 0xAC',
            ha='left', va='center', fontsize=13,
            fontweight='bold', color='#bf360c')

    # 第二字节（high2 + 标志位 0）
    ax.text(2.6, 1.05, '字节 2:', ha='right', va='center', fontsize=12)
    draw_byte_box(ax, 2.8, 0.8, bit_w * 0.92, 0.5,
                  '0', color_flag_end, fontsize=13, fontweight='bold')
    for i, b in enumerate(high2):
        bg = color_bin_high if i >= 5 else '#F3E5F5'
        draw_byte_box(ax, 2.8 + (i + 1) * bit_w, 0.8, bit_w * 0.92, 0.5,
                      b, bg, fontsize=13)
    ax.text(2.8 + 8 * bit_w + 0.3, 1.05, '→ 0x02',
            ha='left', va='center', fontsize=13,
            fontweight='bold', color='#bf360c')

    # 标志位说明（图例）
    legend_y = 0.05
    draw_byte_box(ax, 0.5, legend_y, 0.4, 0.4, '1', color_flag_more, fontsize=11)
    ax.text(1.0, legend_y + 0.2, '后面还有更多组', va='center', fontsize=10, color='#555')

    draw_byte_box(ax, 3.3, legend_y, 0.4, 0.4, '0', color_flag_end, fontsize=11)
    ax.text(3.8, legend_y + 0.2, '这是最后一组', va='center', fontsize=10, color='#555')

    # 最终结果
    ax.text(7.0, legend_y + 0.2, '最终: AC 02 (2 字节)',
            ha='left', va='center', fontsize=12, fontweight='bold', color='#bf360c')

    plt.tight_layout()
    if output_path is None:
        output_path = Path(__file__).parent / 'varint_300.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'图片已保存到: {output_path}')
    plt.close()


if __name__ == '__main__':
    draw_varint_300()
