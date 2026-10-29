"""Check the display model's mesh, units and initial ground clearance."""

import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

import numpy as np
import xacro


def test_gimbal_is_a_separate_articulated_visual():
    """The turret can counter-rotate; the old cylinder cannot be spawned."""
    package = Path(__file__).resolve().parents[1]
    model = ET.fromstring(xacro.process_file(str(package / 'urdf/sentry.urdf.xacro')).toxml())
    joint = model.find("joint[@name='gimbal_yaw_joint']")
    assert joint is not None
    assert joint.get('type') == 'continuous'
    assert len(model.findall('.//visual/geometry/mesh')) == 118
    assert model.find('.//visual/geometry/cylinder') is None
    assert not (package / 'urdf/sentry_simple.urdf').exists()


def test_cad_mesh_and_ground_clearance():
    """Catch missing resources, corrupt STL, unit errors or a buried robot."""
    package = Path(__file__).resolve().parents[1]
    model = ET.fromstring(xacro.process_file(str(package / 'urdf/sentry.urdf.xacro')).toxml())
    metadata = json.loads((package / 'urdf/sentry_cad.json').read_text())
    origins = {'base_link': np.zeros(3)}
    joints = {joint.find('child').get('link'): joint for joint in model.findall('joint')}

    def link_origin(name):
        if name not in origins:
            joint = joints[name]
            origin = joint.find('origin')
            xyz = [0., 0., 0.] if origin is None else [
                float(v) for v in origin.get('xyz', '0 0 0').split()]
            origins[name] = link_origin(joint.find('parent').get('link')) + xyz
        return origins[name]

    complete = []
    for link in model.findall('link'):
        for geometry in link.findall('visual/geometry/mesh'):
            uri = geometry.get('filename')
            assert uri.startswith('package://sentry_description/')
            mesh = package / uri.removeprefix('package://sentry_description/')
            data = mesh.read_bytes()
            count = struct.unpack_from('<I', data, 80)[0]
            assert len(data) == 84 + count * 50
            records = np.frombuffer(data, offset=84, dtype=[
                ('normal', '<f4', 3), ('vertices', '<f4', (3, 3)), ('attribute', '<u2'),
            ])
            vertices = records['vertices'].reshape(-1, 3)
            assert np.isfinite(vertices).all()
            complete.append(vertices + link_origin(link.get('name')))
    vertices = np.concatenate(complete)
    assert np.allclose(vertices.min(0), metadata['bounds_m'][0], atol=1e-6)
    assert np.allclose(vertices.max(0), metadata['bounds_m'][1], atol=1e-6)
    dimensions = np.ptp(vertices, axis=0)
    assert np.all(dimensions > 0.4) and np.all(dimensions < 0.7), dimensions
    bottom = float(vertices[:, 2].min())
    # The selected supply-area support surface is 3 mm above the field datum.
    clearance = metadata['spawn_z'] + bottom - 0.003
    assert 0.001 <= clearance <= 0.005, clearance
    collision = model.find('.//collision/origin')
    collision_z = float(collision.get('xyz').split()[2])
    height = float(model.find('.//collision/geometry/box').get('size').split()[2])
    assert collision_z - height / 2 > bottom + 0.03
    assert metadata['assembly']['no_cached_mesh'] == 0
    assert metadata['assembly']['from_part_files'] == 0


def test_physical_wheel_and_roller_tree():
    """The car must stand on physical wheels, with positive rigid-body inertia."""
    package = Path(__file__).resolve().parents[1]
    model = ET.fromstring(xacro.process_file(str(package / 'urdf/sentry.urdf.xacro')).toxml())
    wheels = [j for j in model.findall('joint') if j.get('name').startswith('wheel_')]
    rollers = [j for j in model.findall('joint') if j.get('name').startswith('roller_')]
    assert len(wheels) == 4 and len(rollers) == 112
    assert len(model.findall('.//collision/geometry/sphere')) == 112
    plugins = [p.get('filename') for p in model.findall('.//plugin')]
    assert 'libgazebo_ros_planar_move.so' not in plugins
    assert not plugins, 'Description must not depend on Gazebo plugins'
    for link in model.findall('link'):
        if link.get('name') in {
                'base_link', 'wheels_link', 'lidar_link', 'lidar_aux_link',
                'camera_link', 'camera_optical_frame', 'gun_link', 'muzzle_link'}:
            continue
        inertial = link.find('inertial')
        assert float(inertial.find('mass').get('value')) > 0
        i = inertial.find('inertia')
        tensor = np.array([[float(i.get('ixx')), float(i.get('ixy')), float(i.get('ixz'))],
                           [float(i.get('ixy')), float(i.get('iyy')), float(i.get('iyz'))],
                           [float(i.get('ixz')), float(i.get('iyz')), float(i.get('izz'))]])
        values = np.linalg.eigvalsh(tensor)
        assert np.all(values > 0)
        assert values[-1] <= values[0] + values[1] + 1e-10
