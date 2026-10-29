"""Exercise actual Qt key press/release events without desktop auto-repeat."""
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PyQt5.QtCore import QEvent, Qt  # noqa: E402
from PyQt5.QtTest import QTest  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import keyboard_window  # noqa: E402


class KeyboardWindowTest(unittest.TestCase):
    """Check the frontend's real event flow and stop behavior."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_hold_release_spin_and_deactivation(self):
        output = {}

        def publisher(_, topic, depth):
            output[topic] = []
            return SimpleNamespace(publish=output[topic].append)

        node = SimpleNamespace(create_publisher=publisher,
                               get_logger=lambda: SimpleNamespace(info=lambda message: None))
        with patch.object(keyboard_window.rclpy, 'ok', return_value=True):
            window = keyboard_window.KeyboardWindow(node, '/teleop/unit_test')
            mode = output['/teleop/unit_test/spin_mode']
            velocity = output['/teleop/unit_test/cmd_vel']
            self.assertFalse(mode[-1].data)
            self.assertEqual(velocity[-1].linear.x, 0.)
            QTest.keyPress(window, Qt.Key_W)
            for _ in range(50):
                window.publish()
                self.assertEqual(velocity[-1].linear.x, .8)
            QTest.keyRelease(window, Qt.Key_W)
            self.assertEqual(velocity[-1].linear.x, 0.)
            QTest.keyClick(window, Qt.Key_X)
            self.assertTrue(mode[-1].data)
            self.assertEqual(velocity[-1].angular.z, 3.)
            QApplication.sendEvent(window, QEvent(QEvent.WindowDeactivate))
            self.assertFalse(mode[-1].data)
            self.assertEqual(velocity[-1].angular.z, 0.)
            window.close()
