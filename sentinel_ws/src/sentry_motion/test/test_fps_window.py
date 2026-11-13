"""Runtime FPS boundary tests; run on the ROS/PyQt5 simulation host."""
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
scripts = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(scripts))
available = all(importlib.util.find_spec(name) is not None
                for name in ('rclpy', 'geometry_msgs', 'sensor_msgs', 'PyQt5'))
if available:
    from PyQt5.QtCore import QEvent, Qt
    from PyQt5.QtTest import QTest
    from PyQt5.QtWidgets import QApplication
    from sensor_msgs.msg import Image
    import fps_control as control


@unittest.skipUnless(available, 'Requires ROS 2 message packages, rclpy and PyQt5')
class FpsWindowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_bgr_padded_rows_and_owned_copy(self):
        msg = Image(width=1, height=2, encoding='bgr8', step=4)
        msg.data = [0, 0, 255, 99, 255, 0, 0, 99]
        image = control.image_to_qimage(msg)
        msg.data[2] = 0
        self.assertEqual(image.pixelColor(0, 0).getRgb(), (255, 0, 0, 255))
        self.assertEqual(image.pixelColor(0, 1).getRgb(), (0, 0, 255, 255))

    def test_rgb_and_rgba_channels(self):
        for encoding, payload, expected in (
                ('rgb8', [10, 20, 30], (10, 20, 30, 255)),
                ('rgba8', [10, 20, 30, 40], (10, 20, 30, 40))):
            msg = Image(width=1, height=1, encoding=encoding, step=len(payload))
            msg.data = payload
            self.assertEqual(control.image_to_qimage(msg).pixelColor(0, 0).getRgb(), expected)

    def test_capture_escape_and_focus_loss_clear_translation_and_spin(self):
        outputs, spins = [], []
        view = control.ViewState()
        view.pose((0., 0., 0., 1.), 'world', 1.)
        node = SimpleNamespace(
            view=view, motion=control.ViewMotion(), image=None,
            ready=lambda now: True, receive=lambda msg: outputs.append(msg),
            receive_spin=lambda msg: spins.append(msg.data), update=lambda: None,
            publish_look=lambda: None)
        with patch.object(control.rclpy, 'ok', return_value=True):
            window = control.FpsWindow(node)
            QTest.mouseClick(window, Qt.LeftButton)
            self.assertTrue(window.captured)
            QTest.keyPress(window, Qt.Key_W)
            QTest.keyPress(window, Qt.Key_X)
            self.assertEqual(outputs[-1].linear.x, .8)
            self.assertTrue(spins[-1])
            QTest.keyClick(window, Qt.Key_Escape)
            self.assertFalse(window.captured)
            self.assertEqual(outputs[-1].linear.x, 0.)
            self.assertFalse(spins[-1])
            QTest.mouseClick(window, Qt.LeftButton)
            QTest.keyPress(window, Qt.Key_W)
            QTest.keyPress(window, Qt.Key_X)
            QApplication.sendEvent(window, QEvent(QEvent.WindowDeactivate))
            self.assertFalse(window.captured)
            self.assertEqual(outputs[-1].linear.x, 0.)
            self.assertFalse(spins[-1])
            window.close()


if __name__ == '__main__':
    unittest.main()
