"""检查 Gazebo 两台导航雷达的点云接口、采样和 Odin 的 /scan 配置。"""
import math
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

import xacro
import yaml


SRC = Path(__file__).resolve().parents[2]


class LidarConfigTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = SRC / 'sentry_sim/urdf/gazebo/lidar.xacro'
        cls.model = ET.fromstring(xacro.process_file(str(path)).toxml())

    def test_cloud_topics_and_attachment_frames(self):
        expected = {'odin1_lite': '/lidar/points', 'mid360s': '/mid360s/points'}
        sensors = self.model.findall('gazebo/sensor')
        self.assertCountEqual([sensor.get('name') for sensor in sensors], list(expected))
        plugins = []
        for mount in self.model.findall('gazebo'):
            sensor = mount.find('sensor')
            name = sensor.get('name')
            frame = name + '_link'
            self.assertEqual(mount.get('reference'), frame)
            self.assertEqual(sensor.get('type'), 'gpu_ray')
            self.assertEqual(sensor.findtext('plugin/frame_name'), frame)
            self.assertEqual(sensor.findtext('plugin/output_type'), 'sensor_msgs/PointCloud2')
            self.assertEqual(sensor.findtext('plugin/ros/remapping'), '~/out:=' + expected[name])
            plugins.append(sensor.find('plugin').get('name'))
        self.assertEqual(len(set(plugins)), 2)

    def test_odin_scan_geometry_and_consumer(self):
        sensor = self.model.find("gazebo/sensor[@name='odin1_lite']")
        scan = sensor.find('ray/scan')
        for axis, count, half_angle in [('horizontal', 240, 60), ('vertical', 180, 45)]:
            self.assertEqual(int(scan.findtext(f'{axis}/samples')), count)
            self.assertEqual(float(scan.findtext(f'{axis}/resolution')), 1.)
            self.assertAlmostEqual(float(scan.findtext(f'{axis}/min_angle')), math.radians(-half_angle))
            self.assertAlmostEqual(float(scan.findtext(f'{axis}/max_angle')), math.radians(half_angle))
        self.assertEqual(float(sensor.findtext('update_rate')), 10.)
        self.assertEqual(float(sensor.findtext('ray/range/min')), .15)
        self.assertEqual(float(sensor.findtext('ray/range/max')), 25.)
        self.assertEqual(sensor.findtext('ray/noise/type'), 'gaussian')
        self.assertEqual(float(sensor.findtext('ray/noise/stddev')), .03)
        path = SRC / 'sentry_perception/config/sentry_pointcloud_to_scan.yaml'
        config = yaml.safe_load(path.read_text(encoding='utf-8'))['pointcloud_to_laserscan']['ros__parameters']
        self.assertEqual(config['scan_time'], 1. / float(sensor.findtext('update_rate')))
        self.assertEqual(config['range_min'], float(sensor.findtext('ray/range/min')))
        self.assertEqual(config['range_max'], float(sensor.findtext('ray/range/max')))

    def test_mid360s_full_turn_without_duplicate_endpoint(self):
        sensor = self.model.find("gazebo/sensor[@name='mid360s']")
        scan = sensor.find('ray/scan')
        vertical = scan.find('vertical')
        self.assertAlmostEqual(float(vertical.findtext('min_angle')), math.radians(-7))
        self.assertAlmostEqual(float(vertical.findtext('max_angle')), math.radians(52))
        horizontal = scan.find('horizontal')
        h = int(horizontal.findtext('samples'))
        v = int(vertical.findtext('samples'))
        self.assertEqual(float(horizontal.findtext('resolution')), 1.)
        self.assertEqual(float(vertical.findtext('resolution')), 1.)
        self.assertEqual(float(sensor.findtext('update_rate')), 10.)
        self.assertEqual(h * v, 20_000)
        width = float(horizontal.findtext('max_angle')) - float(horizontal.findtext('min_angle'))
        self.assertAlmostEqual(width / (h - 1), math.tau / h)
        self.assertEqual(float(sensor.findtext('ray/range/min')), .1)
        self.assertEqual(float(sensor.findtext('ray/range/max')), 40.)


if __name__ == '__main__':
    unittest.main()
