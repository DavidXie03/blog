#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
protoc 编译管道示意图
展示一份 .proto 经过 protoc + 各种插件，生成多种语言代码的流程
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC']
plt.rcParams['axes.unicode_minus'] = False


def add_box(ax, x, y, w, h, lines, facecolor, edgecolor='#333',
            fontsize=11, fontweight='normal', text_color='#1a1a1a'):
    rect = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle='round,pad=0.05',
        facecolor=facecolor, edgecolor=edgecolor, linewidth=1.4,
    )
    ax.add_patch(rect)
    if isinstance(lines, str):
        lines = [lines]
    n = len(lines)
    for i, line in enumerate(lines):
        # 多行竖直均布
        offset = (n - 1) / 2 - i
        ax.text(x, y + offset * 0.32, line,
                ha='center', va='center',
                fontsize=fontsize if i == 0 else fontsize - 1,
                fontweight=fontweight if i == 0 else 'normal',
                color=text_color)


def add_arrow(ax, x1, y1, x2, y2, label='', color='#666',
              label_offset=(0, 0.15), label_color='#444', label_fontsize=9):
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle='->,head_length=8,head_width=6',
        color=color, linewidth=1.5,
        shrinkA=5, shrinkB=5,
    )
    ax.add_patch(arrow)
    if label:
        ax.text((x1 + x2) / 2 + label_offset[0],
                (y1 + y2) / 2 + label_offset[1],
                label, ha='center', va='center',
                fontsize=label_fontsize, color=label_color,
                style='italic')


def draw_codegen_pipeline(output_path=None):
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # 颜色
    color_proto = '#FFE082'      # .proto 黄
    color_protoc = '#90CAF9'     # protoc 蓝
    color_builtin = '#A5D6A7'    # 内置插件 绿
    color_external = '#FFAB91'   # 外部插件 橙
    color_output = '#CE93D8'     # 产物 紫

    # 标题
    ax.text(7, 7.5, 'protoc 的代码生成管道',
            ha='center', va='center', fontsize=16, fontweight='bold')

    # ─── 左：输入 .proto ───
    add_box(ax, 1.5, 4.0, 2.0, 1.4,
            ['my_message', '.proto'],
            color_proto, fontsize=12, fontweight='bold')
    ax.text(1.5, 2.9, '协议契约', ha='center', fontsize=10,
            color='#7c5e00', style='italic')

    # ─── 中：protoc ───
    add_box(ax, 5.5, 4.0, 2.6, 2.0,
            ['protoc', '词法 / 语法分析', '构建 FileDescriptor'],
            color_protoc, fontsize=13, fontweight='bold')
    ax.text(5.5, 2.5, 'Protocol Buffer Compiler',
            ha='center', fontsize=10, color='#1565c0', style='italic')

    add_arrow(ax, 2.5, 4.0, 4.2, 4.0)

    # ─── 右：分发到各插件 + 产物 ───
    plugin_x = 9.5
    plugin_w = 2.4
    plugin_h = 0.7
    output_x = 12.5
    output_w = 1.6

    plugins = [
        # (y, label_lines, color, is_builtin)
        (6.5, ['-​-cpp_out'],     color_builtin, True),
        (5.4, ['-​-python_out'],  color_builtin, True),
        (4.3, ['-​-go_out'],      color_external, False),
        (3.2, ['-​-rust_out'],    color_external, False),
        (2.1, ['-​-rpc_out'],     color_external, False),
    ]
    output_labels = [
        '*.pb.h / *.pb.cc',
        '*_pb2.py',
        '*.pb.go',
        '*.rs',
        '*.rpc.pb.*',
    ]

    for (y, label, color, is_builtin), out_label in zip(plugins, output_labels):
        # 中间 → 插件
        add_arrow(ax, 6.8, 4.0, plugin_x - plugin_w / 2, y,
                  color='#666')
        # 插件方块
        add_box(ax, plugin_x, y, plugin_w, plugin_h, label,
                color, fontsize=11, fontweight='bold')
        # 插件 → 产物
        add_arrow(ax, plugin_x + plugin_w / 2, y,
                  output_x - output_w / 2, y,
                  color='#888')
        # 产物
        add_box(ax, output_x, y, output_w, plugin_h * 0.85,
                out_label, color_output,
                fontsize=10)

    # 内置 vs 外部 图例
    legend_y = 0.6
    add_box(ax, 9.6, legend_y, 1.0, 0.4, '', color_builtin)
    ax.text(10.3, legend_y, 'protoc 内置', va='center', fontsize=10)
    add_box(ax, 12.0, legend_y, 1.0, 0.4, '', color_external)
    ax.text(12.7, legend_y, '外部插件', va='center', fontsize=10)

    plt.tight_layout()
    if output_path is None:
        output_path = Path(__file__).parent / 'codegen_pipeline.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'图片已保存到: {output_path}')
    plt.close()


if __name__ == '__main__':
    draw_codegen_pipeline()
