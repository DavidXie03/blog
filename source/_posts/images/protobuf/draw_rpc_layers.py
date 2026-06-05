#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPC 调用的分层架构图
从业务代码到操作系统，展示 codegen 产物 / protobuf runtime / RPC 框架 / 网络栈
之间的依赖关系
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC']
plt.rcParams['axes.unicode_minus'] = False


def add_layer(ax, y, w, h, x_center, title, sub, color, role,
              role_color='#666'):
    rect = FancyBboxPatch(
        (x_center - w / 2, y - h / 2), w, h,
        boxstyle='round,pad=0.05',
        facecolor=color, edgecolor='#333', linewidth=1.5,
    )
    ax.add_patch(rect)
    ax.text(x_center, y + 0.18, title,
            ha='center', va='center',
            fontsize=12.5, fontweight='bold', color='#1a1a1a')
    ax.text(x_center, y - 0.18, sub,
            ha='center', va='center',
            fontsize=10, color='#444')
    # 右侧职责说明
    ax.text(x_center + w / 2 + 0.4, y, role,
            ha='left', va='center',
            fontsize=10, color=role_color, style='italic')


def add_arrow(ax, x, y1, y2, label='', color='#666',
              label_color='#444', label_x_offset=-0.25):
    arrow = FancyArrowPatch(
        (x, y1), (x, y2),
        arrowstyle='->,head_length=10,head_width=7',
        color=color, linewidth=1.6,
        shrinkA=2, shrinkB=2,
    )
    ax.add_patch(arrow)
    if label:
        ax.text(x + label_x_offset, (y1 + y2) / 2, label,
                ha='right', va='center',
                fontsize=9.5, color=label_color, style='italic')


def draw_rpc_layers(output_path=None):
    fig, ax = plt.subplots(figsize=(11, 9))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10.5)
    ax.axis('off')

    ax.text(6, 9.9, 'RPC 调用的分层架构', ha='center', va='center',
            fontsize=16, fontweight='bold')

    # 颜色（自顶向下）
    colors = {
        'biz': '#FFCCBC',
        'gen': '#FFE082',
        'pb': '#A5D6A7',
        'rpc': '#90CAF9',
        'os': '#CE93D8',
    }

    # 各层位置
    x_center = 4.5
    layer_w = 5.5
    layer_h = 1.0

    layers = [
        # (y, title, sub, color, role)
        (8.5, '业务代码', 'stub.Export(req, &rsp)',
         colors['biz'], '业务侧调用一行'),
        (6.9, '生成代码 (*.pb.cc 与 *.grpc.pb.cc)',
         'message 类 + 服务端基类 + 客户端代理',
         colors['gen'], '由 protoc + 插件生成'),
        (5.3, 'protobuf runtime 库',
         '二进制字节编解码 / Arena 内存',
         colors['pb'], '把对象转成字节，反之亦然'),
        (3.7, 'RPC 框架运行时',
         '网络传输 / 服务发现 / 重试 / 负载均衡',
         colors['rpc'], '把字节送上网线'),
        (2.1, '操作系统 TCP/IP 栈',
         'socket / 协议栈',
         colors['os'], '内核态'),
    ]

    for y, title, sub, color, role in layers:
        add_layer(ax, y, layer_w, layer_h, x_center, title, sub, color, role)

    # 箭头：自顶向下，每层之间
    arrow_x = x_center
    edges = [
        (8.5 - layer_h / 2, 6.9 + layer_h / 2, '调用'),
        (6.9 - layer_h / 2, 5.3 + layer_h / 2, '引用'),
        (5.3 - layer_h / 2, 3.7 + layer_h / 2, '由框架调用'),
        (3.7 - layer_h / 2, 2.1 + layer_h / 2, 'send / recv'),
    ]
    for y1, y2, label in edges:
        add_arrow(ax, arrow_x, y1, y2, label=label)

    # 底部小字总结
    ax.text(6, 0.6,
            '序列化和传输是正交的：可以用 protobuf 走自定义 TCP，也可以用 JSON 走 gRPC',
            ha='center', va='center', fontsize=10.5, color='#555', style='italic')

    plt.tight_layout()
    if output_path is None:
        output_path = Path(__file__).parent / 'rpc_layers.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'图片已保存到: {output_path}')
    plt.close()


if __name__ == '__main__':
    draw_rpc_layers()
