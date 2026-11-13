"""Check sensor/scan configuration agreement without ROS dependencies."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

SRC = Path(__file__).resolve().parents[2]


class OdinConfigTest(unittest.TestCase):
    def test_range_and_rate_match_scan_consumer(self):
        root = ET.parse(SRC / 'sentry_sim/urdf/gazebo/lidar.xacro').getroot()
        values = {p.get('name'): float(p.get('value')) for p in
                  root.findall('{http://www.ros.org/wiki/xacro}property')}
        text = (SRC / 'sentry_perception/config/pointcloud_to_scan.yaml').read_text(encoding='utf-8')
        def scan(key):
            return float(re.search(r'^\s+' + key + r':\s*([-0-9.]+)', text, re.M)[1])
        self.assertEqual(values['lidar_range_min'], .15)
        self.assertEqual(values['lidar_range_max'], 25.)
        self.assertEqual(values['lidar_rate'], 10.)
        self.assertEqual(scan('range_min'), values['lidar_range_min'])
        self.assertEqual(scan('range_max'), values['lidar_range_max'])
        self.assertEqual(scan('scan_time'), 1. / values['lidar_rate'])
        sensors = root.findall('gazebo/sensor')
        self.assertEqual(len(sensors), 1)
        self.assertEqual(sensors[0].get('name'), 'odin1_lite')
        self.assertEqual(sensors[0].findtext('plugin/frame_name'), 'lidar_link')


if __name__ == '__main__':
    unittest.main()
