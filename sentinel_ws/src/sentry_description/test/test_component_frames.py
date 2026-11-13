"""Validate explicit mechanical component references and optical convention."""
from pathlib import Path
import math
import xml.etree.ElementTree as ET

import numpy as np
import xacro
import yaml

PACKAGE = Path(__file__).resolve().parents[1]
REFERENCES = {'lidar_link', 'lidar_aux_link', 'camera_link',
              'camera_optical_frame', 'gun_link', 'muzzle_link'}


def rotation(text):
    """Convert URDF fixed-axis RPY to a child-to-parent rotation."""
    roll, pitch, yaw = map(float, text.split())
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    return np.array([[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
                     [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
                     [-sp, cp * sr, cp * cr]])


def test_reference_frames_are_fixed_connected_and_nominal():
    """Keep CAD aliases nominal at zero, with gun on the added physical pitch axis."""
    data = yaml.safe_load((PACKAGE / 'config/frames.yaml').read_text())
    assert 'CAD' in data['status'] and 'calibrate' in data['status']
    assert set(data['frames']) == REFERENCES
    model = ET.fromstring(xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro')).toxml())
    links = {link.get('name') for link in model.findall('link')}
    for name, frame in data['frames'].items():
        joint = model.find(f"joint[@name='{name}_fixed']")
        assert joint is not None and joint.get('type') == 'fixed'
        assert joint.find('child').get('link') == name
        if name == 'gun_link':
            assert joint.find('parent').get('link') == 'gimbal_pitch_link' in links
            pitch = model.find("joint[@name='gimbal_pitch_joint']")
            assert pitch.get('type') == 'revolute'
            assert pitch.find('parent').get('link') == frame['parent']
            assert np.allclose(list(map(float, pitch.find('origin').get('xyz').split())),
                               list(map(float, frame['xyz'].split())))
            assert np.allclose(rotation(pitch.find('origin').get('rpy')), rotation(frame['rpy']))
            assert np.allclose(list(map(float, joint.find('origin').get('xyz').split())), 0)
            assert np.allclose(rotation(joint.find('origin').get('rpy')), np.eye(3))
        else:
            assert joint.find('parent').get('link') == frame['parent'] in links
            assert np.allclose(list(map(float, joint.find('origin').get('xyz').split())),
                               list(map(float, frame['xyz'].split())))
            assert np.allclose(rotation(joint.find('origin').get('rpy')), rotation(frame['rpy']))
        assert np.isfinite(list(map(float, frame['xyz'].split()))).all()
        assert np.linalg.norm(list(map(float, frame['xyz'].split()))) < .5
        matrix = rotation(frame['rpy'])
        assert np.allclose(matrix.T @ matrix, np.eye(3), atol=1e-10)
        assert np.linalg.det(matrix) > .999999
        assert model.find(f"link[@name='{name}']/inertial") is None
    assert 'wheels_link' not in links


def test_camera_optical_axes_and_muzzle_direction():
    """Use conventional optical axes and a positive forward mechanical exit."""
    frames = yaml.safe_load((PACKAGE / 'config/frames.yaml').read_text())['frames']
    optical = rotation(frames['camera_optical_frame']['rpy'])
    assert np.allclose(optical[:, 0], [0, -1, 0], atol=1e-10)
    assert np.allclose(optical[:, 1], [0, 0, -1], atol=1e-10)
    assert np.allclose(optical[:, 2], [1, 0, 0], atol=1e-10)
    assert frames['muzzle_link']['parent'] == 'gun_link'
    x, y, z = map(float, frames['muzzle_link']['xyz'].split())
    assert 0 < x < .3 and y == z == 0
    assert np.dot(rotation(frames['gun_link']['rpy'])[:, 0],
                  rotation(frames['camera_link']['rpy'])[:, 0]) > .99


def test_fps_camera_tracks_pitch_and_keeps_optical_forward_on_the_barrel():
    """Exercise the expanded moving tree rather than a target-angle camera shortcut."""
    model = ET.fromstring(xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro')).toxml())
    joints = {j.find('child').get('link'): j for j in model.findall('joint')}

    def pose(link, pitch_angle):
        if link == 'gimbal_yaw_link':
            return np.eye(4)
        joint = joints[link]
        origin = joint.find('origin')
        transform = np.eye(4)
        transform[:3, :3] = rotation(origin.get('rpy', '0 0 0'))
        transform[:3, 3] = list(map(float, origin.get('xyz', '0 0 0').split()))
        if joint.get('name') == 'gimbal_pitch_joint':
            motion = np.eye(4)
            motion[:3, :3] = rotation(f'0 {pitch_angle} 0')
            transform = transform @ motion
        return pose(joint.find('parent').get('link'), pitch_angle) @ transform

    for angle in (-.8, 0., .8):
        gun = pose('gun_link', angle)
        camera = pose('fps_camera_link', angle)
        optical = pose('fps_camera_optical_frame', angle)
        muzzle = pose('muzzle_link', angle)
        assert np.allclose(camera[:3, 0], gun[:3, 0])
        assert np.allclose(optical[:3, 2], gun[:3, 0])
        assert np.allclose(optical[:3, 0], -camera[:3, 1])
        assert np.allclose(optical[:3, 1], -camera[:3, 2])
        assert np.allclose(camera[:3, 3] - muzzle[:3, 3], .02 * gun[:3, 0])
