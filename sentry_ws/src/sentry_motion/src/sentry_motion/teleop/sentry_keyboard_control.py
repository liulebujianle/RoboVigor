#!/usr/bin/env python3
"""仿真键盘控制，Qt 窗口和速度看门狗在同一进程中运行。

窗口记录按键状态，节点对速度限幅并处理输入超时。
小陀螺开启时按锁定的云台航向平移，通过 /cmd_vel 和 /spin_mode 控制仿真插件。
"""

import argparse
import math
import signal
import sys
import time

import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry
from PyQt5.QtCore import QEvent, Qt, QTimer
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Bool

ZERO = (0.0, 0.0, 0.0)
KEY_BINDINGS = {
    Qt.Key_W: 'w', Qt.Key_S: 's', Qt.Key_A: 'a', Qt.Key_D: 'd',
    Qt.Key_Q: 'q', Qt.Key_E: 'e', Qt.Key_X: 'x', Qt.Key_C: 'c', Qt.Key_Space: ' ',
}


def fresh_command(command, last_received, now, timeout):
    """用单调时钟检查输入超时，避免受 Gazebo 暂停或时间重置影响。"""
    if last_received is None or now - last_received >= timeout:
        return ZERO
    return command


def as_twist(command):
    """(vx, vy, wz) → geometry_msgs/Twist。"""
    msg = Twist()
    msg.linear.x, msg.linear.y, msg.angular.z = command
    return msg


def world_to_body(vx, vy, yaw):
    """将世界系速度转换到当前车体系。"""
    return (math.cos(yaw) * vx + math.sin(yaw) * vy,
            -math.sin(yaw) * vx + math.cos(yaw) * vy)


class StraightLineReference:
    """小陀螺平移时，修正相对锁定方向的横向偏差。"""

    def __init__(self):
        self.origin, self.direction = None, None
        self.moving = False

    def reset(self):
        """下一次移动以当前位置为新起点。"""
        self.origin, self.direction = None, None
        self.moving = False

    def correct(self, vx, vy, position):
        """保持前向速度，横向修正限幅 0.25 m/s。"""
        speed = math.hypot(vx, vy)
        if speed < 1e-6:
            self.moving = False
            if self.direction is None:
                return vx, vy
        else:
            direction = vx / speed, vy / speed
            if not self.moving or self.direction is None or sum(
                    a * b for a, b in zip(direction, self.direction)) < .999:
                self.origin, self.direction = position, direction
            self.moving = True
        # 松键减速期间保留横向反馈，避免刹车时侧滑。
        nx, ny = -self.direction[1], self.direction[0]
        cross_track = (position[0] - self.origin[0]) * nx + (
            position[1] - self.origin[1]) * ny
        correction = max(-.25, min(.25, -6.0 * cross_track))
        return vx + nx * correction, vy + ny * correction


class HeldKeyboardState:
    """保存移动键状态；小陀螺开启后保持到收到停止输入。"""

    def __init__(self, linear=0.8, angular=1.5, spin_speed=3.0):
        self.linear, self.angular, self.spin_speed = linear, angular, spin_speed
        self.keys, self.spin = set(), False

    def stop(self):
        """清空所有移动键并关掉小陀螺。"""
        self.keys.clear()
        self.spin = False

    def press(self, key):
        """X 只开陀螺；C/空格全停；WASD/QE 记为按住。"""
        if key == 'x':
            self.spin = True
        elif key in ('c', ' '):
            self.stop()
        elif key in ('w', 'a', 's', 'd', 'q', 'e'):
            self.keys.add(key)

    def release(self, key):
        """松开一个移动键，不改陀螺状态。"""
        self.keys.discard(key)

    def output(self):
        """合成按键速度，斜向合速度不超过 linear。"""
        vx = float(('w' in self.keys) - ('s' in self.keys))
        vy = float(('a' in self.keys) - ('d' in self.keys))
        scale = self.linear / max(1.0, math.hypot(vx, vy))
        wz = self.spin_speed if self.spin else self.angular * (
            ('q' in self.keys) - ('e' in self.keys))
        return ((vx * scale, vy * scale, wz), self.spin)


