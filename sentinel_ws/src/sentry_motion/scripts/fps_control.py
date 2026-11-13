#!/usr/bin/env python3
"""Gun camera FPS viewport and guarded measured-view-relative motion."""
import argparse
import math
import signal
import sys
import time

import rclpy
from geometry_msgs.msg import PoseStamped, Vector3Stamped
from PyQt5.QtCore import QEvent, QPoint, Qt, QTimer
from PyQt5.QtGui import QColor, QCursor, QImage, QPainter, QPen
from PyQt5.QtWidgets import QApplication, QWidget
from rclpy.executors import ExternalShutdownException
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import Bool

from fps_logic import ViewMotion, ViewState, angle, image_layout
from keyboard_control import HeldKeyboardState, VelocityGuard, ZERO, as_twist, fresh_command


def image_to_qimage(msg):
    """Deep-copy ROS pixels before the callback releases its padded byte buffer."""
    image_layout(msg.width, msg.height, msg.encoding, msg.step, len(msg.data))
    pixel_format = QImage.Format_RGBA8888 if msg.encoding == 'rgba8' else QImage.Format_RGB888
    result = QImage(bytes(msg.data), msg.width, msg.height, msg.step, pixel_format).copy()
    if result.isNull():
        raise ValueError('Could not decode FPS image')
    return result.rgbSwapped() if msg.encoding == 'bgr8' else result


class FpsVelocityGuard(VelocityGuard):
    """Legacy watchdog transport with an independent FPS frame-conversion path."""
    def __init__(self):
        super().__init__()
        self.fps_mode = True
        self.view = ViewState(self.command_timeout)
        self.motion = ViewMotion()
        self.image = None
        sensor_qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT,
                                durability=DurabilityPolicy.VOLATILE)
        self.look_publisher = self.create_publisher(Vector3Stamped, '/fps/look', 1)
        self.view_subscription = self.create_subscription(
            PoseStamped, '/fps/view_pose', self.receive_view, sensor_qos)
        self.image_subscription = self.create_subscription(
            Image, '/fps/image_raw', self.receive_image, sensor_qos)

    def receive_view(self, msg):
        q = msg.pose.orientation
        self.view.pose((q.x, q.y, q.z, q.w), msg.header.frame_id, time.monotonic())

    def receive_image(self, msg):
        try:
            decoded = image_to_qimage(msg)
        except (ValueError, TypeError, OverflowError):
            return
        self.image = decoded
        self.view.image((msg.header.stamp.sec, msg.header.stamp.nanosec), time.monotonic())

    def ready(self, now):
        return (self.view.ready(now) and self.last_pose is not None
                and 0 <= now - self.last_pose < self.command_timeout)

    def update(self):
        now = time.monotonic()
        fresh = lambda stamp: stamp is not None and 0 <= now - stamp < self.command_timeout
        command = fresh_command(self.command, self.last_received, now, self.command_timeout)
        valid = self.ready(now) and fresh(self.last_received) and fresh(self.last_spin_received)
        spin = valid and self.spin_requested
        if not valid:
            command = ZERO
            self.motion.reset()
        else:
            vx, vy, wz = command
            steering = abs(angle(self.view.target_yaw - self.view.yaw)) > .005
            vx, vy = self.motion.command(vx, vy, self.view.yaw, self.yaw,
                                          self.position, steering)
            scale = min(1., self.max_linear / max(math.hypot(vx, vy), 1e-9))
            command = vx * scale, vy * scale, wz
        self.spin_publisher.publish(Bool(data=spin))
        self.publisher.publish(as_twist(command))

    def publish_look(self):
        if not self.ready(time.monotonic()):
            return
        msg = Vector3Stamped()
        msg.header.frame_id = 'world'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.vector.x, msg.vector.y = self.view.target_yaw, self.view.target_pitch
        self.look_publisher.publish(msg)


