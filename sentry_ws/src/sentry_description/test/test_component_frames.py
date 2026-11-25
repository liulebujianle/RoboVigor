"""检查两台导航雷达的安装关系、零位和转台运动。"""
from pathlib import Path
import math
import xml.etree.ElementTree as ET

import numpy as np
import xacro

import importlib.util


def load_origin():
    path = Path(__file__).resolve().parents[1] / 'src/sentry_description/sentry_display_description.py'
    spec = importlib.util.spec_from_file_location('display_description', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.origin


origin = load_origin()

PACKAGE = Path(__file__).resolve().parents[1]


def test_navigation_camera_uses_the_saved_cad_lens_pose():
    robot = ET.fromstring(xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro')).toxml())
    joints = {joint.find('child').get('link'): joint for joint in robot.findall('joint')}
    assert 'navigation_camera_link' in joints
    assert 'navigation_camera_optical_frame' in joints
    body = joints['navigation_camera_link']
    optical = joints['navigation_camera_optical_frame']
    assert body.get('type') == optical.get('type') == 'fixed'
    assert body.find('parent').get('link') == 'gimbal_yaw_link'
    assert optical.find('parent').get('link') == 'navigation_camera_link'

    pose = origin(body.find('origin')) @ origin(optical.find('origin'))
    np.testing.assert_allclose(pose[:3, 3], [-.002619990, .215684087, .231], atol=1e-8)
    np.testing.assert_allclose(pose[:3, :3], [
        [.999926229, 0, -.012146455],
        [.012146455, 0, .999926229],
        [0, -1, 0],
    ], atol=1e-8)


def test_scan_frames_move_with_the_turntable():
    robot = ET.fromstring(xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro')).toxml())
    by_child = {j.find('child').get('link'): j for j in robot.findall('joint')}
    turntable = by_child['gimbal_yaw_link']
    assert turntable.get('type') == 'continuous'
    assert turntable.find('parent').get('link') == 'chassis_link'
    assert turntable.find('axis').get('xyz') == '0 0 1'
    pivot = origin(turntable.find('origin'))
    quarter_turn = origin(ET.Element('origin', rpy=f'0 0 {math.pi / 2}'))
    for name in ('mid360s_link', 'odin1_lite_mount_link'):
        mount = by_child[name]
        assert mount.get('type') == 'fixed'
        assert mount.find('parent').get('link') == 'gimbal_yaw_link'
        relative = origin(mount.find('origin'))
        zero = pivot @ relative
        moved = pivot @ quarter_turn @ relative
        x, y, z = zero[:3, 3]
        assert np.allclose(moved[:3, 3], [-y, x, z])
        assert not np.allclose(moved, zero)
        if name == 'odin1_lite_mount_link':
            np.testing.assert_allclose([x, y, z], [.1184985, .0008394, .1999000], atol=1e-6)
            np.testing.assert_allclose(zero[:3, 0], [.999926, .012147, 0], atol=1e-5)
        else:
            np.testing.assert_allclose([x, y, z], [-.1569718, .1035010, .2728618], atol=1e-6)
            np.testing.assert_allclose(zero[:3, 2], [-.74309, -.00903, .66913], atol=1e-4)


def test_odin_scan_starts_on_the_outer_face_in_front_of_tx():
    robot = ET.fromstring(xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro')).toxml())
    by_child = {j.find('child').get('link'): j for j in robot.findall('joint')}
    tx = by_child['odin1_lite_link']
    shell = 'odin1_lite_mount_link'
    assert tx.find('parent').get('link') == shell
    pose = origin(tx.find('origin'))
    visual = robot.find(f"link[@name='{shell}']/visual")
    np.testing.assert_allclose(origin(visual.find('origin')), np.eye(4))
    filename = visual.find('geometry/mesh').get('filename').split('sentry_description/')[1]
    dae = ET.parse(PACKAGE / filename)
    position = dae.find(".//{*}vertices/{*}input[@semantic='POSITION']").get('source')[1:]
    array = dae.find(f".//{{*}}source[@id='{position}']/{{*}}float_array")
    front = np.fromstring(array.text, sep=' ').reshape(-1, 3)[:, 0].max()
    np.testing.assert_allclose(front, .037, atol=1e-6)
    # 当前总装亚克力外表面距 TX 外窗 3.8 mm，取整到下一个毫米。
    np.testing.assert_allclose(pose[:3, 3], [front + .004, .015, 0], atol=1e-6)
    np.testing.assert_allclose(pose[:3, :3], np.eye(3))


def test_small_yaw_independent_of_navigation_lidars():
    robot = ET.fromstring(xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro')).toxml())
    joints = {j.find('child').get('link'): j for j in robot.findall('joint')}
    small = joints['small_yaw_link']
    assert small.get('name') == 'small_yaw_joint' and small.get('type') == 'continuous'
    assert small.find('parent').get('link') == 'gimbal_yaw_link'
    assert small.find('mimic') is None
    np.testing.assert_allclose(origin(small.find('origin')), np.eye(4))
    assert all(j.find('parent').get('link') != 'small_yaw_link' for j in joints.values())

    def z_rotation(angle):
        return origin(ET.Element('origin', rpy=f'0 0 {angle}'))

    def pose(link, angles):
        if link == 'base_link':
            return np.eye(4)
        joint = joints[link]
        parent = joint.find('parent').get('link')
        local = origin(joint.find('origin'))
        if joint.get('type') == 'continuous':
            np.testing.assert_allclose(np.fromstring(joint.find('axis').get('xyz'), sep=' '), [0, 0, 1])
            local = local @ z_rotation(angles.get(joint.get('name'), 0))
        return pose(parent, angles) @ local

    for large_angle in (0, .7, -1.2):
        large_only = {'gimbal_yaw_joint': large_angle}
        both = {**large_only, 'small_yaw_joint': -.45}
        expected = pose('gimbal_yaw_link', large_only) @ z_rotation(-.45)
        np.testing.assert_allclose(pose('small_yaw_link', both), expected, atol=1e-10)
        for lidar in ('mid360s_link', 'odin1_lite_link'):
            np.testing.assert_allclose(pose(lidar, both), pose(lidar, large_only), atol=1e-10)
