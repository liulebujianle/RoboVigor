#!/usr/bin/env python3
"""仿真专用：键盘输入与独立速度看门狗；不连接真实底盘。"""

import argparse
import math
import select
import sys
import termios
import time
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


ZERO = (0.0, 0.0, 0.0)


def command_for_key(key, linear, angular):
    """速度按车体坐标解释：x 前、y 左、z 轴逆时针旋转。"""
    return {
        'w': (linear, 0.0, 0.0), 's': (-linear, 0.0, 0.0),
        'a': (0.0, linear, 0.0), 'd': (0.0, -linear, 0.0),
        'q': (0.0, 0.0, angular), 'e': (0.0, 0.0, -angular),
    }.get(key.lower(), ZERO)


def fresh_command(command, last_received, now, timeout):
    """使用单调时钟检查失联，不受 Gazebo 暂停或重置时间影响。"""
    if last_received is None or now - last_received >= timeout:
        return ZERO
    return command


def as_twist(command):
    msg = Twist()
    msg.linear.x, msg.linear.y, msg.angular.z = command
    return msg


class VelocityGuard(Node):
    """独立进程：输入失联 0.5 秒后，持续向插件发布零速度。"""

    def __init__(self):
        super().__init__('simulation_velocity_guard')
        self.command = ZERO
        self.last_received = None
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 1)
        self.subscription = self.create_subscription(
            Twist, '/teleop/cmd_vel', self.receive, 1)
        self.timer = self.create_timer(0.05, self.update)

    def receive(self, msg):
        values = (msg.linear.x, msg.linear.y, msg.angular.z)
        if not all(math.isfinite(value) for value in values):
            self.command = ZERO
        else:
            # 本课仿真速度限制：平移合速度 <= 0.3 m/s，旋转 <= 0.8 rad/s。
            vx, vy, wz = values
            scale = min(1.0, 0.3 / max(math.hypot(vx, vy), 1e-9))
            self.command = (vx * scale, vy * scale, max(-0.8, min(0.8, wz)))
        self.last_received = time.monotonic()

    def update(self):
        self.publisher.publish(as_twist(fresh_command(
            self.command, self.last_received, time.monotonic(), 0.5)))


def run_keyboard(node):
    if not sys.stdin.isatty():
        raise RuntimeError('键盘控制需要交互终端，请使用 sim_teleop.launch.py 启动。')
    publisher = node.create_publisher(Twist, '/teleop/cmd_vel', 1)
    settings = termios.tcgetattr(sys.stdin)
    print('\nRoboVigor 仿真键盘控制\n'
          'W/S 前后 | A/D 横移 | Q/E 旋转 | 空格/X 停车 | Ctrl+C 退出\n'
          '请先用鼠标点击本终端。持续按键移动，无按键输入约 0.3 秒后停车。\n'
          '速度：0.2 m/s，旋转：0.5 rad/s；一次控制一个方向。\n', flush=True)
    command = ZERO
    last_key = None
    try:
        tty.setcbreak(sys.stdin.fileno())
        while rclpy.ok():
            ready, _, _ = select.select([sys.stdin], [], [], 0.05)
            if ready:
                key = sys.stdin.read(1)
                if not key or key == '\x03':
                    break
                command = command_for_key(key, 0.2, 0.5)
                last_key = time.monotonic()
            publisher.publish(as_twist(fresh_command(
                command, last_key, time.monotonic(), 0.3)))
            rclpy.spin_once(node, timeout_sec=0.0)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        if rclpy.ok():
            publisher.publish(as_twist(ZERO))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--keyboard', action='store_true')
    options, ros_args = parser.parse_known_args()
    rclpy.init(args=ros_args)
    node = Node('simulation_keyboard') if options.keyboard else VelocityGuard()
    try:
        if options.keyboard:
            run_keyboard(node)
        else:
            rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if not options.keyboard and rclpy.ok():
            node.publisher.publish(as_twist(ZERO))
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