class VelocityGuard(Node):
    """对键盘速度限幅并检查超时，小陀螺平移时转换坐标后发布 /cmd_vel。"""

    def __init__(self):
        super().__init__('simulation_velocity_guard')
        self.command_timeout = float(self.declare_parameter('command_timeout', 0.5).value)
        self.max_linear = float(self.declare_parameter('max_linear', 1.2).value)
        self.max_angular = float(self.declare_parameter('max_angular', 4.0).value)
        if not all(math.isfinite(v) and v > 0 for v in (
                self.command_timeout, self.max_linear, self.max_angular)):
            raise ValueError('Motion guard limits and timeout must be positive and finite')
        self.command = ZERO
        self.last_received = None
        self.spin_requested, self.last_spin_received = False, None
        self.yaw, self.gimbal_yaw = 0.0, 0.0
        self.position = (0., 0.)
        self.line_reference = StraightLineReference()
        self.last_pose, self.last_gimbal_pose, self.spin_heading = None, None, None
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 1)
        self.spin_publisher = self.create_publisher(Bool, '/spin_mode', 1)
        self.odom_subscription = self.create_subscription(
            Odometry, '/odom', self.receive_pose, 10)
        self.gimbal_subscription = self.create_subscription(
            PoseStamped, '/gimbal_pose', self.receive_gimbal_pose, 10)

    def receive(self, msg):
        """校验并限幅一帧速度：平移合速度 ≤ max_linear，旋转 ≤ max_angular。"""
        values = (msg.linear.x, msg.linear.y, msg.angular.z)
        if not all(math.isfinite(value) for value in values):
            self.command = ZERO
        else:
            vx, vy, wz = values
            scale = min(1.0, self.max_linear / max(math.hypot(vx, vy), 1e-9))
            self.command = (
                vx * scale, vy * scale, max(-self.max_angular, min(self.max_angular, wz)))
        self.last_received = time.monotonic()

    def receive_spin(self, msg):
        """记录小陀螺状态心跳，超时后停止旋转。"""
        self.spin_requested = msg.data
        self.last_spin_received = time.monotonic()

    def receive_pose(self, msg):
        """从里程计读取底盘位置和 yaw。"""
        q = msg.pose.pose.orientation
        p = msg.pose.pose.position
        values = (q.x, q.y, q.z, q.w, p.x, p.y)
        if all(math.isfinite(v) for v in values):
            self.position = (p.x, p.y)
            self.yaw = math.atan2(2 * (q.w * q.z + q.x * q.y),
                                  1 - 2 * (q.y * q.y + q.z * q.z))
            self.last_pose = time.monotonic()

    def receive_gimbal_pose(self, msg):
        """从一帧实际位姿锁存世界航向，避免混用不同时刻的角度。"""
        q = msg.pose.orientation
        if msg.header.frame_id == 'world' and all(
                math.isfinite(v) for v in (q.x, q.y, q.z, q.w)):
            self.gimbal_yaw = math.atan2(
                2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
            self.last_gimbal_pose = time.monotonic()

    def update(self):
        """根据输入和位姿计算速度，发布 /spin_mode 和 /cmd_vel。"""
        now = time.monotonic()

        def fresh(stamp):
            return stamp is not None and now - stamp < self.command_timeout
        command = fresh_command(self.command, self.last_received, now, self.command_timeout)
        spin = (self.spin_requested and fresh(self.last_spin_received)
                and fresh(self.last_received))
        if spin and not (fresh(self.last_pose) and fresh(self.last_gimbal_pose)):
            command, spin = ZERO, False
        if spin:
            if self.spin_heading is None:
                self.spin_heading = self.gimbal_yaw
            vx, vy, wz = command
            c, s = math.cos(self.spin_heading), math.sin(self.spin_heading)
            vx, vy = self.line_reference.correct(
                c * vx - s * vy, s * vx + c * vy, self.position)
            scale = min(1.0, self.max_linear / max(math.hypot(vx, vy), 1e-9))
            vx, vy = world_to_body(vx * scale, vy * scale, self.yaw)
            command = (vx, vy, wz)
        else:
            self.spin_heading = None
            self.line_reference.reset()
            # 小陀螺状态超时后清除旧的旋转指令。
            if self.spin_requested:
                command = ZERO
        self.spin_publisher.publish(Bool(data=spin))
        self.publisher.publish(as_twist(command))


class KeyboardWindow(QWidget):
    """按住连续走、松开停；小陀螺 X 开、C/空格或关窗全停。"""

    def __init__(self, node, linear=0.8, angular=1.5, spin_speed=3.0):
        super().__init__()
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.node = node
        self.state = HeldKeyboardState(linear, angular, spin_speed)
        self.setWindowTitle('RoboVigor 键盘控制')
        self.setFocusPolicy(Qt.StrongFocus)
        self.resize(530, 230)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            '点击此窗口后操作\n\n'
            '按住 W/S 前后、A/D 横移，松开停止平移\n'
            'Q/E 普通旋转；X 开启小陀螺，C / 空格全停\n'
            '切换窗口会松开移动键；已开启的小陀螺继续旋转\n'
            f'平移 {linear} m/s；小陀螺 {spin_speed} rad/s'))
        self.status = QLabel()
        layout.addWidget(self.status)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(20)
        self.publish()
        self.node.get_logger().info('Keyboard ready: gyro OFF; click the window to control')

    def publish(self):
        """将当前按键状态交给速度看门狗，并刷新界面。"""
        if not rclpy.ok():
            return
        command, spin = self.state.output()
        self.node.receive(as_twist(command))
        self.node.receive_spin(Bool(data=spin))
        self.node.update()
        self.status.setText('小陀螺：' + ('开启' if spin else '关闭') +
                            f'    平移指令：{command[0]:.2f}, {command[1]:.2f} m/s')

    def tick(self):
        """每 20 ms 处理 ROS 回调并更新速度。"""
        if not rclpy.ok():
            self.close()
            return
        rclpy.spin_once(self.node, timeout_sec=0.0)
        self.publish()

    def keyPressEvent(self, event):
        """保留真实按键状态，忽略桌面自动重复事件。"""
        if not event.isAutoRepeat():
            key = KEY_BINDINGS.get(event.key())
            if key == 'x' and not self.state.spin:
                self.node.get_logger().info('Gyro enabled by X key')
            self.state.press(key)
            self.publish()
        event.accept()

    def keyReleaseEvent(self, event):
        """松键后立即更新速度，忽略自动重复事件。"""
        if not event.isAutoRepeat():
            self.state.release(KEY_BINDINGS.get(event.key()))
            self.publish()
        event.accept()

    def event(self, event):
        # 切去操作 Gazebo 或 RViz 后，松键事件可能不会再回到这个窗口。
        if event.type() == QEvent.WindowDeactivate and self.state.keys:
            self.state.keys.clear()
            self.publish()
        return super().event(event)

    def closeEvent(self, event):
        """关窗前先发一帧全停。"""
        self.state.stop()
        self.publish()
        event.accept()


def main():
    """启动 ROS 节点和 Qt 键盘窗口。"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--linear', type=float, default=0.8)
    parser.add_argument('--angular', type=float, default=1.5)
    parser.add_argument('--spin-speed', type=float, default=3.0)
    args, ros_args = parser.parse_known_args()
    if not all(math.isfinite(v) and v > 0 for v in (
            args.linear, args.angular, args.spin_speed)):
        parser.error('Speeds must be positive and finite')
    rclpy.init(args=ros_args)
    node = VelocityGuard()
    app = QApplication(sys.argv[:1])
    window = KeyboardWindow(node, args.linear, args.angular, args.spin_speed)
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    signal.signal(signal.SIGTERM, lambda *_: app.quit())
    window.show()
    try:
        app.exec_()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        window.state.stop()
        window.publish()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