class FpsWindow(QWidget):
    def __init__(self, node, linear=.8, angular=1.5, spin_speed=3., sensitivity=.002):
        super().__init__()
        self.node = node
        self.state = HeldKeyboardState(linear, angular, spin_speed)
        self.sensitivity, self.captured = sensitivity, False
        self.setWindowTitle('RoboVigor FPS — 点击捕获鼠标 / Esc 释放')
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.resize(800, 640)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(20)

    def center(self):
        return QPoint(self.width() // 2, self.height() // 2)

    def release_control(self):
        self.state.stop()
        if self.captured:
            self.captured = False
            self.releaseMouse()
            self.unsetCursor()
        self.node.motion.reset()
        self.publish()

    def publish(self):
        if not rclpy.ok():
            return
        command, spin = self.state.output() if self.captured else (ZERO, False)
        self.node.receive(as_twist(command))
        self.node.receive_spin(Bool(data=spin))
        self.node.update()
        if self.captured:
            self.node.publish_look()

    def tick(self):
        if not rclpy.ok():
            self.close()
            return
        # Depth-one camera QoS and a bounded callback drain keep the displayed
        # frame current alongside high-rate pose/odometry streams.
        for _ in range(8):
            rclpy.spin_once(self.node, timeout_sec=0.)
        if self.captured and not self.node.ready(time.monotonic()):
            self.release_control()
        self.publish()
        self.update()

    def mousePressEvent(self, event):
        if (event.button() == Qt.LeftButton and not self.captured
                and self.node.ready(time.monotonic())):
            self.node.view.sync_target()
            self.captured = True
            self.setFocus(Qt.MouseFocusReason)
            self.setCursor(Qt.BlankCursor)
            self.grabMouse()
            QCursor.setPos(self.mapToGlobal(self.center()))
            self.publish()
        event.accept()

    def mouseMoveEvent(self, event):
        if self.captured:
            delta = event.pos() - self.center()
            if not delta.isNull():
                self.node.view.mouse(delta.x(), delta.y(), self.sensitivity)
                QCursor.setPos(self.mapToGlobal(self.center()))
                self.node.publish_look()
        event.accept()

    def keyPressEvent(self, event):
        if not event.isAutoRepeat():
            if event.key() == Qt.Key_Escape:
                self.release_control()
            elif self.captured:
                key = event.text().lower()
                if key in ('w', 'a', 's', 'd', 'x', 'c', ' '):
                    self.state.press(key)
                    self.publish()
        event.accept()

    def keyReleaseEvent(self, event):
        if not event.isAutoRepeat():
            self.state.release(event.text().lower())
            self.publish()
        event.accept()

    def focusOutEvent(self, event):
        self.release_control()
        super().focusOutEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.WindowDeactivate:
            self.release_control()
        super().changeEvent(event)

    def closeEvent(self, event):
        self.timer.stop()
        self.release_control()
        event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#11151a'))
        image = self.node.image
        if image is not None:
            size = image.size().scaled(self.size(), Qt.KeepAspectRatio)
            x, y = (self.width() - size.width()) // 2, (self.height() - size.height()) // 2
            painter.drawImage(x, y, image.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            # Symmetric letterboxing keeps the reticle at the optical center.
            cx, cy = self.width() // 2, self.height() // 2
            for color, width in ((QColor('black'), 3), (QColor('#a8ff80'), 1)):
                painter.setPen(QPen(color, width))
                for a, b, c, d in ((cx-12, cy, cx-4, cy), (cx+4, cy, cx+12, cy),
                                   (cx, cy-12, cx, cy-4), (cx, cy+4, cx, cy+12)):
                    painter.drawLine(a, b, c, d)
        painter.setPen(QColor('white'))
        ready = self.node.ready(time.monotonic())
        status = ('鼠标已捕获 · WASD 移动 · X 小陀螺 · C/空格停车 · Esc 释放'
                  if self.captured else '点击画面捕获鼠标 · WASD 移动 · X 小陀螺 · Esc 释放')
        if not ready:
            status = '等待新鲜相机画面、世界视角与底盘位姿 — 已停车'
        painter.fillRect(0, 0, self.width(), 30, QColor(0, 0, 0, 190))
        painter.drawText(10, 21, status)
        painter.end()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--linear', type=float, default=.8)
    parser.add_argument('--angular', type=float, default=1.5)
    parser.add_argument('--spin-speed', type=float, default=3.)
    parser.add_argument('--mouse-sensitivity', type=float, default=.002)
    args, ros_args = parser.parse_known_args()
    if not all(math.isfinite(v) and v > 0 for v in
               (args.linear, args.angular, args.spin_speed, args.mouse_sensitivity)):
        parser.error('Speeds and sensitivity must be positive and finite')
    rclpy.init(args=ros_args)
    node = FpsVelocityGuard()
    app = QApplication(sys.argv[:1])
    window = FpsWindow(node, args.linear, args.angular, args.spin_speed, args.mouse_sensitivity)
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    signal.signal(signal.SIGTERM, lambda *_: app.quit())
    window.show()
    try:
        app.exec_()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        window.release_control()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
