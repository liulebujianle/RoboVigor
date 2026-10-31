"""Check lightweight cylindrical tires against the supplied native assembly."""
from pathlib import Path
import xml.etree.ElementTree as ET

import json

import numpy as np
import xacro

PACKAGE = Path(__file__).resolve().parents[1]


def test_four_cad_axles_and_matching_cylinder_geometry():
    """Keep X-drive axes and measured tire sizes without passive roller bodies."""
    robot = ET.fromstring(xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro')).toxml())
    assert not any(e.get('name', '').startswith('roller_') for e in robot)
    assert len(robot.findall("joint[@type='continuous']")) == 5
    measured = json.loads((PACKAGE / 'config/wheel_dimensions.json').read_text())['wheels']
    for i in range(1, 5):
        actual = measured[f'wheel_{i}_link']
        link = robot.find(f"link[@name='wheel_{i}_link']")
        joint = robot.find(f"joint[@name='wheel_{i}_joint']")
        axis = list(map(float, joint.find('axis').get('xyz').split()))
        assert np.allclose(axis, actual['axis'])
        assert np.allclose(list(map(float, joint.find('origin').get('xyz').split())),
                           actual['center_m'])
        for kind in ('visual', 'collision'):
            cylinder = link.find(f'{kind}/geometry/cylinder')
            assert cylinder is not None
            assert float(cylinder.get('radius')) == .0761
            assert float(cylinder.get('length')) == .03979804608234
            rpy = list(map(float, link.find(f'{kind}/origin').get('rpy').split()))
            direction = [np.cos(rpy[2]), np.sin(rpy[2]), 0.]
            assert np.allclose(direction, axis)
        y = float(joint.find('origin').get('xyz').split()[1])
        assert np.isclose(abs(y), .16731710127)


def test_body_visuals_are_lightweight_without_changing_physics():
    """The default whole robot must not load any triangle meshes."""
    robot = ET.fromstring(xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro')).toxml())
    assert not robot.findall('.//mesh')
    assert len(robot.findall('.//visual')) <= 15
    assert not robot.findall('.//collision/geometry/mesh')
    for name in ('lidar_link', 'lidar_aux_link', 'camera_link', 'gun_link'):
        assert robot.find(f"link[@name='{name}']/visual") is not None
