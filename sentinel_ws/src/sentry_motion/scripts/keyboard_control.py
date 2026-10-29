#!/usr/bin/env python3
"""仿真专用：键盘输入与独立速度看门狗；不连接真实底盘."""

import argparse
import math
import select
import sys
import termios
import time
import tty

import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from std_msgs.msg import Bool


ZERO = (0.0, 0.0, 0.0)


def command_for_key(key, linear, angular):
    """速度按车体坐标解释：x 前、y 左、z 轴逆时针旋转."""
    return {
        'w': (linear, 0.0, 0.0), 's': (-linear, 0.0, 0.0),
        'a': (0.0, linear, 0.0), 'd': (0.0, -linear, 0.0),
        'q': (0.0, 0.0, angular), 'e': (0.0, 0.0, -angular),
    }.get(key.lower(), ZERO)


def fresh_command(command, last_received, now, timeout):
    """使用单调时钟检查失联，不受 Gazebo 暂停或重置时间影响."""
    if last_received is None or now - last_received >= timeout:
        return ZERO
    return command


def as_twist(command):
    msg = Twist()
    msg.linear.x, msg.linear.y, msg.angular.z = command
    return msg


def world_to_body(vx, vy, yaw):
    """Rotate a world velocity into the current chassis frame."""
    return (math.cos(yaw) * vx + math.sin(yaw) * vy,
            -math.sin(yaw) * vx + math.cos(yaw) * vy)


class KeyboardState:
    """Keep spin latched while allowing translation keys to time out."""

    def __init__(self, linear=0.8, angular=1.5, spin_speed=3.0):
        self.linear, self.angular, self.spin_speed = linear, angular, spin_speed
        self.command, self.last_key, self.spin = ZERO, None, False

    def press(self, key, now):
        """X enables spin idempotently; C and space stop it without key-up events."""
        key = key.lower()
        if key == 'x':
            self.spin = True
        elif key in ('c', ' '):
            self.spin = False
            self.command, self.last_key = ZERO, None
        else:
            self.command = command_for_key(key, self.linear, self.angular)
            self.last_key = now

    def output(self, now):
        """Return a live heartbeat, retaining only spin after movement expires."""
        vx, vy, wz = fresh_command(self.command, self.last_key, now, 0.3)
        return ((vx, vy, self.spin_speed if self.spin else wz), self.spin)


class StraightLineReference:
    """Correct measured lateral drift along each requested world-frame line."""

    def __init__(self):
        self.origin, self.direction = None, None
        self.moving = False

    def reset(self):
        """Start the next movement from the actual current position."""
        self.origin, self.direction = None, None
        self.moving = False

    def correct(self, vx, vy, position):
        """Keep forward speed and bound the transverse correction to 0.25 m/s."""
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
        # Keep lateral feedback while braking with gyro still on. Dropping it
        # immediately at key release permits a sideways coast during deceleration.
        nx, ny = -self.direction[1], self.direction[0]
        cross_track = (position[0] - self.origin[0]) * nx + (
            position[1] - self.origin[1]) * ny
        correction = max(-.25, min(.25, -6.0 * cross_track))
        return vx + nx * correction, vy + ny * correction


