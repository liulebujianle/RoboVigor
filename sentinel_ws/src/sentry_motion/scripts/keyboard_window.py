#!/usr/bin/env python3
"""Read real press/release events and publish one launch's manual commands."""
import argparse
import math
import signal
import sys

from PyQt5.QtCore import QEvent, Qt, QTimer
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
import rclpy
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool

from keyboard_control import HeldKeyboardState, as_twist


class KeyboardWindow(QWidget):
    """Keep held-key motion continuous and stop on release or lost focus."""

    def __init__(self, node, input_prefix, linear=0.8, angular=1.5, spin_speed=3.0):
        super().__init__()
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.node = node
        self.state = HeldKeyboardState(linear, angular, spin_speed)
        self.velocity = node.create_publisher(Twist, input_prefix + '/cmd_vel', 1)
        self.mode = node.create_publisher(Bool, input_prefix + '/spin_mode', 1)
        self.setWindowTitle('RoboVigor 键盘控制')
        self.setFocusPolicy(Qt.StrongFocus)
        self.resize(530, 230)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            '点击此窗口后操作\n\n'
            '按住 W/S 前后、A/D 横移，松开停止平移\n'
            'Q/E 普通旋转；X 开启小陀螺，C / 空格全停\n'
            '小陀螺时按云台朝向直线移动；切换窗口会停车\n'
            f'平移 {linear} m/s；小陀螺 {spin_speed} rad/s'))
        self.status = QLabel()
        layout.addWidget(self.status)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(20)
        self.publish()
        self.node.get_logger().info('Keyboard ready: gyro OFF; click this window before control')

    def publish(self):
        """Publish a heartbeat even while stopped, with gyro disabled initially."""
        command, spin = self.state.output()
        if rclpy.ok():
            self.mode.publish(Bool(data=spin))
            self.velocity.publish(as_twist(command))
        self.status.setText('小陀螺：' + ('开启' if spin else '关闭') +
                            f'    平移指令：{command[0]:.2f}, {command[1]:.2f} m/s')

    def tick(self):
        """Service ROS without blocking the keyboard event loop."""
        if rclpy.ok():
            rclpy.spin_once(self.node, timeout_sec=0.0)
            self.publish()
        else:
            self.close()

    def keyPressEvent(self, event):
        """Keep real key state; ignore synthetic desktop auto-repeat events."""
        if not event.isAutoRepeat():
            key = event.text().lower()
            if key == 'x' and not self.state.spin:
                self.node.get_logger().info('Gyro enabled by X key')
            self.state.press(key)
            self.publish()
        event.accept()

    def keyReleaseEvent(self, event):
        """Release a key immediately without waiting for a repeat timeout."""
        if not event.isAutoRepeat():
            self.state.release(event.text().lower())
            self.publish()
        event.accept()

    def event(self, event):
        """Cancel latched gyro and held movement when focus leaves this window."""
        if event.type() == QEvent.WindowDeactivate and hasattr(self, 'state'):
            self.state.stop()
            self.publish()
        return super().event(event)

    def closeEvent(self, event):
        """Send a stop before closing the launch-managed frontend."""
        self.state.stop()
        self.publish()
        event.accept()


def main():
    """Run a Qt keyboard frontend directly managed by ROS launch."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--linear', type=float, default=0.8)
    parser.add_argument('--angular', type=float, default=1.5)
    parser.add_argument('--spin-speed', type=float, default=3.0)
    parser.add_argument('--input-prefix', default='/teleop/manual')
    args, ros_args = parser.parse_known_args()
    if not all(math.isfinite(v) and v > 0 for v in (
            args.linear, args.angular, args.spin_speed)):
        parser.error('Speeds must be positive and finite')
    rclpy.init(args=ros_args)
    app = QApplication(sys.argv[:1])
    node = rclpy.create_node('simulation_keyboard')
    window = KeyboardWindow(node, args.input_prefix, args.linear, args.angular, args.spin_speed)
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    signal.signal(signal.SIGTERM, lambda *_: app.quit())
    window.show()
    try:
        app.exec_()
    finally:
        window.state.stop()
        window.publish()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
