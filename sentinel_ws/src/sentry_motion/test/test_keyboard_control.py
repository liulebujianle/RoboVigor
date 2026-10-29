"""验证按键方向、限速、失联停车与窗口事件，不需要启动 Gazebo."""
import importlib.util
import math
import os
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from geometry_msgs.msg import Twist

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PyQt5.QtCore import QEvent, Qt  # noqa: E402
from PyQt5.QtTest import QTest  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402


path = Path(__file__).resolve().parents[1] / 'scripts' / 'keyboard_control.py'
spec = importlib.util.spec_from_file_location('keyboard_control', path)
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


class ControlTest(unittest.TestCase):
    def test_timeout_and_missing_input(self):
        velocity = (0.2, 0.0, 0.0)
        self.assertEqual(control.fresh_command(velocity, 1.0, 1.1, 0.5), velocity)
        self.assertEqual(control.fresh_command(velocity, 1.0, 1.5, 0.5), (0., 0., 0.))
        self.assertEqual(control.fresh_command(velocity, None, 1.0, 0.5), (0., 0., 0.))

    def test_guard_limits_combined_speed_and_rotation(self):
        state = SimpleNamespace(command=None, last_received=None, max_linear=1.2, max_angular=4.0)
        msg = Twist()
        msg.linear.x, msg.linear.y, msg.angular.z = 3.0, 4.0, -2.0
        control.VelocityGuard.receive(state, msg)
        self.assertAlmostEqual(state.command[0], 0.72)
        self.assertAlmostEqual(state.command[1], 0.96)
        self.assertEqual(state.command[2], -2.0)

    def test_guard_rejects_nonfinite_input(self):
        state = SimpleNamespace(command=None, last_received=None, max_linear=1.2, max_angular=4.0)
        msg = Twist()
        msg.linear.x = float('nan')
        control.VelocityGuard.receive(state, msg)
        self.assertEqual(state.command, (0., 0., 0.))

    def test_spin_translation_keeps_gimbal_forward_direction(self):
        vx, vy = control.world_to_body(0.8, 0., math.pi / 2)
        self.assertAlmostEqual(vx, 0.)
        self.assertAlmostEqual(vy, -0.8)

    def test_spin_heading_uses_actual_world_pose_not_unsynchronized_joint_samples(self):
        output, mode = [], []
        state = SimpleNamespace(
            command=(0.8, 0., 3.), last_received=0.99, command_timeout=0.5,
            spin_requested=True, last_spin_received=0.99,
            yaw=1.2, gimbal_angle=-0.7, last_pose=0.99, last_joint=0.99,
            gimbal_yaw=0., last_gimbal_pose=0.99, spin_heading=None,
            position=(0., 0.), line_reference=control.StraightLineReference(), max_linear=1.2,
            publisher=SimpleNamespace(publish=output.append),
            spin_publisher=SimpleNamespace(publish=mode.append),
        )
        with patch.object(control.time, 'monotonic', return_value=1.0):
            control.VelocityGuard.update(state)
        command = output[-1]
        world_x = math.cos(1.2) * command.linear.x - math.sin(1.2) * command.linear.y
        world_y = math.sin(1.2) * command.linear.x + math.cos(1.2) * command.linear.y
        self.assertAlmostEqual(world_x, 0.8)
        self.assertAlmostEqual(world_y, 0.)


