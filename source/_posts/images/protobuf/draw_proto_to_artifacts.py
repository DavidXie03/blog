#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一份 .proto 到两份产物的分叉示意图
展示 vanilla -​-cpp_out 和 RPC 框架插件分别从同一份 .proto 生成不同产物
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC']
plt.rcParams['axes.unicode_minus'] = False


def add_box(ax, x, y, w, h, lines, facecolor, edgecolor='#333',
            fontsize=11, fontweight='normal', text_color='#1a1a1a',
            line_height=0.32, title_extra_size=0):
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
        offset = (n - 1) / 2 - i
        ax.text(x, y + offset * line_height, line,
                ha='center', va='center',
                fontsize=fontsize + (title_extra_size if i == 0 else 0),
                fontweight=fontweight if i == 0 else 'normal',
                color=text_color)


def add_arrow(ax, x1, y1, x2, y2, label='', color='#555',
              label_offset=(0.3, 0), label_color='#444',
              label_fontsize=10, linestyle='-'):
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle='->,head_length=10,head_width=7',
        color=color, linewidth=1.6,
        shrinkA=5, shrinkB=5,
        linestyle=linestyle,
    )
    ax.add_patch(arrow)
    if label:
        ax.text((x1 + x2) / 2 + label_offset[0],
                (y1 + y2) / 2 + label_offset[1],
                label, ha='center', va='center',
                fontsize=label_fontsize, color=label_color,
                style='italic')


def draw_proto_to_artifacts(output_path=None):
    fig, ax = plt.subplots(figsize=(13, 8.5))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # 颜色
    color_proto = '#FFE082'
    color_vanilla = '#A5D6A7'   # 绿，vanilla
    color_rpc_plugin = '#FFAB91'  # 橙，RPC 插件
    color_pb_artifact = '#C8E6C9'   # 浅绿
    color_rpc_artifact = '#FFCCBC'  # 浅橙

    ax.text(7, 9.5, '一份 .proto，两份产物',
            ha='center', va='center', fontsize=16, fontweight='bold')

    # ─── 顶部：.proto 文件 ───
    add_box(ax, 7, 8.0, 6.0, 1.7,
            ['log_service.proto',
             'service LogsService { rpc Export(...) ... }',
             'message ExportLogsRequest { ... }'],
            color_proto, fontsize=12, fontweight='bold',
            line_height=0.36)

    # ─── 分叉：左到 vanilla codegen，右到 RPC 插件 ───
    add_arrow(ax, 5.5, 7.15, 3.3, 6.2,
              label='-​-cpp_out', label_offset=(-0.4, 0.2),
              label_color='#1b5e20')
    add_arrow(ax, 8.5, 7.15, 10.7, 6.2,
              label='-​-grpc_out', label_offset=(0.4, 0.2),
              label_color='#bf360c')

    # ─── 第二层：两个 codegen ───
    add_box(ax, 3.3, 5.4, 3.4, 1.2,
            ['protoc 内置 cpp 插件', '处理 message'],
            color_vanilla, fontsize=12, fontweight='bold')

    add_box(ax, 10.7, 5.4, 3.4, 1.2,
            ['grpc_cpp_plugin', '处理 service / rpc'],
            color_rpc_plugin, fontsize=12, fontweight='bold')

    add_arrow(ax, 3.3, 4.7, 3.3, 3.7)
    add_arrow(ax, 10.7, 4.7, 10.7, 3.7)

    # ─── 第三层：产物 ───
    # 左：vanilla 产物
    add_box(ax, 3.3, 2.6, 4.5, 2.0,
            ['*.pb.h / *.pb.cc',
             '',
             '• 每个 message 一个 C++ 类',
             '• 字段访问器（get/set/mutable）',
             '• SerializeToString / ParseFromString',
             '• 反射元信息（Descriptor）'],
            color_pb_artifact, fontsize=11, fontweight='bold',
            line_height=0.26)

    # 右：RPC 插件产物
    add_box(ax, 10.7, 2.6, 4.5, 2.0,
            ['*.grpc.pb.h / *.grpc.pb.cc',
             '',
             '• 服务端基类（业务 override）',
             '• 客户端 Stub（同步/异步）',
             '• 方法名注册到框架',
             '• 转发到 BlockingUnaryCall 等模板'],
            color_rpc_artifact, fontsize=11, fontweight='bold',
            line_height=0.26)

    # 底部说明：右侧产物 #include 左侧
    add_arrow(ax, 5.6, 2.6, 8.4, 2.6,
              label='#include', label_offset=(0, 0.25),
              label_color='#444', linestyle='--', color='#888')

    # 底部一行小字
    ax.text(7, 0.45,
            'vanilla codegen 关心数据结构，gRPC 插件关心服务接口；两者通过 #include 串起来',
            ha='center', va='center', fontsize=11, color='#555', style='italic')

    plt.tight_layout()
    if output_path is None:
        output_path = Path(__file__).parent / 'proto_to_artifacts.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'图片已保存到: {output_path}')
    plt.close()


if __name__ == '__main__':
    draw_proto_to_artifacts()