class VelocityGuard(Node):
    """独立进程：输入失联 0.5 秒后，持续向插件发布零速度."""

    def __init__(self):
        super().__init__('simulation_velocity_guard')
        self.command_timeout = float(self.declare_parameter('command_timeout', 0.5).value)
        self.max_linear = float(self.declare_parameter('max_linear', 1.2).value)
        self.max_angular = float(self.declare_parameter('max_angular', 4.0).value)
        self.input_prefix = str(self.declare_parameter('input_prefix', '/teleop/manual').value)
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
        self.subscription = self.create_subscription(
            Twist, self.input_prefix + '/cmd_vel', self.receive, 1)
        self.spin_subscription = self.create_subscription(
            Bool, self.input_prefix + '/spin_mode', self.receive_spin, 1)
        self.odom_subscription = self.create_subscription(
            Odometry, '/odom', self.receive_pose, 10)
        self.gimbal_subscription = self.create_subscription(
            PoseStamped, '/gimbal_pose', self.receive_gimbal_pose, 10)
        # Recompute the body-frame direction at 100 Hz during 3 rad/s gyro.
        self.timer = self.create_timer(0.01, self.update)

    def receive(self, msg):
        values = (msg.linear.x, msg.linear.y, msg.angular.z)
        if not all(math.isfinite(value) for value in values):
            self.command = ZERO
        else:
            # 仿真上限：平移合速度 <= 1.2 m/s，旋转 <= 4 rad/s。
            vx, vy, wz = values
            scale = min(1.0, self.max_linear / max(math.hypot(vx, vy), 1e-9))
            self.command = (
                vx * scale, vy * scale, max(-self.max_angular, min(self.max_angular, wz)))
        self.last_received = time.monotonic()

    def receive_spin(self, msg):
        """Require the keyboard's spin state to keep arriving."""
        self.spin_requested = msg.data
        self.last_spin_received = time.monotonic()

    def receive_pose(self, msg):
        """Read actual chassis yaw, rather than integrating requested speed."""
        q = msg.pose.pose.orientation
        p = msg.pose.pose.position
        values = (q.x, q.y, q.z, q.w, p.x, p.y)
        if all(math.isfinite(v) for v in values):
            self.position = (p.x, p.y)
            self.yaw = math.atan2(2 * (q.w * q.z + q.x * q.y),
                                  1 - 2 * (q.y * q.y + q.z * q.z))
            self.last_pose = time.monotonic()

    def receive_gimbal_pose(self, msg):
        """Latch world heading from one actual pose, avoiding mixed-time angles."""
        q = msg.pose.orientation
        if msg.header.frame_id == 'world' and all(
                math.isfinite(v) for v in (q.x, q.y, q.z, q.w)):
            self.gimbal_yaw = math.atan2(
                2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
            self.last_gimbal_pose = time.monotonic()

    def update(self):
        now = time.monotonic()

        def fresh(stamp):
            return stamp is not None and now - stamp < self.command_timeout
        command = fresh_command(self.command, self.last_received, now, self.command_timeout)
        spin = self.spin_requested and fresh(self.last_spin_received) and fresh(self.last_received)
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
            # A stale spin-state stream must not leave a stale spin rate active.
            if self.spin_requested:
                command = ZERO
        self.spin_publisher.publish(Bool(data=spin))
        self.publisher.publish(as_twist(command))


class HeldKeyboardState:
    """Keep movement live until release, independently of desktop key repeat."""

    def __init__(self, linear=0.8, angular=1.5, spin_speed=3.0):
        self.linear, self.angular, self.spin_speed = linear, angular, spin_speed
        self.keys, self.spin = set(), False

    def stop(self):
        """Clear every movement key and disable gyro."""
        self.keys.clear()
        self.spin = False

    def press(self, key):
        """Enable gyro only on X; keep movement keys until explicit release."""
        if key == 'x':
            self.spin = True
        elif key in ('c', ' '):
            self.stop()
        elif key in ('w', 'a', 's', 'd', 'q', 'e'):
            self.keys.add(key)

    def release(self, key):
        """Release one movement key without altering the gyro latch."""
        self.keys.discard(key)

    def output(self):
        """Combine held keys with a bounded diagonal speed."""
        vx = float(('w' in self.keys) - ('s' in self.keys))
        vy = float(('a' in self.keys) - ('d' in self.keys))
        scale = self.linear / max(1.0, math.hypot(vx, vy))
        wz = self.spin_speed if self.spin else self.angular * (
            ('q' in self.keys) - ('e' in self.keys))
        return ((vx * scale, vy * scale, wz), self.spin)


def run_keyboard(node, linear=0.8, angular=1.5, spin_speed=3.0, input_prefix='/teleop/manual'):
    if not sys.stdin.isatty():
        raise RuntimeError('键盘控制需要交互终端，请使用 sentry_bringup sim_teleop.launch.py 启动。')
    publisher = node.create_publisher(Twist, input_prefix + '/cmd_vel', 1)
    spin_publisher = node.create_publisher(Bool, input_prefix + '/spin_mode', 1)
    settings = termios.tcgetattr(sys.stdin)
    print('\nRoboVigor 仿真键盘控制\n'
          'W/S 前后 | A/D 横移 | Q/E 旋转 | X 开小陀螺 | C 关闭 | 空格全停\n'
          '请先用鼠标点击本终端。持续按键移动，无按键输入约 0.3 秒后停车。\n'
          f'速度：{linear} m/s，旋转：{angular} rad/s，小陀螺：{spin_speed} rad/s。\n'
          '小陀螺开启后会持续旋转；WASD 按云台保持的朝向移动。\n', flush=True)
    state = KeyboardState(linear, angular, spin_speed)
    try:
        tty.setcbreak(sys.stdin.fileno())
        while rclpy.ok():
            ready, _, _ = select.select([sys.stdin], [], [], 0.05)
            if ready:
                key = sys.stdin.read(1)
                if not key or key == '\x03':
                    break
                state.press(key, time.monotonic())
            command, spin = state.output(time.monotonic())
            spin_publisher.publish(Bool(data=spin))
            publisher.publish(as_twist(command))
            rclpy.spin_once(node, timeout_sec=0.0)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        if rclpy.ok():
            spin_publisher.publish(Bool(data=False))
            publisher.publish(as_twist(ZERO))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--keyboard', action='store_true')
    parser.add_argument('--linear', type=float, default=0.8)
    parser.add_argument('--angular', type=float, default=1.5)
    parser.add_argument('--spin-speed', type=float, default=3.0)
    parser.add_argument('--input-prefix', default='/teleop/manual')
    options, ros_args = parser.parse_known_args()
    if not all(math.isfinite(v) and v > 0 for v in
               (options.linear, options.angular, options.spin_speed)):
        parser.error('Speeds must be positive finite numbers')
    rclpy.init(args=ros_args)
    node = Node('simulation_keyboard') if options.keyboard else VelocityGuard()
    try:
        if options.keyboard:
            run_keyboard(node, options.linear, options.angular, options.spin_speed,
                         options.input_prefix)
        else:
            rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except RuntimeError:
        # SIGINT can invalidate the context between a timer's two publishes.
        # Preserve genuine runtime failures while the context remains live.
        if rclpy.ok():
            raise
    finally:
        if not options.keyboard and rclpy.ok():
            try:
                node.spin_publisher.publish(Bool(data=False))
                node.publisher.publish(as_twist(ZERO))
            except RuntimeError:
                if rclpy.ok():
                    raise
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