class HeldControlTest(unittest.TestCase):
    def test_start_still_and_hold_does_not_expire(self):
        state = control.HeldKeyboardState()
        self.assertEqual(state.output(), ((0., 0., 0.), False))
        state.press('w')
        for _ in range(100):
            self.assertEqual(state.output(), ((0.8, 0., 0.), False))
        state.release('w')
        self.assertEqual(state.output(), ((0., 0., 0.), False))

    def test_spin_is_explicit_and_translation_releases_independently(self):
        state = control.HeldKeyboardState()
        state.press('x')
        state.release('x')
        state.press('w')
        self.assertEqual(state.output(), ((0.8, 0., 3.), True))
        state.release('w')
        self.assertEqual(state.output(), ((0., 0., 3.), True))
        state.press('x')
        self.assertEqual(state.output(), ((0., 0., 3.), True))
        state.press('c')
        self.assertEqual(state.output(), ((0., 0., 0.), False))

    def test_diagonal_limit_and_explicit_stop(self):
        state = control.HeldKeyboardState()
        state.press('w')
        state.press('a')
        velocity, _ = state.output()
        self.assertAlmostEqual(math.hypot(*velocity[:2]), 0.8)
        state.press('x')
        state.stop()
        self.assertEqual(state.output(), ((0., 0., 0.), False))


class StraightLineTest(unittest.TestCase):
    def test_correct_cross_track_without_changing_forward_request(self):
        line = control.StraightLineReference()
        self.assertEqual(line.correct(.8, 0., (1., 2.)), (.8, 0.))
        vx, vy = line.correct(.8, 0., (2., 2.04))
        self.assertAlmostEqual(vx, .8)
        self.assertAlmostEqual(vy, -.24)
        self.assertAlmostEqual(line.correct(0., 0., (2., 2.04))[1], -.24)
        self.assertEqual(line.correct(.8, 0., (2., 2.04)), (.8, 0.))

    def test_new_direction_starts_a_new_line_and_correction_is_bounded(self):
        line = control.StraightLineReference()
        line.correct(.8, 0., (0., 0.))
        self.assertEqual(line.correct(.8, 0., (0., 10.)), (.8, -.25))
        self.assertEqual(line.correct(0., .8, (0., 10.)), (0., .8))


class FakeGuard:
    """Stand-in for VelocityGuard: records what the window pushes into it."""

    def __init__(self):
        self.commands, self.spins, self.updates = [], [], 0

    def receive(self, msg):
        self.commands.append(msg)

    def receive_spin(self, msg):
        self.spins.append(msg.data)

    def update(self):
        self.updates += 1

    def get_logger(self):
        return SimpleNamespace(info=lambda *args: None)


class KeyboardWindowTest(unittest.TestCase):
    """窗口把按键直接喂给同进程看门狗，不再经过 /teleop 中转话题。"""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.guard = FakeGuard()
        with patch.object(control.rclpy, 'ok', return_value=True):
            self.window = control.KeyboardWindow(self.guard)

    def test_hold_release_spin_and_click_elsewhere_keeps_moving(self):
        with patch.object(control.rclpy, 'ok', return_value=True):
            self.assertEqual(self.guard.commands[-1].linear.x, 0.)
            QTest.keyPress(self.window, Qt.Key_W)
            for _ in range(50):
                self.window.publish()
                self.assertEqual(self.guard.commands[-1].linear.x, .8)
            QTest.keyRelease(self.window, Qt.Key_W)
            self.assertEqual(self.guard.commands[-1].linear.x, 0.)
            QTest.keyClick(self.window, Qt.Key_X)
            self.assertTrue(self.guard.spins[-1])
            self.assertEqual(self.guard.commands[-1].angular.z, 3.)
            # Clicking outside the window must no longer stop the robot.
            QApplication.sendEvent(self.window, QEvent(QEvent.WindowDeactivate))
            self.assertTrue(self.guard.spins[-1])
            self.assertEqual(self.guard.commands[-1].angular.z, 3.)
            self.window.close()

    def test_close_sends_a_final_zero_command(self):
        with patch.object(control.rclpy, 'ok', return_value=True):
            QTest.keyPress(self.window, Qt.Key_W)
            self.assertEqual(self.guard.commands[-1].linear.x, .8)
            self.window.close()
            self.assertEqual(self.guard.commands[-1].linear.x, 0.)
            self.assertFalse(self.guard.spins[-1])
            self.assertGreater(self.guard.updates, 0)


if __name__ == '__main__':
    unittest.main()
