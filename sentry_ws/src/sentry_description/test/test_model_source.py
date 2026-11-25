"""检查默认导航 URDF 的连通性和兼容坐标系。"""
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import xacro

PACKAGE = Path(__file__).resolve().parents[1]


def test_single_parent_tree_reaches_base_link():
    model = xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro'))
    robot = ET.fromstring(model.toxml())
    names = [link.get('name') for link in robot.findall('link')]
    assert len(names) == len(set(names))
    parents = {}
    joints = robot.findall('joint')
    assert len({joint.get('name') for joint in joints}) == len(joints)
    for joint in joints:
        child = joint.find('child').get('link')
        parent = joint.find('parent').get('link')
        assert child in names and parent in names
        assert child not in parents, child
        parents[child] = parent
    assert set(names) - set(parents) == {'base_link'}
    for name in names:
        seen = set()
        while name != 'base_link':
            assert name not in seen, f'TF cycle at {name}'
            seen.add(name)
            name = parents[name]


def test_both_lidars_follow_yaw_and_legacy_frame_matches_odin():
    model = xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro'))
    robot = ET.fromstring(model.toxml())
    mounts = {joint.find('child').get('link'): joint for joint in robot.findall('joint')}
    for frame in ('odin1_lite_mount_link', 'mid360s_link'):
        joint = mounts[frame]
        assert joint.get('type') == 'fixed'
        assert joint.find('parent').get('link') == 'gimbal_yaw_link'
    assert mounts['odin1_lite_link'].find('parent').get('link') == 'odin1_lite_mount_link'
    alias = mounts['lidar_link']
    assert alias.get('type') == 'fixed'
    assert alias.find('parent').get('link') == 'odin1_lite_link'
    origin = alias.find('origin')
    if origin is not None:
        for key in ('xyz', 'rpy'):
            np.testing.assert_allclose(np.fromstring(origin.get(key, '0 0 0'), sep=' '), [0, 0, 0])
