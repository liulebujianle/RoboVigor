"""核对当前总装的四轮安装和 Gazebo 接触几何。"""
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import xacro

PACKAGE = Path(__file__).resolve().parents[1]


def test_four_cad_axles_and_matching_cylinder_geometry():
    """四个 CAD 轮心的坐标及其指向车内的轮轴，单位 m。"""
    robot = ET.fromstring(xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro')).toxml())
    assert not any(e.get('name', '').startswith('roller_') for e in robot)
    assert len([j for j in robot.findall("joint[@type='continuous']")
                if j.get('name').startswith('wheel_')]) == 4
    corners = [(-1, 1), (1, 1), (1, -1), (-1, -1)]
    for i, (x_sign, y_sign) in enumerate(corners, start=1):
        link = robot.find(f"link[@name='wheel_{i}_link']")
        joint = robot.find(f"joint[@name='wheel_{i}_joint']")
        assert joint.find('parent').get('link') == 'chassis_link'
        assert joint.find('child').get('link') == f'wheel_{i}_link'
        axis = np.fromstring(joint.find('axis').get('xyz'), sep=' ')
        np.testing.assert_allclose(axis, np.array([-x_sign, -y_sign, 0]) / np.sqrt(2))
        center = np.fromstring(joint.find('origin').get('xyz'), sep=' ')
        np.testing.assert_allclose(center, [.16731710127*x_sign, .16731710127*y_sign, -.03618833])
        cylinder = link.find('collision/geometry/cylinder')
        assert float(cylinder.get('radius')) == .0761
        assert float(cylinder.get('length')) == .03979804608234
        origin = link.find('collision/origin')
        roll, pitch, yaw = np.fromstring(origin.get('rpy'), sep=' ')
        np.testing.assert_allclose([roll, pitch], [0, np.pi / 2])
        np.testing.assert_allclose([np.cos(yaw), np.sin(yaw), 0], axis)
        np.testing.assert_allclose(np.fromstring(origin.get('xyz'), sep=' '), -.00150040329349 * axis)


def test_cad_visuals_keep_simple_collisions_and_independent_lidar_housings():
    robot = ET.fromstring(xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro')).toxml())
    assert not robot.findall('.//collision/geometry/mesh')
    assert len(robot.findall('.//collision/geometry/cylinder')) == 4
    assert robot.find("link[@name='chassis_link']/collision/geometry/box") is not None
    assert robot.find("link[@name='mid360s_link']/visual/geometry/mesh").get('filename').endswith('/sentry_mid360s.dae')
    assert robot.find("link[@name='odin1_lite_mount_link']/visual/geometry/mesh") is not None
    assert robot.find("link[@name='lidar_link']/visual") is None
