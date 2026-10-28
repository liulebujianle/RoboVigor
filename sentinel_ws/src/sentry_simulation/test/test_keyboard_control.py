"""验证按键方向及失联停车，不需要启动 Gazebo。"""
import importlib.util
from pathlib import Path
import unittest
from types import SimpleNamespace
from geometry_msgs.msg import Twist


path = Path(__file__).resolve().parents[1] / 'scripts' / 'keyboard_control.py'
spec = importlib.util.spec_from_file_location('keyboard_control', path)
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


class ControlTest(unittest.TestCase):
    def test_directions_and_stop(self):
        expected = {
            'w': (0.2, 0.0, 0.0), 's': (-0.2, 0.0, 0.0),
            'a': (0.0, 0.2, 0.0), 'd': (0.0, -0.2, 0.0),
            'q': (0.0, 0.0, 0.5), 'e': (0.0, 0.0, -0.5),
            ' ': (0.0, 0.0, 0.0), 'x': (0.0, 0.0, 0.0),
        }
        for key, value in expected.items():
            with self.subTest(key=key):
                self.assertEqual(control.command_for_key(key, 0.2, 0.5), value)
        self.assertEqual(control.command_for_key('W', 0.2, 0.5), expected['w'])

    def test_timeout_and_missing_input(self):
        velocity = (0.2, 0.0, 0.0)
        self.assertEqual(control.fresh_command(velocity, 1.0, 1.1, 0.5), velocity)
        self.assertEqual(control.fresh_command(velocity, 1.0, 1.5, 0.5), (0., 0., 0.))
        self.assertEqual(control.fresh_command(velocity, None, 1.0, 0.5), (0., 0., 0.))

    def test_guard_limits_combined_speed_and_rotation(self):
        state = SimpleNamespace(command=None, last_received=None)
        msg = Twist()
        msg.linear.x, msg.linear.y, msg.angular.z = 3.0, 4.0, -2.0
        control.VelocityGuard.receive(state, msg)
        self.assertAlmostEqual(state.command[0], 0.18)
        self.assertAlmostEqual(state.command[1], 0.24)
        self.assertEqual(state.command[2], -0.8)

    def test_guard_rejects_nonfinite_input(self):
        state = SimpleNamespace(command=None, last_received=None)
        msg = Twist()
        msg.linear.x = float('nan')
        control.VelocityGuard.receive(state, msg)
        self.assertEqual(state.command, (0., 0., 0.))


if __name__ == '__main__':
    unittest.main()
