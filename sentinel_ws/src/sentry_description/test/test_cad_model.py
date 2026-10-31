"""Check the primitive default model, ground clearance and rigid-body inertia."""
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import xacro

PACKAGE = Path(__file__).resolve().parents[1]


def model():
    """Expand the platform actually used by RViz and Gazebo."""
    return ET.fromstring(xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro')).toxml())


def test_gimbal_is_a_separate_articulated_visual():
    """Keep the turret and reference hardware independently visible without CAD meshes."""
    robot = model()
    assert robot.find("joint[@name='gimbal_yaw_joint']").get('type') == 'continuous'
    assert len(robot.find("link[@name='gimbal_yaw_link']").findall('visual')) == 3
    assert not robot.findall('.//mesh')
    assert len(robot.findall('.//visual')) == 13
    assert not (PACKAGE / 'urdf/sentry_simple.urdf').exists()


def test_initial_ground_clearance():
    """The wheel tires must support the robot before the chassis box hits the field."""
    robot = model()
    wheel = robot.find("joint[@name='wheel_1_joint']/origin")
    bottom = float(wheel.get('xyz').split()[2]) - .0761
    clearance = .118 + bottom - .003
    assert .001 <= clearance <= .005
    collision = robot.find("link[@name='chassis_link']/collision")
    collision_z = float(collision.find('origin').get('xyz').split()[2])
    height = float(collision.find('geometry/box').get('size').split()[2])
    assert collision_z - height / 2 > bottom + .03


def test_physical_wheel_tree_and_inertias():
    """Only four driven wheel joints and one gimbal remain; no passive rollers."""
    robot = model()
    assert len(robot.findall("joint[@type='continuous']")) == 5
    assert not any(e.get('name', '').startswith('roller_') for e in robot)
    assert len(robot.findall('.//collision/geometry/cylinder')) == 4
    assert not robot.findall('gazebo')
    for link in robot.findall('link'):
        inertial = link.find('inertial')
        if inertial is None:
            continue
        assert float(inertial.find('mass').get('value')) > 0
        i = inertial.find('inertia')
        tensor = np.array([[float(i.get('ixx')), float(i.get('ixy')), float(i.get('ixz'))],
                           [float(i.get('ixy')), float(i.get('iyy')), float(i.get('iyz'))],
                           [float(i.get('ixz')), float(i.get('iyz')), float(i.get('izz'))]])
        values = np.linalg.eigvalsh(tensor)
        assert np.all(values > 0)
        assert values[-1] <= values[0] + values[1] + 1e-10
