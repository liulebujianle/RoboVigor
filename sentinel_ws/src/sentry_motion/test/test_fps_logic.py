"""Pure FPS contracts, runnable without ROS or Qt."""
import importlib.util
import math
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'scripts' / 'fps_logic.py'
spec = importlib.util.spec_from_file_location('fps_logic', path)
logic = importlib.util.module_from_spec(spec) if path.exists() else None
if logic is not None:
    spec.loader.exec_module(logic)


class FpsLogicTest(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(logic, 'FPS pure control module is missing')

    def test_measured_view_direction_independent_of_spinning_body(self):
        vx, vy = logic.ViewMotion().command(.8, 0., math.pi / 2, math.pi, (0., 0.), False)
        self.assertAlmostEqual(vx, 0.)
        self.assertAlmostEqual(vy, -.8)

    def test_held_forward_follows_turn_without_old_line_correction(self):
        motion = logic.ViewMotion()
        self.assertEqual(motion.command(.8, 0., 0., 0., (0., 0.), False), (.8, 0.))
        self.assertAlmostEqual(motion.command(.8, 0., 0., 0., (1., .04), False)[1], -.24)
        vx, vy = motion.command(.8, 0., math.pi / 2, 0., (1., .04), True)
        self.assertAlmostEqual(vx, 0.)
        self.assertAlmostEqual(vy, .8)
        vx, vy = motion.command(.8, 0., math.pi, 0., (1., .04), False)
        self.assertAlmostEqual(vx, -.8)
        self.assertAlmostEqual(vy, 0.)

    def test_straight_correction_bounded_and_release_stops_translation(self):
        motion = logic.ViewMotion()
        motion.command(.8, 0., 0., 0., (0., 0.), False)
        self.assertEqual(motion.command(.8, 0., 0., 0., (1., 1.), False), (.8, -.25))
        self.assertEqual(motion.command(0., 0., 0., 0., (1., 1.), False), (0., 0.))

    def test_mouse_signs_pitch_limit_and_initial_actual_pose(self):
        view = logic.ViewState()
        self.assertTrue(view.pose((0., 0., math.sqrt(.5), math.sqrt(.5)), 'world', 10.))
        self.assertAlmostEqual(view.target_yaw, math.pi / 2)
        view.mouse(100., -100., .002)
        self.assertAlmostEqual(view.target_yaw, math.pi / 2 - .2)
        self.assertAlmostEqual(view.target_pitch, -.2)
        view.mouse(0., 100000., .002)
        self.assertAlmostEqual(view.target_pitch, math.pi / 3)
        view.mouse(0., -100000., .002)
        self.assertAlmostEqual(view.target_pitch, -math.pi / 3)

    def test_requires_fresh_valid_world_pose_and_new_image(self):
        view = logic.ViewState()
        self.assertFalse(view.ready(1.))
        self.assertFalse(view.pose((0., 0., 0., 0.), 'world', 1.))
        self.assertFalse(view.pose((0., 0., 0., 1.), 'map', 1.))
        self.assertFalse(view.pose((0., 0., float('nan'), 1.), 'world', 1.))
        view.pose((0., 0., 0., 1.), 'world', 1.)
        view.image((5, 0), 1.)
        self.assertTrue(view.ready(1.49))
        self.assertFalse(view.ready(1.5))
        view.pose((0., 0., 0., 1.), 'world', 1.6)
        view.image((5, 0), 1.6)
        self.assertFalse(view.ready(1.6))
        view.image((5, 1), 1.6)
        self.assertTrue(view.ready(1.6))

    def test_padded_image_layout_and_bad_payload(self):
        self.assertEqual(logic.image_layout(2, 2, 'bgr8', 8, 16), (3, 8))
        self.assertEqual(logic.image_layout(2, 1, 'rgba8', 8, 8), (4, 8))
        for args in [(2, 2, 'mono8', 2, 4), (2, 2, 'rgb8', 5, 12),
                     (2, 2, 'rgb8', 6, 11), (0, 2, 'rgb8', 6, 12)]:
            with self.assertRaises(ValueError):
                logic.image_layout(*args)


if __name__ == '__main__':
    unittest.main()
