"""Offline checks of the FPS articulated source model; no ROS dependency."""
import math
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

PACKAGE = Path(__file__).resolve().parents[1]
SIM = PACKAGE.parent / 'sentry_sim'
NS = {'xacro': 'http://www.ros.org/wiki/xacro'}


class FpsModelSourceTest(unittest.TestCase):
    def test_pitch_axis_preserves_nominal_mount_and_supports_world_range(self):
        root = ET.parse(PACKAGE / 'urdf/sensors.xacro').getroot()
        pitch = root.find("joint[@name='gimbal_pitch_joint']")
        self.assertIsNotNone(pitch, 'FPS requires a physical pitch joint')
        self.assertEqual(pitch.get('type'), 'revolute')
        self.assertEqual(pitch.find('parent').get('link'), 'gimbal_yaw_link')
        self.assertEqual(pitch.find('child').get('link'), 'gimbal_pitch_link')
        self.assertEqual(pitch.find('axis').get('xyz'), '0 1 0')
        self.assertEqual(pitch.find('origin').get('xyz'), "${frame_data['gun_link']['xyz']}")
        self.assertEqual(pitch.find('origin').get('rpy'), "${frame_data['gun_link']['rpy']}")
        limit = pitch.find('limit')
        nominal_pitch = .316456434558
        self.assertLessEqual(float(limit.get('lower')) + nominal_pitch, -math.pi / 3)
        self.assertGreaterEqual(float(limit.get('upper')) + nominal_pitch, math.pi / 3)
        inertia = root.find("link[@name='gimbal_pitch_link']/inertial")
        self.assertGreater(float(inertia.find('mass').get('value')), 0)

    def test_muzzle_camera_and_sensor_share_physical_pitch_reference(self):
        root = ET.parse(PACKAGE / 'urdf/sensors.xacro').getroot()
        camera = root.find("joint[@name='fps_camera_fixed']")
        self.assertIsNotNone(camera, 'FPS camera must follow the gun')
        self.assertEqual(camera.find('parent').get('link'), 'muzzle_link')
        self.assertEqual(camera.find('origin').get('xyz'), '0.02 0 0')
        self.assertEqual(camera.find('origin').get('rpy'), '0 0 0')
        optical = root.find("joint[@name='fps_camera_optical_fixed']")
        r, p, y = map(float, optical.find('origin').get('rpy').split())
        self.assertAlmostEqual(r, -math.pi / 2)
        self.assertEqual(p, 0)
        self.assertAlmostEqual(y, -math.pi / 2)
        sim = ET.parse(SIM / 'urdf/gazebo/fps_camera.xacro').getroot()
        attachment = sim.find("gazebo[@reference='gimbal_pitch_link']")
        self.assertIsNotNone(attachment, 'Sensor must survive fixed alias lumping')
        sensor = attachment.find('sensor')
        self.assertEqual(sensor.findtext('pose'), '${fps_camera_x} 0 0 0 0 0')
        self.assertEqual(sensor.findtext('update_rate'), '30')
        self.assertEqual(sensor.findtext('camera/image/width'), '640')
        self.assertEqual(sensor.findtext('camera/image/height'), '480')
        plugin = sensor.find('plugin')
        self.assertEqual(plugin.get('filename'), 'libgazebo_ros_camera.so')
        self.assertEqual(plugin.findtext('camera_name'), 'fps')
        self.assertEqual(plugin.findtext('frame_name'), 'fps_camera_optical_frame')
        self.assertEqual({e.text for e in plugin.findall('ros/remapping')},
                         {'fps/image_raw:=/fps/image_raw', 'fps/camera_info:=/fps/camera_info'})


if __name__ == '__main__':
    unittest.main()
